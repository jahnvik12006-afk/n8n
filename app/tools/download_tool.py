"""Download tool — fetch video formats via highreach.ai API."""
import httpx
from app.tools.base import Tool

_API = "https://highreach.ai/api/tools/twitter-gif-download"


class FetchDownloadFormats(Tool):
    def __init__(self):
        super().__init__(
            name="FetchDownloadFormats",
            description="Get download formats for a YouTube/Twitter URL",
            permission="READ",
        )

    async def run(self, url: str, **kwargs) -> dict:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(_API, json={"tweet_url": url})
            r.raise_for_status()
            return r.json()
