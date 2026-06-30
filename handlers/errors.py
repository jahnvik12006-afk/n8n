from core.bot import Bot
from core.logger import logger
from ui.templates import error_card


async def handle_error(bot: Bot, chat_id: int, error: Exception):
    logger.exception("Unhandled error for chat %s: %s", chat_id, error)
    try:
        await bot.send_message(chat_id, error_card(f"Internal error: {str(error)[:100]}"))
    except Exception:
        logger.error("Failed to send error message to %s", chat_id)
