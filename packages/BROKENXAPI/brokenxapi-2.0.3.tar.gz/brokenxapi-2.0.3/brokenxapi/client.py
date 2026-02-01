import aiohttp

class BrokenXAPI:
    def __init__(self, api_key: str, base_url: str = "https://mrbroken-brokenxbots.hf.space"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._session = None

    async def __aenter__(self):
        self._session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.api_key}"
            }
        )
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._session:
            await self._session.close()

    async def _get(self, path: str, params: dict | None = None):
        url = f"{self.base_url}{path}"
        async with self._session.get(url, params=params) as r:
            r.raise_for_status()
            return await r.json()

    # -------- PUBLIC METHODS --------

    async def search(self, query: str, video: bool = False):
        return await self._get(
            "/search",
            {
                "q": query,
                "video": video
            }
        )

    async def download(self, video_id: str, media: str = "audio"):
        if media not in ("audio", "video"):
            raise ValueError("media must be 'audio' or 'video'")

        return await self._get(
            f"/download/{media}",
            {"video_id": video_id}
        )

