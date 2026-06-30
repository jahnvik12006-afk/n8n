import asyncio
import os
import time

from core.config import config
from core.logger import logger


_temp_cleanup_running = False


async def start_scheduler():
    global _temp_cleanup_running
    if _temp_cleanup_running:
        return
    _temp_cleanup_running = True
    asyncio.create_task(_temp_cleanup_loop())
    logger.info("Scheduler started")


async def _temp_cleanup_loop():
    while True:
        await asyncio.sleep(config.DOWNLOAD_DELETE_TIMER)
        try:
            now = time.time()
            temp_dir = config.TEMP_DIR
            if not os.path.exists(temp_dir):
                continue
            for fname in os.listdir(temp_dir):
                fpath = os.path.join(temp_dir, fname)
                if os.path.isfile(fpath):
                    age = now - os.path.getmtime(fpath)
                    if age > config.DOWNLOAD_DELETE_TIMER:
                        os.remove(fpath)
                        logger.debug("Cleaned temp file: %s", fpath)
        except Exception as e:
            logger.exception("Temp cleanup error: %s", e)
