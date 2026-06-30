from motor.motor_asyncio import AsyncIOMotorClient
from core.config import config


class Database:
    _client: AsyncIOMotorClient | None = None
    _db = None

    @classmethod
    async def connect(cls):
        if cls._client is None:
            cls._client = AsyncIOMotorClient(config.MONGODB_URL)
            cls._db = cls._client[config.DATABASE_NAME]
            await cls._ensure_indexes()

    @classmethod
    async def disconnect(cls):
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None

    @classmethod
    def db(cls):
        return cls._db

    @classmethod
    async def _ensure_indexes(cls):
        await cls._db.cache.create_index("key", unique=True)
        await cls._db.cache.create_index("expire_at", expireAfterSeconds=0)
        await cls._db.jobs.create_index("job_id", unique=True)
        await cls._db.jobs.create_index("status")
        await cls._db.users.create_index("telegram_id", unique=True)
        await cls._db.channels.create_index("name", unique=True)
        await cls._db.logs.create_index("created_at")
        await cls._db.anime_cache.create_index("slug", unique=True)
