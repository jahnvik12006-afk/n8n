from core.bot import Bot
from core.logger import logger
from core.retry import with_retry


@with_retry()
async def send_video_to_channel(channel_id: str, file_path: str, caption: str) -> bool:
    try:
        bot = Bot.get()
        await bot.send_video(channel_id, file_path, caption=caption)
        return True
    except Exception as e:
        logger.exception("send_video_to_channel failed: %s", e)
        return False


@with_retry()
async def send_photo_to_channel(channel_id: str, photo_url: str, caption: str) -> bool:
    try:
        bot = Bot.get()
        await bot.send_photo(channel_id, photo_url, caption=caption)
        return True
    except Exception as e:
        logger.exception("send_photo_to_channel failed: %s", e)
        return False
