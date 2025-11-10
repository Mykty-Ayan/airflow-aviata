import aiohttp


from src.reqresp import search

class AlphaClient:
    def __init__(self, config):
        self.config = config
        self._session = None

    async def _get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                base_url=self.config.get("PROVIDER_A_API_BASE_URL", "http://provider-alpha:8080"),
                timeout=aiohttp.ClientTimeout(self.config.get("HTTP_TIMEOUT", 100))
                )
        return self._session

    async def search(self) -> search.AlphaSearchResponse:
        session = await self._get_session()
        async with session.post("/search") as response:
            data = await response.json()  # This is the raw list
            return search.AlphaSearchResponse(root=data)

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
