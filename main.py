import asyncio
import sys

import uvloop

from core.bot import Bot
from core.config import config
from core.database import Database
from core.http_client import HttpClient
from core.logger import logger
from core.scheduler import start_scheduler
from core.webhook_server import start_server
from core.worker_pool import ensure_pool, requeue_pending_jobs


async def main():
    logger.info("Starting AutoAnimeBot v2.0")

    try:
        await Database.connect()
        logger.info("MongoDB connected")

        await HttpClient.get()
        logger.info("HTTP client initialized")

        await ensure_pool()
        await requeue_pending_jobs()
        logger.info("Worker pool ready")

        await start_scheduler()
        logger.info("Scheduler started")

        if config.WEBHOOK_URL:
            bot = Bot.get()
            webhook_full = f"{config.WEBHOOK_URL}/webhook"
            result = await bot.set_webhook(webhook_full, config.WEBHOOK_SECRET)
            logger.info("Webhook set: %s -> %s", webhook_full, result)

        runner = await start_server()

        logger.info("AutoAnimeBot is running. Press Ctrl+C to stop.")

        while True:
            await asyncio.sleep(3600)

    except asyncio.CancelledError:
        logger.info("Shutdown requested")
    except Exception as e:
        logger.exception("Fatal error: %s", e)
    finally:
        await HttpClient.close()
        await Database.disconnect()
        logger.info("Shutdown complete")


if __name__ == "__main__":
    uvloop.install()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt")
        sys.exit(0)
