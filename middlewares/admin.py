from core.config import config
from core.database import Database


async def is_admin(telegram_id: int) -> bool:
    if telegram_id in config.ADMINS:
        return True
    user = await Database.db.users.find_one({"telegram_id": telegram_id})
    return user is not None and user.get("is_admin", False)


async def ensure_admin(telegram_id: int) -> bool:
    return await is_admin(telegram_id)


async def get_admin_ids() -> list[int]:
    admin_users = await Database.db.users.find({"is_admin": True}).to_list(None)
    return list(set(config.ADMINS + [u["telegram_id"] for u in admin_users]))
