import asyncio
import logging
from typing import Protocol, runtime_checkable

import redis.asyncio as redis
from redis.exceptions import ResponseError

from src.client.alpha.client import AlphaClient
from src.client.betta.client import BettaClient
from src.reqresp import search as search_reqresp


log = logging.getLogger("uvicorn.error")


ACTION_SEARCH_TICKET_IN = "action.search-tickets.in"
CONSUMER_GROUP = "search_group"
CONSUMER_NAME = "search_consumer"


@runtime_checkable
class ConsumerProtocol(Protocol):
    async def start(self) -> None:
        ...

    def stop(self) -> None:
        ...


class SearchRequestConsumer:
    """Redis stream consumer that fetches search tasks and stores provider results."""

    def __init__(
        self,
        redis_client: redis.Redis,
        alpha_client: AlphaClient,
        betta_client: BettaClient,
        *,
        stream: str = ACTION_SEARCH_TICKET_IN,
        group: str = CONSUMER_GROUP,
        consumer_name: str = CONSUMER_NAME,
        poll_timeout_ms: int = 1000,
        idle_sleep: float = 0.1,
    ) -> None:
        self.redis_client = redis_client
        self.alpha_client = alpha_client
        self.betta_client = betta_client
        self.stream = stream
        self.group = group
        self.consumer_name = consumer_name
        self.poll_timeout_ms = poll_timeout_ms
        self.idle_sleep = idle_sleep
        self._running = False

    async def start(self) -> None:
        log.info("🚀 Starting search request consumer (%s)", self.consumer_name)
        await self._ensure_stream_group()
        self._running = True

        try:
            while self._running:
                await self._consume_batch()
        finally:
            log.info("✅ Search request consumer stopped")

    def stop(self) -> None:
        log.info("🛑 Stop requested for search request consumer")
        self._running = False

    async def _ensure_stream_group(self) -> None:
        try:
            await self.redis_client.xgroup_create(
                name=self.stream,
                groupname=self.group,
                id="0-0",
                mkstream=True,
            )
            log.info(
                "Created consumer group '%s' for stream '%s'",
                self.group,
                self.stream,
            )
        except ResponseError as exc:
            if "BUSYGROUP" in str(exc):
                log.debug("Consumer group already exists")
            else:
                raise

    async def _consume_batch(self) -> None:
        try:
            response: redis.ResponseT = await self.redis_client.xreadgroup(
                groupname=self.group,
                consumername=self.consumer_name,
                streams={self.stream: ">"},
                count=1,
                block=self.poll_timeout_ms,
            )

            if not response:
                await asyncio.sleep(self.idle_sleep)
                return

            for _, messages in response:
                for message_id, message_data in messages:
                    await self._handle_message(message_id, message_data)

        except Exception as exc:  # pragma: no cover - defensive guardrail
            log.error("Error while consuming search requests: %s", exc, exc_info=True)
            await asyncio.sleep(1.0)

    async def _handle_message(self, message_id: str, message_data: dict) -> None:
        request = search_reqresp.RedisSearchRequest.model_validate(message_data)
        log.info("Processing search request with ID %s", request.search_id)

        try:
            result = search_reqresp.SearchResponse(
                search_id=request.search_id,
                status=search_reqresp.SearchStatus.PENDING,
                items=[],
            )
            await self.redis_client.json().set(
                f"search_results:{request.search_id}",
                 "$",
                result.model_dump(mode="json"),
            )
            log.info("Requesting search from provider alpha for ID %s", request.search_id)
            alpha_response = await self.alpha_client.search()
            for item in alpha_response.root:
                result.items.append(item)
            log.info(
                "Stored %s search results for ID %s",
                len(alpha_response.root),
                request.search_id,
            )
            log.info("Requesting search from provider betta for ID %s", request.search_id)
            betta_response = await self.betta_client.search()
            for item in betta_response.root:
                result.items.append(item)
            log.info(
                "Stored %s search results from Betta for ID %s",
                len(betta_response.root),
                request.search_id,
            )

            result.status = search_reqresp.SearchStatus.COMPLETED
            await self.redis_client.json().set(
                f"search_results:{request.search_id}",
                "$",
                result.model_dump(mode="json"),
            )
            log.info("Updated search results status to COMPLETED for ID %s", request.search_id)
            await self.redis_client.xack(self.stream, self.group, message_id)
            log.info("Acknowledged message %s", message_id)
        except Exception as exc:
            log.error(
                "Failed to process search request %s: %s",
                request.search_id,
                exc,
                exc_info=True,
            )


async def search_requests_consumer(
    redis_client: redis.Redis,
    alpha_client: AlphaClient,
    betta_client: BettaClient,
    *,
    poll_timeout_ms: int = 1000,
) -> None:
    """Entrypoint that satisfies ConsumerProtocol for background execution."""
    consumer = SearchRequestConsumer(
        redis_client=redis_client,
        alpha_client=alpha_client,
        betta_client=betta_client,
        poll_timeout_ms=poll_timeout_ms,
    )
    await consumer.start()

