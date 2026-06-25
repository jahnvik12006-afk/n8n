"""Telegram bot — admin-only interface."""
import asyncio
import uuid
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes,
)
from app.config import TELEGRAM_BOT_TOKEN, TELEGRAM_ADMIN_ID
from app.agent import run_agent
from app.report_engine import generate_report
from app.tools.write_tools import add_pending, pop_pending
from app.tools.registry import TOOLS

logger = logging.getLogger(__name__)


def admin_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != TELEGRAM_ADMIN_ID:
            await update.message.reply_text("Access Denied.")
            return
        return await func(update, context)
    return wrapper


async def _reply(update: Update, text: str):
    # Telegram message limit 4096 chars
    for i in range(0, len(text), 4000):
        await update.message.reply_text(text[i:i+4000])


@admin_only
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 HisuClaw v2.0 — Hindi Manhwa YouTube Agent\n\n"
        "Use /help for commands."
    )


@admin_only
async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📋 *Commands*\n"
        "/channel — Channel overview\n"
        "/videos — Video list\n"
        "/video <id> — Single video audit\n"
        "/growth — Growth trend\n"
        "/retention — Retention data\n"
        "/ctr — CTR analysis\n"
        "/seo — SEO audit\n"
        "/competitors <id1> [id2...] — Competitor analysis\n"
        "/report — Generate & send report\n"
        "/title <video_id> <new title> — Suggest title update\n"
        "/description <video_id> — Suggest description update\n"
        "/tags <video_id> <tag1,tag2,...> — Suggest tags update\n"
        "/strategy — Content strategy\n"
        "\nOr just type any question!"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


@admin_only
async def cmd_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = await TOOLS["AnalyzeChannel"].execute()
    await _reply(update, json.dumps(result, indent=2))


@admin_only
async def cmd_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = await TOOLS["AnalyzeVideos"].execute(max_results=10)
    lines = [f"{v['title']} — {v['views']:,} views" for v in result.get("videos", [])]
    await _reply(update, "\n".join(lines) or "No videos found.")


@admin_only
async def cmd_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /video <video_id>")
        return
    result = await TOOLS["AnalyzeVideo"].execute(video_id=args[0])
    await _reply(update, json.dumps(result, indent=2))


@admin_only
async def cmd_growth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = await TOOLS["AnalyzeGrowth"].execute()
    await _reply(update, json.dumps(result, indent=2))


@admin_only
async def cmd_retention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video_id = context.args[0] if context.args else None
    result = await TOOLS["AnalyzeRetention"].execute(video_id=video_id)
    await _reply(update, json.dumps(result, indent=2))


@admin_only
async def cmd_ctr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = await TOOLS["AnalyzeCTR"].execute()
    await _reply(update, json.dumps(result, indent=2))


@admin_only
async def cmd_seo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = await TOOLS["AnalyzeSEO"].execute()
    await _reply(update, json.dumps(result, indent=2))


@admin_only
async def cmd_competitors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /competitors <channel_id1> [channel_id2 ...]")
        return
    result = await TOOLS["AnalyzeCompetitors"].execute(channel_ids=context.args)
    await _reply(update, json.dumps(result, indent=2))


@admin_only
async def cmd_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Generating report...")
    report = await generate_report()
    await _reply(update, report)


@admin_only
async def cmd_strategy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = await TOOLS["GenerateContentStrategy"].execute()
    await _reply(update, result.get("raw", "No strategy generated."))


async def _send_confirmation(update: Update, token: str, field: str, video_id: str, new_value: str):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ CONFIRM", callback_data=f"confirm:{token}"),
            InlineKeyboardButton("❌ DECLINE", callback_data=f"decline:{token}"),
        ]
    ])
    text = (
        f"🔔 *{field.title()} Update Request*\n"
        f"Video ID: `{video_id}`\n"
        f"New value:\n`{new_value[:300]}`"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)


@admin_only
async def cmd_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /title <video_id> <new title>")
        return
    video_id = context.args[0]
    new_title = " ".join(context.args[1:])
    token = str(uuid.uuid4())
    add_pending(token, {"video_id": video_id, "field": "title", "new_value": new_title})
    await _send_confirmation(update, token, "title", video_id, new_title)


@admin_only
async def cmd_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /description <video_id> <new description>")
        return
    video_id = context.args[0]
    new_desc = " ".join(context.args[1:])
    token = str(uuid.uuid4())
    add_pending(token, {"video_id": video_id, "field": "description", "new_value": new_desc})
    await _send_confirmation(update, token, "description", video_id, new_desc)


@admin_only
async def cmd_tags(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /tags <video_id> <tag1,tag2,...>")
        return
    video_id = context.args[0]
    tags = context.args[1].split(",")
    token = str(uuid.uuid4())
    add_pending(token, {"video_id": video_id, "field": "tags", "new_value": tags})
    await _send_confirmation(update, token, "tags", video_id, str(tags))


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != TELEGRAM_ADMIN_ID:
        await query.answer("Access Denied.")
        return

    await query.answer()
    action, token = query.data.split(":", 1)
    pending = pop_pending(token)

    if not pending:
        await query.edit_message_text("⚠️ Request expired or already handled.")
        return

    if action == "decline":
        await query.edit_message_text("❌ Request declined.")
        return

    # CONFIRM — execute the write
    field = pending["field"]
    video_id = pending["video_id"]
    new_value = pending["new_value"]

    tool_map = {"title": "UpdateTitle", "description": "UpdateDescription", "tags": "UpdateTags"}
    tool = TOOLS[tool_map[field]]

    kwargs = {"video_id": video_id, "confirmed": True}
    if field == "title":
        kwargs["new_title"] = new_value
    elif field == "description":
        kwargs["new_description"] = new_value
    elif field == "tags":
        kwargs["new_tags"] = new_value

    try:
        result = await tool.execute(**kwargs)
        await query.edit_message_text(f"✅ {field.title()} updated successfully!\n{json.dumps(result)}")
    except Exception as e:
        await query.edit_message_text(f"❌ Error: {e}")


@admin_only
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Free-form chat routed through AI agent."""
    user_text = update.message.text
    await update.message.reply_text("⏳ Thinking...")
    response = await run_agent(user_text)
    await _reply(update, response)


def build_application() -> Application:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("channel", cmd_channel))
    app.add_handler(CommandHandler("videos", cmd_videos))
    app.add_handler(CommandHandler("video", cmd_video))
    app.add_handler(CommandHandler("growth", cmd_growth))
    app.add_handler(CommandHandler("retention", cmd_retention))
    app.add_handler(CommandHandler("ctr", cmd_ctr))
    app.add_handler(CommandHandler("seo", cmd_seo))
    app.add_handler(CommandHandler("competitors", cmd_competitors))
    app.add_handler(CommandHandler("report", cmd_report))
    app.add_handler(CommandHandler("strategy", cmd_strategy))
    app.add_handler(CommandHandler("title", cmd_title))
    app.add_handler(CommandHandler("description", cmd_description))
    app.add_handler(CommandHandler("tags", cmd_tags))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    return app
