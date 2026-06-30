from core.bot import Bot
from core.logger import logger
from middlewares.admin import ensure_admin
from services.search import get_detail
from services.metadata import get_available_languages
from ui.cards import build_detail_card
from ui.buttons import language_selector
from ui.templates import error_card


async def handle_slug(bot: Bot, chat_id: int, message_id: int, text: str, parts: list[str]):
    if not await ensure_admin(chat_id):
        return

    if len(parts) < 2:
        await bot.send_message(chat_id, error_card("Usage: /post <slug>"))
        return

    slug = parts[1]
    try:
        anime = await get_detail(detail_path=slug)
        if not anime:
            await bot.send_message(chat_id, error_card(f"No detail found for: {slug}"))
            return

        raw = anime.raw if hasattr(anime, "raw") else {}
        card = build_detail_card(raw)
        languages = get_available_languages(anime)
        reply_markup = language_selector(slug, languages) if languages else None

        cover = raw.get("cover", {})
        cover_url = cover.get("url", "") if isinstance(cover, dict) else ""
        if cover_url:
            await bot.send_photo(chat_id, cover_url, caption=card, reply_markup=reply_markup)
        else:
            await bot.send_message(chat_id, card, reply_markup=reply_markup)

    except Exception as e:
        logger.exception("Slug error: %s", e)
        await bot.send_message(chat_id, error_card(f"Failed: {str(e)[:100]}"))
