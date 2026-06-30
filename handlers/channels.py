from core.bot import Bot
from core.database import Database
from core.logger import logger
from middlewares.admin import ensure_admin
from ui.templates import error_card, channel_list


async def handle_channel_command(bot: Bot, chat_id: int, message_id: int, text: str, parts: list[str]):
    if not await ensure_admin(chat_id):
        return

    command = parts[0]

    if command == "/listsub":
        channels = await Database.db.channels.find().to_list(None)
        if not channels:
            await bot.send_message(chat_id, "No channels configured.")
            return
        await bot.send_message(chat_id, channel_list(channels))

    elif command == "/setmain":
        if len(parts) < 2:
            await bot.send_message(chat_id, "Usage: /setmain <channel_id>")
            return
        channel_id = parts[1]
        from core.config import config
        import os
        os.environ["MAIN_CHANNEL"] = channel_id
        await log_action(chat_id, "setmain", {"channel_id": channel_id})
        await bot.send_message(chat_id, f"Main channel set to {channel_id}")

    elif command == "/addsub":
        if len(parts) < 3:
            await bot.send_message(chat_id, "Usage: /addsub <name> <channel_id>")
            return
        name = parts[1]
        channel_id = parts[2]
        await Database.db.channels.update_one(
            {"name": name},
            {"$set": {"name": name, "channel_id": channel_id}},
            upsert=True,
        )
        await bot.send_message(chat_id, f"Added channel: {name} ({channel_id})")

    elif command == "/removesub":
        if len(parts) < 2:
            await bot.send_message(chat_id, "Usage: /removesub <name>")
            return
        name = parts[1]
        result = await Database.db.channels.delete_one({"name": name})
        if result.deleted_count:
            await bot.send_message(chat_id, f"Removed channel: {name}")
        else:
            await bot.send_message(chat_id, error_card(f"Channel not found: {name}"))


async def log_action(chat_id: int, action: str, details: dict | None = None):
    from middlewares.logging import log_action as la
    await la(chat_id, action, details)
