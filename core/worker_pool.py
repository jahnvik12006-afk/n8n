import asyncio

from core.config import config
from core.database import Database
from core.uploader import upload_to_channel
from services.api_client import get_play_url
from core.bot import Bot
from core.logger import logger
from ui.cards import build_upload_progress_card
from ui.html_builder import build_button


_job_queue: asyncio.Queue = None
_workers: list[asyncio.Task] = []
_semaphore: asyncio.Semaphore = None


async def ensure_pool():
    global _job_queue, _semaphore
    if _job_queue is None:
        _job_queue = asyncio.Queue()
        _semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_UPLOADS)
        for _ in range(config.MAX_CONCURRENT_UPLOADS):
            task = asyncio.create_task(_worker_loop())
            _workers.append(task)


async def _worker_loop():
    while True:
        job = await _job_queue.get()
        async with _semaphore:
            try:
                await _process_job(job)
            except Exception as e:
                logger.exception("Worker: job %s failed: %s", job.get("job_id"), e)
                await Database.db.jobs.update_one(
                    {"job_id": job["job_id"]},
                    {"$set": {"status": "Failed", "error": str(e)}},
                )


async def _process_job(job: dict):
    bot = Bot.get()
    admin_id = job["admin_id"]
    msg_id = job.get("message_id")
    job_id = job["job_id"]
    episodes = job["episodes"]
    channel_id = job["channel_id"]
    subject = job.get("subject", {})
    slug = job.get("slug", "")
    language = job.get("language", "")

    await Database.db.jobs.update_one(
        {"job_id": job_id}, {"$set": {"status": "Downloading"}}
    )

    for i, ep in enumerate(episodes):
        season = ep.get("season", 1)
        episode = ep.get("episode", 1)
        progress_text = f"{i + 1}/{len(episodes)}"

        await bot.edit_message_text(
            admin_id, msg_id,
            build_upload_progress_card(job_id, "Downloading", slug, season, episode, progress_text),
            reply_markup=build_button("Cancel", f"cancel:{job_id}"),
        )

        cdn_url = await get_play_url(subject, season, episode, language)
        if cdn_url is None:
            await Database.db.jobs.update_one(
                {"job_id": job_id}, {"$set": {"status": "Failed", "error": f"Play URL resolve failed ep {episode}"}}
            )
            return

        await Database.db.jobs.update_one(
            {"job_id": job_id}, {"$set": {"status": "Uploading"}}
        )

        await bot.edit_message_text(
            admin_id, msg_id,
            build_upload_progress_card(job_id, "Uploading", slug, season, episode, progress_text),
            reply_markup=build_button("Cancel", f"cancel:{job_id}"),
        )

        success = await upload_to_channel(channel_id, cdn_url, subject, season, episode, language)
        if not success:
            await Database.db.jobs.update_one(
                {"job_id": job_id}, {"$set": {"status": "Failed", "error": f"Upload failed ep {episode}"}}
            )
            return

    await Database.db.jobs.update_one(
        {"job_id": job_id}, {"$set": {"status": "Completed"}}
    )

    await bot.edit_message_text(
        admin_id, msg_id,
        build_upload_progress_card(job_id, "Completed", slug, 0, 0, f"{len(episodes)}/{len(episodes)}"),
    )


async def enqueue_job(job: dict):
    global _job_queue
    await ensure_pool()
    await _job_queue.put(job)


async def requeue_pending_jobs():
    await ensure_pool()
    pending = await Database.db.jobs.find({"status": {"$in": ["Downloading", "Uploading", "Pending"]}}).to_list(None)
    for job in pending:
        await Database.db.jobs.update_one(
            {"job_id": job["job_id"]}, {"$set": {"status": "Pending"}}
        )
        await _job_queue.put(job)
    if pending:
        logger.info("Requeued %d pending jobs", len(pending))
