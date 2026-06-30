from core.bot import Bot
from core.config import config
from ui.dialogs import start_dialog


async def handle_start(bot: Bot, chat_id: int, message_id: int, text: str, parts: list[str] | None = None):
    first_name = "User"
    cover = config.BOT_START_IMAGE
    msg = start_dialog(first_name)

    if cover:
        await bot.send_photo(chat_id, cover, caption=msg)
    else:
        await bot.send_message(chat_id, msg)
