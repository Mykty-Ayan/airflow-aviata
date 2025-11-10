import aiohttp

from src.reqresp import search

class BettaClient:
    def __init__(self, config):
        self.config = config
        self._session = None

    async def _get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                base_url=self.config.get("PROVIDER_B_API_BASE_URL", "http://provider-betta:8081"),
                timeout=aiohttp.ClientTimeout(self.config.get("HTTP_TIMEOUT", 100))
                )
        return self._session

    async def search(self) -> search.BettaSearchResponse:
        session = await self._get_session()
        async with session.post("/search") as response:
            data = await response.text()  # This is the raw list
            return search.BettaSearchResponse.model_validate_json(data)
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()