from core.bot import Bot
from core.database import Database
from core.logger import logger
from middlewares.admin import ensure_admin
from middlewares.logging import log_action, get_recent_logs
from ui.templates import admin_panel, error_card
from ui.cards import build_stats_card
from ui.theme import box_top, box_bot, kv_line, tag_code, tag_bold
from core.cache import Cache


async def handle_admin_command(bot: Bot, chat_id: int, message_id: int, text: str, parts: list[str]):
    if not await ensure_admin(chat_id):
        return

    command = parts[0]

    if command == "/admin":
        await bot.send_message(chat_id, admin_panel())

    elif command == "/stats":
        total_jobs = await Database.db.jobs.count_documents({})
        completed = await Database.db.jobs.count_documents({"status": "Completed"})
        failed = await Database.db.jobs.count_documents({"status": "Failed"})
        pending = await Database.db.jobs.count_documents({"status": "Pending"})
        running = await Database.db.jobs.count_documents({"status": {"$in": ["Downloading", "Uploading"]}})
        channels = await Database.db.channels.count_documents({})
        cache_st = await Cache.stats()
        stats = {
            "total_jobs": total_jobs,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "running": running,
            "channels": channels,
            "cache_memory": cache_st.get("memory_size", 0),
            "cache_db": cache_st.get("mongo_count", 0),
        }
        await bot.send_message(chat_id, build_stats_card(stats))
        await log_action(chat_id, "stats")

    elif command == "/logs":
        logs = await get_recent_logs(10)
        lines = [box_top(36), tag_bold("Recent Logs"), ""]
        for log in logs:
            action = log.get("action", "?")
            ts = str(log.get("created_at", ""))[:19]
            lines.append(kv_line(ts, action))
        lines.append(box_bot(36))
        await bot.send_message(chat_id, "\n".join(lines))

    elif command == "/reload":
        from core.config import config
        logger.info("Config reloaded")
        await bot.send_message(chat_id, "Config reloaded.")

    elif command == "/cache":
        sub = parts[1] if len(parts) > 1 else "stats"
        if sub == "stats":
            st = await Cache.stats()
            await bot.send_message(chat_id, build_stats_card({
                "cache_memory": st.get("memory_size", 0),
                "cache_db": st.get("mongo_count", 0),
            }))
        elif sub == "clear":
            await Cache.clear_all()
            await bot.send_message(chat_id, "Cache cleared.")

    elif command == "/broadcast":
        if len(parts) < 2:
            await bot.send_message(chat_id, "Usage: /broadcast <message>")
            return
        msg = " ".join(parts[1:])
        channels = await Database.db.channels.find().to_list(None)
        sent = 0
        for ch in channels:
            try:
                await bot.send_message(ch["channel_id"], msg)
                sent += 1
            except Exception as e:
                logger.warning("Broadcast to %s failed: %s", ch["channel_id"], e)
        await bot.send_message(chat_id, f"Broadcast sent to {sent} channels.")

    elif command == "/cancel":
        if len(parts) < 2:
            await bot.send_message(chat_id, "Usage: /cancel <job_id>")
            return
        job_id = parts[1]
        await Database.db.jobs.update_one({"job_id": job_id}, {"$set": {"status": "Cancelled"}})
        await bot.send_message(chat_id, f"Job {job_id} cancelled.")
