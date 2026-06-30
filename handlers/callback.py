from core.bot import Bot
from core.database import Database
from core.logger import logger
from middlewares.admin import ensure_admin
from services.search import get_detail
from services.metadata import get_available_languages
from ui.cards import build_detail_card
from ui.buttons import language_selector, upload_mode_selector, channel_selector
from ui.dialogs import ask_start_episode, ask_end_episode
from ui.templates import error_card

_user_flow: dict = {}


async def handle_callback(bot: Bot, callback: dict):
    cb_data = callback.get("data", "")
    chat_id = callback["from"]["id"]
    msg = callback.get("message", {})
    message_id = msg.get("message_id", 0)
    cb_id = callback["id"]

    if not await ensure_admin(chat_id):
        await bot.answer_callback_query(cb_id, "Access denied")
        return

    parts = cb_data.split(":", 3)
    action = parts[0]

    try:
        if action == "view":
            slug = parts[1]
            anime = await get_detail(detail_path=slug)
            if not anime:
                await bot.answer_callback_query(cb_id, "Detail not found")
                return
            raw = anime.raw if hasattr(anime, "raw") else {}
            languages = get_available_languages(anime) or ["Dual Audio"]
            await bot.edit_message_text(chat_id, message_id, build_detail_card(raw),
                                        reply_markup=language_selector(slug, languages))
            await bot.answer_callback_query(cb_id)

        elif action == "lang":
            slug = parts[1]
            language = parts[2]
            await bot.edit_message_text(chat_id, message_id, f"Language: {language}",
                                        reply_markup=upload_mode_selector(slug, language))
            await bot.answer_callback_query(cb_id)

        elif action == "mode":
            slug = parts[1]
            language = parts[2]
            mode = parts[3]
            channels = await Database.db.channels.find().to_list(None)
            if not channels:
                await bot.send_message(chat_id, error_card("No sub-channels configured. Use /addsub first."))
                await bot.answer_callback_query(cb_id)
                return
            await bot.edit_message_text(chat_id, message_id, f"Mode: {mode}",
                                        reply_markup=channel_selector(slug, language, mode, channels))
            await bot.answer_callback_query(cb_id)

        elif action == "channel":
            slug = parts[1]
            language = parts[2]
            mode = parts[3]
            channel_id = parts[4]
            channel_name = parts[5] if len(parts) > 5 else channel_id
            _user_flow[chat_id] = {
                "slug": slug,
                "language": language,
                "mode": mode,
                "channel_id": channel_id,
                "channel_name": channel_name,
            }
            if mode == "single":
                await bot.send_message(chat_id, "Send episode number:")
            else:
                await bot.send_message(chat_id, ask_start_episode(slug, language))
            await bot.answer_callback_query(cb_id)

        elif action == "cancel":
            job_id = parts[1]
            await Database.db.jobs.update_one({"job_id": job_id}, {"$set": {"status": "Cancelled"}})
            await bot.edit_message_text(chat_id, message_id, f"Job {job_id} cancelled.")
            await bot.answer_callback_query(cb_id, "Cancelled")

        elif action == "cancel_flow":
            _user_flow.pop(chat_id, None)
            await bot.edit_message_text(chat_id, message_id, "Cancelled.")
            await bot.answer_callback_query(cb_id)

        elif action == "redirect":
            channel_id = parts[1]
            await bot.answer_callback_query(cb_id, f"Go to channel: {channel_id}")

        else:
            await bot.answer_callback_query(cb_id, "Unknown action")

    except Exception as e:
        logger.exception("Callback error: %s", e)
        await bot.answer_callback_query(cb_id, "Error processing request")


def get_user_flow(chat_id: int) -> dict | None:
    return _user_flow.get(chat_id)


def clear_user_flow(chat_id: int):
    _user_flow.pop(chat_id, None)
