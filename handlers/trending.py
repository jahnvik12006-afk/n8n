from core.bot import Bot
from core.logger import logger
from middlewares.admin import ensure_admin
from services.api_client import get_trending, get_content_list
from ui.cards import build_search_card
from ui.buttons import view_detail_buttons
from ui.templates import error_card

CONTENT_TYPES = {
    "trending-cinema": "5692654647815587592",
    "trending": "4516404531735022304",
    "bollywood": "414907768299210008",
    "south-indian": "3859721901924910512",
    "hollywood": "8019599703232971616",
    "asian": "5429170738815291968",
    "top-series": "4741626294545400336",
    "anime": "8434602210994128512",
    "reality-tv": "1255898847918934600",
    "indian-drama": "4903182713986896328",
    "korean-drama": "7878715743607948784",
    "chinese-drama": "8788126208987989488",
    "western-tv": "3910636007619709856",
    "turkish-drama": "5177200225164885656",
}


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
    if not await ensure_admin(chat_id):
        return

    try:
        page = 1
        if len(parts) > 1:
            page = max(1, int(parts[1]))

        results = await get_content_list("trending-cinema", page=page)
        if not results:
            await bot.send_message(chat_id, error_card("No latest found"))
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
        logger.exception("Latest error: %s", e)
        await bot.send_message(chat_id, error_card(str(e)[:100]))


async def handle_content(bot: Bot, chat_id: int, message_id: int, text: str, parts: list[str]):
    if not await ensure_admin(chat_id):
        return

    try:
        content_type = parts[1] if len(parts) > 1 else "anime"
        page = 1
        if len(parts) > 2:
            page = max(1, int(parts[2]))

        type_id = CONTENT_TYPES.get(content_type)
        if not type_id:
            types = ", ".join(CONTENT_TYPES.keys())
            await bot.send_message(chat_id, error_card(f"Invalid type. Use: {types}"))
            return

        results = await get_content_list(content_type, page=page)
        if not results:
            await bot.send_message(chat_id, error_card(f"No {content_type} found"))
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
        logger.exception("Content error: %s", e)
        await bot.send_message(chat_id, error_card(str(e)[:100]))
