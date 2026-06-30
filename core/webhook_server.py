import asyncio

from aiohttp import web

from core.bot import Bot
from core.config import config
from core.logger import logger
from core.database import Database
from handlers.callback import handle_callback, get_user_flow, clear_user_flow
from handlers.start import handle_start
from handlers.admin import handle_admin_command
from handlers.search import handle_search
from handlers.slug import handle_slug
from handlers.upload import handle_single_upload, handle_multi_upload
from handlers.channels import handle_channel_command
from handlers.channel_list import handle_listchannels
from handlers.jobs import handle_jobs_command
from handlers.trending import handle_trending, handle_latest, handle_content
from ui.templates import error_card


async def webhook_handler(request: web.Request) -> web.Response:
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if config.WEBHOOK_SECRET and secret != config.WEBHOOK_SECRET:
        return web.Response(status=403)

    body = await request.json()
    asyncio.create_task(process_update(body))
    return web.Response(status=200)


COMMAND_MAP = {
    "/start": handle_start,
    "/help": handle_start,
    "/admin": handle_admin_command,
    "/stats": handle_admin_command,
    "/logs": handle_admin_command,
    "/reload": handle_admin_command,
    "/cache": handle_admin_command,
    "/jobs": handle_jobs_command,
    "/broadcast": handle_admin_command,
    "/cancel": handle_admin_command,
    "/setmain": handle_channel_command,
    "/addsub": handle_channel_command,
    "/removesub": handle_channel_command,
    "/listsub": handle_channel_command,
    "/listchannels": handle_listchannels,
    "/post": handle_slug,
    "/trending": handle_trending,
    "/latest": handle_latest,
    "/content": handle_content,
}


async def process_update(update: dict):
    try:
        bot = Bot.get()

        if "callback_query" in update:
            await handle_callback(bot, update["callback_query"])
            return

        if "my_chat_member" in update:
            await _handle_my_chat_member(update["my_chat_member"])
            return

        if "message" not in update:
            return

        msg = update["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "").strip()
        message_id = msg["message_id"]

        if not text:
            return

        parts = text.split()
        command = parts[0].split("@")[0]

        handler = COMMAND_MAP.get(command)
        if handler:
            await handler(bot, chat_id, message_id, text, parts)
            return

        if command.startswith("/"):
            return

        flow = get_user_flow(chat_id)
        if flow:
            mode = flow.get("mode")
            slug = flow.get("slug", "")
            language = flow.get("language", "")
            channel_id = flow.get("channel_id", "")
            channel_name = flow.get("channel_name", "")

            if "start_ep" not in flow:
                try:
                    ep = int(text)
                    if mode == "single":
                        clear_user_flow(chat_id)
                        await handle_single_upload(bot, chat_id, message_id, slug, language, ep, channel_id)
                        return
                    else:
                        flow["start_ep"] = ep
                        from ui.dialogs import ask_end_episode
                        text, markup = ask_end_episode(slug, language, ep)
                        await bot.send_message(chat_id, text, reply_markup=markup)
                        return
                except ValueError:
                    await bot.send_message(chat_id, error_card("Invalid episode number."))
                    return

            elif "start_ep" in flow and mode == "multi":
                try:
                    end_ep = int(text)
                    clear_user_flow(chat_id)
                    await handle_multi_upload(bot, chat_id, message_id, slug, language, flow["start_ep"], end_ep, channel_id)
                    return
                except ValueError:
                    await bot.send_message(chat_id, error_card("Invalid episode number."))
                    return

        await handle_search(bot, chat_id, message_id, text)

    except Exception as e:
        logger.exception("Error processing update: %s", e)


async def _handle_my_chat_member(member_update: dict):
    try:
        chat = member_update.get("chat", {})
        new = member_update.get("new_chat_member", {})
        status = new.get("status", "")
        chat_id = str(chat.get("id", ""))
        if not chat_id:
            return

        if status == "administrator":
            await Database.db.memberships.update_one(
                {"chat_id": chat_id},
                {"$set": {
                    "chat_id": chat_id,
                    "title": chat.get("title", ""),
                    "username": chat.get("username", ""),
                    "type": chat.get("type", ""),
                    "is_admin": True,
                }},
                upsert=True,
            )
            logger.info("Bot added as admin to: %s (%s)", chat.get("title", chat_id), chat_id)
        elif status in ("left", "kicked"):
            await Database.db.memberships.delete_one({"chat_id": chat_id})
            logger.info("Bot removed from: %s (%s)", chat.get("title", chat_id), chat_id)
    except Exception as e:
        logger.exception("Error handling my_chat_member: %s", e)


async def health_handler(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"}, status=200)


async def start_server():
    app = web.Application()
    app.router.add_get("/", health_handler)
    app.router.add_get("/health", health_handler)
    app.router.add_post("/webhook", webhook_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, config.WEBHOOK_HOST, config.WEBHOOK_PORT)
    await site.start()
    logger.info("Webhook server started on %s:%s", config.WEBHOOK_HOST, config.WEBHOOK_PORT)
    return runner
