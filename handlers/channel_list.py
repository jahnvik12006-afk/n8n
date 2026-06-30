from core.bot import Bot
from core.config import config
from core.database import Database
from core.logger import logger
from middlewares.admin import ensure_admin
from ui.theme import box_top, box_bot, kv_emoji, tag_bold
from ui.html_builder import build_inline_keyboard


async def handle_listchannels(bot: Bot, chat_id: int, message_id: int, text: str, parts: list[str]):
    if not await ensure_admin(chat_id):
        return

    channels = await Database.db.memberships.find(
        {"is_admin": True}
    ).sort("title", 1).to_list(None)

    if not channels:
        await bot.send_message(
            chat_id,
            "No channels found.\n\n"
            "Add me as <b>admin</b> to a channel, then use /listchannels again."
        )
        return

    buttons = []
    for ch in channels:
        cid = ch["chat_id"]
        label = ch.get("title") or ch.get("username") or cid
        buttons.append([{"text": label, "callback_data": f"chsel:{cid}:{label}"}])

    main_id = config.MAIN_CHANNEL
    existing_subs = {ch.get("channel_id") for ch in
                     await Database.db.channels.find({}, {"channel_id": 1}).to_list(None)}

    lines = [
        box_top(40),
        tag_bold("📢 Known Channels"),
        "",
    ]
    for ch in channels:
        cid = ch["chat_id"]
        title = ch.get("title") or ch.get("username") or cid
        role = ""
        if cid == main_id:
            role = " ⭐ MAIN"
        elif cid in existing_subs:
            role = " 📋 SUB"
        lines.append(kv_emoji("📺", title[:20], role.strip() or "—"))
    lines.append("")
    lines.append("Tap a channel below to set as Main or Sub.")
    lines.append(box_bot(40))

    await bot.send_message(
        chat_id,
        "\n".join(lines),
        reply_markup=build_inline_keyboard(buttons),
    )
