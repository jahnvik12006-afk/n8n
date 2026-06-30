from core.bot import Bot
from core.database import Database
from core.logger import logger
from middlewares.admin import ensure_admin
from services.search import get_detail
from services.metadata import extract_episode_range
from ui.dialogs import job_queued_card
from ui.templates import error_card
from ui.html_builder import build_button

import uuid
from core.worker_pool import enqueue_job


async def handle_upload(bot: Bot, chat_id: int, message_id: int, text: str, parts: list[str]):
    pass


async def handle_single_upload(bot: Bot, chat_id: int, reply_to_msg_id: int, slug: str, language: str, episode: int, channel_id: str):
    if not await ensure_admin(chat_id):
        return

    job_id = uuid.uuid4().hex[:12]
    try:
        anime = await get_detail(detail_path=slug)
        if not anime:
            await bot.send_message(chat_id, error_card("Anime not found"))
            return

        subject = anime.raw if hasattr(anime, "raw") else {}
        episodes = [{"season": anime.season or 1, "episode": episode}]
        job = {
            "job_id": job_id,
            "admin_id": chat_id,
            "message_id": reply_to_msg_id,
            "status": "Pending",
            "subject": subject,
            "slug": slug,
            "language": language,
            "episodes": episodes,
            "channel_id": channel_id,
            "channel_name": channel_id,
        }
        await Database.db.jobs.insert_one(job)
        await enqueue_job(job)

        await bot.send_message(chat_id, job_queued_card(job_id, slug, 1, language, channel_id),
                               reply_markup=build_button("Cancel", f"cancel:{job_id}"))

    except Exception as e:
        logger.exception("Single upload error: %s", e)
        await bot.send_message(chat_id, error_card(str(e)[:100]))


async def handle_multi_upload(bot: Bot, chat_id: int, reply_to_msg_id: int, slug: str, language: str, start_ep: int, end_ep: int, channel_id: str):
    if not await ensure_admin(chat_id):
        return

    job_id = uuid.uuid4().hex[:12]
    try:
        anime = await get_detail(detail_path=slug)
        if not anime:
            await bot.send_message(chat_id, error_card("Anime not found"))
            return

        subject = anime.raw if hasattr(anime, "raw") else {}
        episodes = extract_episode_range(anime, start_ep, end_ep)
        job = {
            "job_id": job_id,
            "admin_id": chat_id,
            "message_id": reply_to_msg_id,
            "status": "Pending",
            "subject": subject,
            "slug": slug,
            "language": language,
            "episodes": episodes,
            "channel_id": channel_id,
            "channel_name": channel_id,
        }
        await Database.db.jobs.insert_one(job)
        await enqueue_job(job)

        await bot.send_message(chat_id, job_queued_card(job_id, slug, len(episodes), language, channel_id),
                               reply_markup=build_button("Cancel", f"cancel:{job_id}"))

    except Exception as e:
        logger.exception("Multi upload error: %s", e)
        await bot.send_message(chat_id, error_card(str(e)[:100]))
