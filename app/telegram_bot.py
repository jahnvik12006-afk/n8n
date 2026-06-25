"""Telegram bot — admin-only interface."""
import uuid
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes,
)
from telegram.constants import ParseMode
from app.config import TELEGRAM_BOT_TOKEN, TELEGRAM_ADMIN_ID
from app.agent import run_agent
from app.report_engine import generate_report
from app.tools.write_tools import add_pending, pop_pending
from app.tools.registry import TOOLS

logger = logging.getLogger(__name__)


def admin_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != TELEGRAM_ADMIN_ID:
            await update.message.reply_text("🚫 Access Denied.")
            return
        return await func(update, context)
    return wrapper


async def _reply(update: Update, text: str, parse_mode=ParseMode.MARKDOWN):
    for i in range(0, len(text), 4000):
        try:
            await update.message.reply_text(text[i:i+4000], parse_mode=parse_mode)
        except Exception:
            await update.message.reply_text(text[i:i+4000])


def _fmt_channel(data: dict) -> str:
    return (
        f"📺 *{data.get('title', 'N/A')}*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👥 Subscribers: `{int(data.get('subscribers') or 0):,}`\n"
        f"👁 Total Views: `{int(data.get('total_views') or 0):,}`\n"
        f"🎬 Videos: `{data.get('video_count', 'N/A')}`\n"
        f"📤 Recent Uploads: `{data.get('recent_uploads', 'N/A')}`\n"
    )


def _fmt_videos(data: dict) -> str:
    lines = ["🎬 *Video Performance Ranking*\n━━━━━━━━━━━━━━━"]
    for i, v in enumerate(data.get("videos", [])[:10], 1):
        lines.append(f"{i}\\. `{v['views']:,}` views — {v['title'][:50]}")
    return "\n".join(lines)


def _fmt_growth(data: dict) -> str:
    rows = data.get("growth_data", [])
    if not rows:
        return "📈 No growth data available."
    lines = ["📈 *Growth (Last 28 Days)*\n━━━━━━━━━━━━━━━"]
    total_views = sum(int(r[1]) for r in rows if len(r) > 1)
    total_subs = sum(int(r[2]) for r in rows if len(r) > 2)
    lines.append(f"👁 Total Views: `{total_views:,}`")
    lines.append(f"➕ Subs Gained: `{total_subs:,}`")
    lines.append(f"\n_Last 5 days:_")
    for r in rows[-5:]:
        lines.append(f"• {r[0]}: `{int(r[1]):,}` views, `+{int(r[2])}` subs")
    return "\n".join(lines)


def _fmt_ctr(data: dict) -> str:
    rows = data.get("ctr_data", [])
    if not rows:
        return "📊 No CTR data available."
    lines = ["📊 *CTR Analysis (Last 28 Days)*\n━━━━━━━━━━━━━━━"]
    for r in rows[-7:]:
        ctr = f"{float(r[2])*100:.1f}%" if len(r) > 2 else "N/A"
        lines.append(f"• {r[0]}: `{int(r[1]):,}` views — CTR: `{ctr}`")
    return "\n".join(lines)


def _fmt_seo(data: dict) -> str:
    lines = ["🔍 *SEO Audit*\n━━━━━━━━━━━━━━━"]
    for v in data.get("seo_data", [])[:5]:
        title_score = "✅" if 40 <= v["title_length"] <= 70 else "⚠️"
        desc_score = "✅" if v["description_length"] > 200 else "⚠️"
        tag_score = "✅" if v["tag_count"] >= 10 else "⚠️"
        lines.append(
            f"\n*{v['title'][:45]}...*\n"
            f"  {title_score} Title: `{v['title_length']}` chars\n"
            f"  {desc_score} Desc: `{v['description_length']}` chars\n"
            f"  {tag_score} Tags: `{v['tag_count']}`"
        )
    return "\n".join(lines)


@admin_only
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *HisuClaw v2\\.0*\n"
        "━━━━━━━━━━━━━━━\n"
        "AI\\-powered YouTube Channel Manager\n"
        "Hindi Manhwa/Manga Recaps 🎌\n\n"
        "Type /help to see all commands\\.",
        parse_mode=ParseMode.MARKDOWN_V2,
    )


@admin_only
async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📋 *HisuClaw Commands*\n"
        "━━━━━━━━━━━━━━━\n"
        "📊 *Analytics*\n"
        "/channel — Channel overview\n"
        "/videos — Video rankings\n"
        "/video `<id>` — Single video audit\n"
        "/growth — Growth trend\n"
        "/retention — Retention data\n"
        "/ctr — CTR analysis\n"
        "/seo — SEO audit\n"
        "/competitors `<id1> <id2>` — Competitor intel\n\n"
        "📝 *Content*\n"
        "/report — Full channel report\n"
        "/strategy — Content strategy\n\n"
        "✏️ *Updates \\(requires confirm\\)*\n"
        "/title `<video_id> <new title>`\n"
        "/description `<video_id> <text>`\n"
        "/tags `<video_id> <tag1,tag2>`\n\n"
        "💬 Or just ask anything\\!"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)


@admin_only
async def cmd_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⏳ Fetching channel data...")
    result = await TOOLS["AnalyzeChannel"].execute()
    await msg.delete()
    await _reply(update, _fmt_channel(result))


@admin_only
async def cmd_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⏳ Fetching videos...")
    result = await TOOLS["AnalyzeVideos"].execute(max_results=10)
    await msg.delete()
    await _reply(update, _fmt_videos(result))


