from datetime import datetime, timezone

from core.database import Database
from core.logger import logger


async def log_action(telegram_id: int, action: str, details: dict | None = None):
    record = {
        "telegram_id": telegram_id,
        "action": action,
        "details": details or {},
        "created_at": datetime.now(timezone.utc),
    }
    try:
        await Database.db.logs.insert_one(record)
    except Exception as e:
        logger.warning("Failed to log action: %s", e)


async def get_recent_logs(limit: int = 20) -> list[dict]:
    cursor = Database.db.logs.find().sort("created_at", -1).limit(limit)
    return await cursor.to_list(limit)
