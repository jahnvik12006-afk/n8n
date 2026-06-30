from core.bot import Bot
from core.logger import logger
from middlewares.admin import ensure_admin
from services.search import perform_search
from ui.cards import build_search_card
from ui.buttons import view_detail_buttons
from ui.templates import error_card


async def handle_search(bot: Bot, chat_id: int, message_id: int, query: str):
    if not await ensure_admin(chat_id):
        return

    try:
        results = await perform_search(query)
        if not results:
            await bot.send_message(chat_id, error_card(f"No results for: {query}"))
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
        logger.exception("Search error: %s", e)
        await bot.send_message(chat_id, error_card(f"Search failed: {str(e)[:100]}"))