@admin_only
async def cmd_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /video `<video_id>`", parse_mode=ParseMode.MARKDOWN)
        return
    msg = await update.message.reply_text("⏳ Auditing video...")
    result = await TOOLS["AnalyzeVideo"].execute(video_id=context.args[0])
    await msg.delete()
    text = (
        f"🎬 *{result.get('title', 'N/A')}*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👁 Views: `{int(result.get('views',0)):,}`\n"
        f"👍 Likes: `{int(result.get('likes',0)):,}`\n"
        f"💬 Comments: `{int(result.get('comments',0)):,}`\n"
        f"🏷 Tags: `{len(result.get('tags',[]))}`\n"
        f"📝 Desc length: `{len(result.get('description',''))}` chars\n"
    )
    await _reply(update, text)


@admin_only
async def cmd_growth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⏳ Fetching growth data...")
    result = await TOOLS["AnalyzeGrowth"].execute()
    await msg.delete()
    await _reply(update, _fmt_growth(result))


@admin_only
async def cmd_retention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⏳ Fetching retention data...")
    video_id = context.args[0] if context.args else None
    result = await TOOLS["AnalyzeRetention"].execute(video_id=video_id)
    await msg.delete()
    rows = result.get("retention_data", [])
    if not rows:
        await update.message.reply_text("📉 No retention data available.")
        return
    lines = ["📉 *Retention Data*\n━━━━━━━━━━━━━━━"]
    for r in rows[:10]:
        lines.append(f"• Video `{r[0]}` — Avg: `{r[1]}s` | `{r[2]:.1f}%`")
    await _reply(update, "\n".join(lines))


@admin_only
async def cmd_ctr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⏳ Fetching CTR data...")
    result = await TOOLS["AnalyzeCTR"].execute()
    await msg.delete()
    await _reply(update, _fmt_ctr(result))


@admin_only
async def cmd_seo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⏳ Running SEO audit...")
    result = await TOOLS["AnalyzeSEO"].execute()
    await msg.delete()
    await _reply(update, _fmt_seo(result))


@admin_only
async def cmd_competitors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /competitors `<channel_id1>` `[channel_id2]`", parse_mode=ParseMode.MARKDOWN)
        return
    msg = await update.message.reply_text("⏳ Analyzing competitors...")
    result = await TOOLS["AnalyzeCompetitors"].execute(channel_ids=context.args)
    await msg.delete()
    lines = ["🕵️ *Competitor Analysis*\n━━━━━━━━━━━━━━━"]
    for c in result.get("competitors", []):
        lines.append(
            f"\n📺 *{c['channel_title']}*\n"
            f"  👥 Subs: `{int(c.get('subscribers') or 0):,}`\n"
            f"  👁 Views: `{int(c.get('total_views') or 0):,}`\n"
            f"  🎬 Recent videos: `{len(c.get('recent_videos', []))}`"
        )
    await _reply(update, "\n".join(lines))


@admin_only
async def cmd_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⏳ Generating report... (this may take 30s)")
    report = await generate_report()
    await msg.delete()
    await _reply(update, f"📊 *Channel Report*\n━━━━━━━━━━━━━━━\n{report}")


@admin_only
async def cmd_strategy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⏳ Generating strategy...")
    result = await TOOLS["GenerateContentStrategy"].execute()
    await msg.delete()
    await _reply(update, f"🗓 *Content Strategy*\n━━━━━━━━━━━━━━━\n{result.get('raw', 'N/A')}")


async def _send_confirmation(update: Update, token: str, field: str, video_id: str, new_value: str):
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ CONFIRM", callback_data=f"confirm:{token}"),
        InlineKeyboardButton("❌ DECLINE", callback_data=f"decline:{token}"),
    ]])
    text = (
        f"⚠️ *{field.title()} Update Request*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🎬 Video: `{video_id}`\n"
        f"📝 New {field}:\n`{str(new_value)[:300]}`\n\n"
        f"_Confirm to apply this change to YouTube\\._"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=keyboard)


@admin_only
async def cmd_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /title `<video_id>` `<new title>`", parse_mode=ParseMode.MARKDOWN)
        return
    video_id = context.args[0]
    new_title = " ".join(context.args[1:])
    token = str(uuid.uuid4())
    add_pending(token, {"video_id": video_id, "field": "title", "new_value": new_title})
    await _send_confirmation(update, token, "title", video_id, new_title)


@admin_only
async def cmd_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /description `<video_id>` `<text>`", parse_mode=ParseMode.MARKDOWN)
        return
    video_id = context.args[0]
    new_desc = " ".join(context.args[1:])
    token = str(uuid.uuid4())
    add_pending(token, {"video_id": video_id, "field": "description", "new_value": new_desc})
    await _send_confirmation(update, token, "description", video_id, new_desc)


@admin_only
async def cmd_tags(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /tags `<video_id>` `<tag1,tag2,...>`", parse_mode=ParseMode.MARKDOWN)
        return
    video_id = context.args[0]
    tags = context.args[1].split(",")
    token = str(uuid.uuid4())
    add_pending(token, {"video_id": video_id, "field": "tags", "new_value": tags})
    await _send_confirmation(update, token, "tags", video_id, str(tags))


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != TELEGRAM_ADMIN_ID:
        await query.answer("🚫 Access Denied.")
        return
    await query.answer()
    action, token = query.data.split(":", 1)
    pending = pop_pending(token)

    if not pending:
        await query.edit_message_text("⚠️ Request expired or already handled.")
        return

    if action == "decline":
        await query.edit_message_text("❌ Update declined. No changes made.")
        return

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
        await tool.execute(**kwargs)
        await query.edit_message_text(f"✅ *{field.title()} updated successfully\\!*\n`{video_id}`", parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        await query.edit_message_text(f"❌ Error: {e}")


@admin_only
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("🤔 Thinking...")
    response = await run_agent(update.message.text)
    await msg.delete()
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
