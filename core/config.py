import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    BOT_START_IMAGE: str = os.getenv("BOT_START_IMAGE", "")
    WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")
    WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "")
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "autoanimebot")
    API_BASE: str = os.getenv("API_BASE", "https://h5-api.aoneroom.com/wefeed-h5api-bff")
    API_PLAY_BASE: str = os.getenv("API_PLAY_BASE", "https://h5.aoneroom.com/wefeed-h5-bff/web/subject/play")
    API_TOKEN: str = os.getenv("API_TOKEN", "afaea552101228848de8f8c7f48a1b7d7a6a042a6094274eaa9d30cb64bf91a7")
    DOWNLOAD_DELETE_TIMER: int = int(os.getenv("DOWNLOAD_DELETE_TIMER", "840"))
    MAIN_CHANNEL: str = os.getenv("MAIN_CHANNEL", "")
    ADMINS: list[int] = [int(x.strip()) for x in os.getenv("ADMINS", "").split(",") if x.strip()]
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    MAX_RETRY: int = int(os.getenv("MAX_RETRY", "3"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    MAX_CONCURRENT_UPLOADS: int = int(os.getenv("MAX_CONCURRENT_UPLOADS", "3"))
    HTTP_POOL_SIZE: int = int(os.getenv("HTTP_POOL_SIZE", "100"))
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "300"))
    MONGO_CACHE_TTL: int = int(os.getenv("MONGO_CACHE_TTL", "86400"))
    WEBHOOK_HOST: str = os.getenv("WEBHOOK_HOST", "0.0.0.0")
    WEBHOOK_PORT: int = int(os.getenv("PORT", os.getenv("WEBHOOK_PORT", "8443")))
    TEMP_DIR: str = os.getenv("TEMP_DIR", "temp")


config = Config()
