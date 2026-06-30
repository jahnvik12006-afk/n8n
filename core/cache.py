import asyncio
from cachetools import TTLCache
from core.config import config
from core.database import Database


class Cache:
    _memory: TTLCache | None = None
    _lock = asyncio.Lock()

    @classmethod
    def _get_memory(cls) -> TTLCache:
        if cls._memory is None:
            cls._memory = TTLCache(maxsize=1000, ttl=config.CACHE_TTL_SECONDS)
        return cls._memory

    @classmethod
    async def get(cls, key: str) -> str | None:
        mem = cls._get_memory()
        if key in mem:
            return mem[key]
        doc = await Database.db.cache.find_one({"key": key})
        if doc:
            mem[key] = doc["value"]
            return doc["value"]
        return None

    @classmethod
    async def set(cls, key: str, value: str, ttl: int | None = None):
        mem = cls._get_memory()
        mem[key] = value
        expire_ttl = ttl or config.MONGO_CACHE_TTL
        await Database.db.cache.update_one(
            {"key": key},
            {"$set": {"value": value, "expire_at": __import__("datetime").datetime.utcnow()}},
            upsert=True,
        )

    @classmethod
    async def delete(cls, key: str):
        mem = cls._get_memory()
        mem.pop(key, None)
        await Database.db.cache.delete_one({"key": key})

    @classmethod
    async def clear_all(cls):
        cls._get_memory().clear()
        await Database.db.cache.delete_many({})

    @classmethod
    async def stats(cls) -> dict:
        mem = cls._get_memory()
        mongo_count = await Database.db.cache.count_documents({})
        return {"memory_size": len(mem), "memory_maxsize": mem.maxsize, "mongo_count": mongo_count}
