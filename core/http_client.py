import httpx
from core.config import config


class HttpClient:
    _instance: httpx.AsyncClient | None = None

    @classmethod
    def get(cls) -> httpx.AsyncClient:
        if cls._instance is None or cls._instance.is_closed:
            cls._instance = httpx.AsyncClient(
                limits=httpx.Limits(
                    max_connections=config.HTTP_POOL_SIZE,
                    max_keepalive_connections=config.HTTP_POOL_SIZE,
                ),
                timeout=httpx.Timeout(config.REQUEST_TIMEOUT),
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "en-US,en;q=0.9",
                },
            )
        return cls._instance

    @classmethod
    async def close(cls):
        if cls._instance and not cls._instance.is_closed:
            await cls._instance.aclose()
            cls._instance = None
