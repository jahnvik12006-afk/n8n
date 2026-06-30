from core.bot import Bot
from core.database import Database
from middlewares.admin import ensure_admin
from ui.cards import build_job_card
from ui.templates import error_card


async def handle_jobs_command(bot: Bot, chat_id: int, message_id: int, text: str, parts: list[str]):
    if not await ensure_admin(chat_id):
        return

    status_filter = parts[1] if len(parts) > 1 else None
    query = {}
    if status_filter:
        query["status"] = status_filter.capitalize()

    jobs = await Database.db.jobs.find(query).sort("created_at", -1).limit(10).to_list(10)
    if not jobs:
        await bot.send_message(chat_id, "No jobs found.")
        return

    for job in jobs:
        card = build_job_card(job)
        await bot.send_message(chat_id, card)
