
import logging
from uuid import uuid4

import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException

from src.api import dependencies
from src.reqresp import search
from src.reqresp import national_bank


ACTION_SEARCH_TICKET_IN = "action.search-tickets.in"


router = APIRouter(tags=["search"])
log = logging.getLogger("uvicorn.error")


@router.post("/search", response_model=search.SearchResponse)
async def search_tickets(
    client: redis.Redis = Depends(dependencies.get_redis_client),
):
    """Enqueue a search job for asynchronous processing."""
    search_id = str(uuid4())
    request = search.RedisSearchRequest(search_id=search_id)

    response: redis.ResponseT = await client.xadd(
        name=ACTION_SEARCH_TICKET_IN,
        fields=request.model_dump(),
    )
    log.info("Published search request %s to stream %s", search_id, ACTION_SEARCH_TICKET_IN)

    if response is None:
        log.error("Failed to publish search request %s", search_id)
        return search.SearchResponse(
            search_id=search_id,
            status="error",
            message="Failed to process search request.",
        )

    return search.SearchResponse(
        search_id=search_id,
        status="pending",
        message="Search request received and is being processed.",
    )


@router.get(
    "/results/{search_id}/{currency}",
    response_model=search.SearchResponse,
)
async def get_search_results(
    search_id: str,
    currency: str,
    client: redis.Redis = Depends(dependencies.get_redis_client),
):
    """Return cached search results for a given search ID."""
    redis_key = f"search_results:{search_id}"
    cached = await client.json().get(redis_key, "$")

    if not cached:
        raise HTTPException(
            status_code=404,
            detail="Search results not found or still processing.",
        )

    try:
        payload = cached[0] if isinstance(cached, list) else cached
        result = search.SearchResponse.model_validate(payload)

    except Exception as exc:  # pragma: no cover - defensive guardrail
        log.error("Failed to deserialize cached results for %s: %s", search_id, exc)
        raise HTTPException(status_code=500, detail="Corrupted cached search results") from exc
    
    if result.status != search.SearchStatus.COMPLETED:
        return result
    
    cached_currencies = await client.get("exchange_rates")
    national_bank_response = national_bank.NationalBankResponse.model_validate_json(cached_currencies)
    currency_map = {}
    for curr in national_bank_response.rate.currencies:
        currency_map[curr.title] = curr.description

    if currency.upper() not in currency_map and currency.upper() != "KZT":
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported target currency: {currency}",
        )

    for item in result.items or []:
        rate_for_currency = currency_map.get(item.pricing.currency.upper())
        if not rate_for_currency and item.pricing.currency.upper() != "KZT":
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported currency conversion for {item.pricing.currency} to {currency}",
            )
        if item.pricing.currency.upper() == "KZT":
            rate_for_currency = 1.0

        amount_in_kzt: float = item.pricing.total * rate_for_currency
        converted_amount: float = amount_in_kzt
    
        if currency.upper() != "KZT":
            converted_amount: float = amount_in_kzt / currency_map[currency.upper()]
        
        item.price = search.Price(
            amount=round(converted_amount, 2),
            currency=currency.upper()
        )


    log.info("Returning results for search %s (requested currency %s)", search_id, currency)
    return result