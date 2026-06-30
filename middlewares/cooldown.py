from datetime import datetime, timedelta, timezone

from core.database import Database


async def check_cooldown(telegram_id: int, cooldown_seconds: int = 2) -> bool:
    user = await Database.db.users.find_one({"telegram_id": telegram_id})
    if user and user.get("cooldown_until"):
        cooldown = user["cooldown_until"]
        if isinstance(cooldown, datetime) and cooldown > datetime.now(timezone.utc):
            return False
    return True


async def set_cooldown(telegram_id: int, cooldown_seconds: int = 2):
    until = datetime.now(timezone.utc) + timedelta(seconds=cooldown_seconds)
    await Database.db.users.update_one(
        {"telegram_id": telegram_id},
        {"$set": {"cooldown_until": until}},
        upsert=True,
    )
