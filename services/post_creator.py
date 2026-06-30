from ui.cards import build_promo_card
from ui.html_builder import build_button
from core.bot import Bot
from core.config import config
from core.logger import logger


async def post_promo_to_main_channel(subject: dict, season: int, episode: int, language: str, sub_channel_id: str):
    bot = Bot.get()
    main_channel = config.MAIN_CHANNEL
    if not main_channel:
        logger.warning("MAIN_CHANNEL not configured, skipping promo")
        return

    card_text = build_promo_card(subject, season, episode, language)
    reply_markup = build_button("DOWNLOAD NOW", f"redirect:{sub_channel_id}")

    try:
        cover = subject.get("cover", {})
        cover_url = cover.get("url", "") if isinstance(cover, dict) else ""
        if cover_url:
            await bot.send_photo(main_channel, cover_url, caption=card_text, reply_markup=reply_markup)
        else:
            await bot.send_message(main_channel, card_text, reply_markup=reply_markup)
        logger.info("Promo posted to %s", main_channel)
    except Exception as e:
        logger.exception("Failed to post promo: %s", e)
