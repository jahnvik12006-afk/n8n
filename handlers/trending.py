from core.bot import Bot
from core.logger import logger
from middlewares.admin import ensure_admin
from services.api_client import get_trending
from ui.cards import build_search_card
from ui.buttons import view_detail_buttons
from ui.templates import error_card


async def handle_trending(bot: Bot, chat_id: int, message_id: int, text: str, parts: list[str]):
    if not await ensure_admin(chat_id):
        return

    try:
        page = 0
        if len(parts) > 1:
            page = max(0, int(parts[1]) - 1)

        results = await get_trending(page=page)
        if not results:
            await bot.send_message(chat_id, error_card("No trending found"))
            return

        for anime in results[:5]:
            raw = anime.raw if hasattr(anime, "raw") else {}
            card = build_search_card(raw)
            cover = raw.get("cover", {})
            cover_url = cover.get("url", "") if isinstance(cover, dict) else ""
            reply_markup = view_detail_buttons(anime.slug)
            if cover_url:
                await bot.send_photo(chat_id, cover_url, caption=card, reply_markup=reply_markup)
            else:
                await bot.send_message(chat_id, card, reply_markup=reply_markup)

    except Exception as e:
        logger.exception("Trending error: %s", e)
        await bot.send_message(chat_id, error_card(str(e)[:100]))


async def handle_latest(bot: Bot, chat_id: int, message_id: int, text: str, parts: list[str]):
    await handle_trending(bot, chat_id, message_id, text, parts)
