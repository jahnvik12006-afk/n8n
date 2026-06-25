"""Telegram bot — admin-only, full UI with all Telegram features."""
import uuid
import json
import logging
import asyncio
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
    MenuButtonCommands,
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes,
)
from telegram.constants import ParseMode, ChatAction
from telegram.helpers import escape_markdown
from app.config import TELEGRAM_BOT_TOKEN, TELEGRAM_ADMIN_ID
from app.agent import run_agent
from app.report_engine import generate_report
from app.tools.write_tools import add_pending, pop_pending
from app.tools.registry import TOOLS

logger = logging.getLogger(__name__)

# ── Main Menu Keyboard ─────────────────────────────────────────────────────────
MAIN_MENU = ReplyKeyboardMarkup(
    [
        ["📊 Channel", "🎬 Videos", "📈 Growth"],
        ["📉 Retention", "🎯 CTR", "🔍 SEO"],
        ["🕵️ Competitors", "📋 Report", "🗓 Strategy"],
    ],
    resize_keyboard=True,
    input_field_placeholder="Choose an option or ask anything...",
)

MENU_MAP = {
    "📊 Channel": "channel",
    "🎬 Videos": "videos",
    "📈 Growth": "growth",
    "📉 Retention": "retention",
    "🎯 CTR": "ctr",
    "🔍 SEO": "seo",
    "📋 Report": "report",
    "🗓 Strategy": "strategy",
}


# ── Helpers ────────────────────────────────────────────────────────────────────
def admin_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != TELEGRAM_ADMIN_ID:
            await update.message.reply_text("🚫 *Access Denied*", parse_mode=ParseMode.MARKDOWN)
            return
        return await func(update, context)
    return wrapper


def em(text: str) -> str:
    """Escape for MarkdownV2."""
    return escape_markdown(str(text), version=2)


async def typing(update: Update):
    await update.message.chat.send_action(ChatAction.TYPING)


async def _send(update: Update, text: str, md=True, reply_markup=None):
    parse = ParseMode.MARKDOWN if md else None
    for i in range(0, len(text), 4000):
        chunk = text[i:i+4000]
        try:
            await update.message.reply_text(chunk, parse_mode=parse, reply_markup=reply_markup if i == 0 else None)
        except Exception:
            await update.message.reply_text(chunk, reply_markup=reply_markup if i == 0 else None)


# ── Formatters ─────────────────────────────────────────────────────────────────
def _bar(value: float, max_val: float, width: int = 10) -> str:
    filled = int((value / max_val) * width) if max_val > 0 else 0
    return "█" * filled + "░" * (width - filled)


def _fmt_channel(d: dict) -> str:
    subs = int(d.get("subscribers") or 0)
    views = int(d.get("total_views") or 0)
    return (
        f"📺 *{d.get('title', 'N/A')}*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 Subscribers  `{subs:,}`\n"
        f"👁 Total Views   `{views:,}`\n"
        f"🎬 Videos        `{d.get('video_count', '?')}`\n"
        f"📤 Recent Uploads `{d.get('recent_uploads', '?')}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"||_Tap to see full analytics_||"
    )


def _fmt_videos(d: dict) -> str:
    videos = d.get("videos", [])
    if not videos:
        return "🎬 No videos found."
    max_views = videos[0]["views"] if videos else 1
    lines = ["🎬 *Top Videos — Performance Ranking*", "━━━━━━━━━━━━━━━━━━━━"]
    medals = ["🥇", "🥈", "🥉"]
    for i, v in enumerate(videos[:10]):
        medal = medals[i] if i < 3 else f"`{i+1}.`"
        bar = _bar(v["views"], max_views)
        lines.append(f"{medal} {bar} `{v['views']:,}`")
        lines.append(f"    _{v['title'][:55]}_")
    return "\n".join(lines)


def _fmt_growth(d: dict) -> str:
    rows = d.get("growth_data", [])
    if not rows:
        return "📈 No growth data."
    total_v = sum(int(r[1]) for r in rows if len(r) > 1)
    total_s = sum(int(r[2]) for r in rows if len(r) > 2)
    total_l = sum(int(r[3]) for r in rows if len(r) > 3)
    net = total_s - total_l
    trend = "📈" if net > 0 else "📉"
    lines = [
        "📈 *Growth — Last 28 Days*", "━━━━━━━━━━━━━━━━━━━━",
        f"👁 Views:        `{total_v:,}`",
        f"➕ Subs Gained:  `{total_s:,}`",
        f"➖ Subs Lost:    `{total_l:,}`",
        f"{trend} Net Growth:   `{net:+,}`",
        "", "📅 *Daily Trend (last 7 days)*",
    ]
    max_v = max((int(r[1]) for r in rows if len(r) > 1), default=1)
    for r in rows[-7:]:
        bar = _bar(int(r[1]), max_v, 8)
        lines.append(f"`{r[0]}` {bar} `{int(r[1]):,}`")
    return "\n".join(lines)


def _fmt_ctr(d: dict) -> str:
    rows = d.get("ctr_data", [])
    if not rows:
        return "🎯 No CTR data."
    avg_ctr = sum(float(r[2]) for r in rows if len(r) > 2) / len(rows) * 100
    grade = "🟢 Great" if avg_ctr > 5 else "🟡 Average" if avg_ctr > 3 else "🔴 Needs Work"
    lines = [
        "🎯 *CTR Analysis — Last 28 Days*", "━━━━━━━━━━━━━━━━━━━━",
        f"📊 Avg CTR: `{avg_ctr:.2f}%` — {grade}", "",
        "📅 *Daily CTR:*"
    ]
    for r in rows[-7:]:
        ctr = float(r[2]) * 100 if len(r) > 2 else 0
        bar = _bar(ctr, 10, 8)
        lines.append(f"`{r[0]}` {bar} `{ctr:.1f}%`")
    return "\n".join(lines)


def _fmt_seo(d: dict) -> str:
    lines = ["🔍 *SEO Audit*", "━━━━━━━━━━━━━━━━━━━━"]
    for v in d.get("seo_data", [])[:5]:
        t = "✅" if 40 <= v["title_length"] <= 70 else "⚠️"
        desc = "✅" if v["description_length"] > 200 else "⚠️"
        tags = "✅" if v["tag_count"] >= 10 else "⚠️"
        score = [t, desc, tags].count("✅")
        stars = "⭐" * score + "☆" * (3 - score)
        lines.append(
            f"\n{stars} _{v['title'][:50]}_\n"
            f"  {t} Title `{v['title_length']}ch` "
            f"{desc} Desc `{v['description_length']}ch` "
            f"{tags} Tags `{v['tag_count']}`"
        )
    return "\n".join(lines)


def _fmt_retention(d: dict) -> str:
    rows = d.get("retention_data", [])
    if not rows:
        return "📉 No retention data."
    lines = ["📉 *Audience Retention*", "━━━━━━━━━━━━━━━━━━━━"]
    max_pct = max((float(r[2]) for r in rows if len(r) > 2), default=1)
    for r in rows[:8]:
        pct = float(r[2]) if len(r) > 2 else 0
        bar = _bar(pct, max_pct, 8)
        emoji = "🟢" if pct > 40 else "🟡" if pct > 25 else "🔴"
        lines.append(f"{emoji} `{r[0][:15]}` {bar} `{pct:.1f}%`")
    return "\n".join(lines)


# ── Commands ───────────────────────────────────────────────────────────────────
@admin_only
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    await update.message.reply_text(
        f"👋 *Namaste {name}\\!*\n\n"
        f"🤖 *HisuClaw v2\\.0* — AI YouTube Manager\n"
        f"Hindi Manhwa/Manga Recap Channel 🎌\n\n"
        f"⚡ Fast analytics, smart suggestions,\n"
        f"🔒 Safe updates with your approval\\.\n\n"
        f"Use the menu below or ask me anything\\!",
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=MAIN_MENU,
    )


@admin_only
async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Analytics", callback_data="menu:analytics"),
         InlineKeyboardButton("✏️ Updates", callback_data="menu:updates")],
        [InlineKeyboardButton("🤖 AI Features", callback_data="menu:ai"),
         InlineKeyboardButton("❓ About", callback_data="menu:about")],
    ])
    await update.message.reply_text(
        "📋 *HisuClaw Help Menu*\n━━━━━━━━━━━━━━━━━━━━\nChoose a category:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard,
    )


@admin_only
async def cmd_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await typing(update)
    result = await TOOLS["AnalyzeChannel"].execute()
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("📈 Growth", callback_data="quick:growth"),
        InlineKeyboardButton("🎯 CTR", callback_data="quick:ctr"),
        InlineKeyboardButton("🔍 SEO", callback_data="quick:seo"),
    ]])
    await _send(update, _fmt_channel(result), reply_markup=keyboard)


@admin_only
async def cmd_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await typing(update)
    result = await TOOLS["AnalyzeVideos"].execute(max_results=10)
    videos = result.get("videos", [])
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🎬 {v['title'][:30]}...", callback_data=f"video:{v['id']}")]
        for v in videos[:5]
    ])
    await _send(update, _fmt_videos(result), reply_markup=keyboard)


@admin_only
async def cmd_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await _send(update, "Usage: /video `<video_id>`")
        return
    await typing(update)
    r = await TOOLS["AnalyzeVideo"].execute(video_id=context.args[0])
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✏️ Update Title", callback_data=f"suggest_title:{r['id']}"),
        InlineKeyboardButton("🏷 Update Tags", callback_data=f"suggest_tags:{r['id']}"),
    ]])
    text = (
        f"🎬 *{r.get('title', 'N/A')}*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👁 Views:    `{int(r.get('views',0)):,}`\n"
        f"👍 Likes:    `{int(r.get('likes',0)):,}`\n"
        f"💬 Comments: `{int(r.get('comments',0)):,}`\n"
        f"🏷 Tags:     `{len(r.get('tags',[]))}`\n"
        f"📝 Desc:     `{len(r.get('description',''))}` chars\n\n"
        f"||_Full analytics in YouTube Studio_||"
    )
    await _send(update, text, reply_markup=keyboard)


@admin_only
async def cmd_growth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await typing(update)
    result = await TOOLS["AnalyzeGrowth"].execute()
    await _send(update, _fmt_growth(result))


@admin_only
async def cmd_retention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await typing(update)
    video_id = context.args[0] if context.args else None
    result = await TOOLS["AnalyzeRetention"].execute(video_id=video_id)
    await _send(update, _fmt_retention(result))


@admin_only
async def cmd_ctr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await typing(update)
    result = await TOOLS["AnalyzeCTR"].execute()
    await _send(update, _fmt_ctr(result))


@admin_only
async def cmd_seo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await typing(update)
    result = await TOOLS["AnalyzeSEO"].execute()
    await _send(update, _fmt_seo(result))


@admin_only
async def cmd_competitors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await _send(update, "Usage: /competitors `<channel_id1>` `[id2...]`")
        return
    await typing(update)
    result = await TOOLS["AnalyzeCompetitors"].execute(channel_ids=context.args)
    lines = ["🕵️ *Competitor Intelligence*", "━━━━━━━━━━━━━━━━━━━━"]
    for c in result.get("competitors", []):
        lines.append(
            f"\n📺 *{c['channel_title']}*\n"
            f"  👥 `{int(c.get('subscribers') or 0):,}` subs | "
            f"👁 `{int(c.get('total_views') or 0):,}` views\n"
            f"  🎬 Recent: `{len(c.get('recent_videos', []))}` videos"
        )
        for v in c.get("recent_videos", [])[:3]:
            lines.append(f"    • _{v['title'][:50]}_ — `{v['views']:,}` views")
    await _send(update, "\n".join(lines))


@admin_only
async def cmd_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⏳ *Generating report\\.\\.\\.*\n`Analyzing videos → Growth → AI insights`", parse_mode=ParseMode.MARKDOWN_V2)
    report = await generate_report()
    await msg.delete()
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔄 Refresh", callback_data="quick:report"),
        InlineKeyboardButton("📤 Share", switch_inline_query=report[:200]),
    ]])
    await _send(update, f"📊 *Channel Report*\n━━━━━━━━━━━━━━━━━━━━\n{report}", reply_markup=keyboard)


@admin_only
async def cmd_strategy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await typing(update)
    result = await TOOLS["GenerateContentStrategy"].execute()
    await _send(update, f"🗓 *Content Strategy*\n━━━━━━━━━━━━━━━━━━━━\n{result.get('raw', 'N/A')}")


@admin_only
async def cmd_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await _send(update, "Usage: /title `<video_id>` `<new title>`")
        return
    video_id, new_title = context.args[0], " ".join(context.args[1:])
    token = str(uuid.uuid4())
    add_pending(token, {"video_id": video_id, "field": "title", "new_value": new_title})
    await _confirm_msg(update, token, "title", video_id, new_title)


@admin_only
async def cmd_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await _send(update, "Usage: /description `<video_id>` `<text>`")
        return
    video_id, new_desc = context.args[0], " ".join(context.args[1:])
    token = str(uuid.uuid4())
    add_pending(token, {"video_id": video_id, "field": "description", "new_value": new_desc})
    await _confirm_msg(update, token, "description", video_id, new_desc)


@admin_only
async def cmd_tags(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await _send(update, "Usage: /tags `<video_id>` `<tag1,tag2,...>`")
        return
    video_id, tags = context.args[0], context.args[1].split(",")
    token = str(uuid.uuid4())
    add_pending(token, {"video_id": video_id, "field": "tags", "new_value": tags})
    await _confirm_msg(update, token, "tags", video_id, ", ".join(tags))


async def _confirm_msg(update: Update, token: str, field: str, video_id: str, value: str):
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ CONFIRM UPDATE", callback_data=f"confirm:{token}"),
        InlineKeyboardButton("❌ DECLINE", callback_data=f"decline:{token}"),
    ]])
    icons = {"title": "📝", "description": "📄", "tags": "🏷"}
    await update.message.reply_text(
        f"⚠️ *{field.title()} Update Request*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎬 Video: `{video_id}`\n"
        f"{icons.get(field,'📝')} New {field}:\n"
        f"```\n{str(value)[:400]}\n```\n"
        f"⚡ _This will update YouTube directly._",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard,
    )


# ── Callback Handler ───────────────────────────────────────────────────────────
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != TELEGRAM_ADMIN_ID:
        await query.answer("🚫 Access Denied.", show_alert=True)
        return
    await query.answer()
    data = query.data

    # Help menu
    if data.startswith("menu:"):
        section = data.split(":")[1]
        help_texts = {
            "analytics": "📊 *Analytics Commands*\n/channel /videos /video /growth /retention /ctr /seo /competitors",
            "updates":   "✏️ *Update Commands*\n/title /description /tags\n\n_All require your confirmation._",
            "ai":        "🤖 *AI Features*\n/report /strategy\n\nOr just type any question — AI answers using your channel data.",
            "about":     "ℹ️ *HisuClaw v2.0*\nAI YouTube Manager for Hindi Manhwa channels.\nGroq LLM • YouTube API • Telegram Bot",
        }
        await query.edit_message_text(help_texts.get(section, ""), parse_mode=ParseMode.MARKDOWN)
        return

    # Quick action buttons
    if data.startswith("quick:"):
        cmd = data.split(":")[1]
        fake_update = update
        handlers = {
            "growth": lambda: TOOLS["AnalyzeGrowth"].execute(),
            "ctr": lambda: TOOLS["AnalyzeCTR"].execute(),
            "seo": lambda: TOOLS["AnalyzeSEO"].execute(),
            "report": generate_report,
        }
        if cmd in handlers:
            result = await handlers[cmd]()
            formatters = {"growth": _fmt_growth, "ctr": _fmt_ctr, "seo": _fmt_seo}
            text = formatters[cmd](result) if cmd in formatters else str(result)
            try:
                await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
            except Exception:
                await query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        return

    # Video quick view
    if data.startswith("video:"):
        video_id = data.split(":")[1]
        r = await TOOLS["AnalyzeVideo"].execute(video_id=video_id)
        text = (
            f"🎬 *{r.get('title','N/A')}*\n"
            f"👁 `{int(r.get('views',0)):,}` views | 👍 `{int(r.get('likes',0)):,}` likes\n"
            f"🏷 `{len(r.get('tags',[]))}` tags | 📝 `{len(r.get('description',''))}` chars desc"
        )
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
        return

    # Suggest title/tags
    if data.startswith("suggest_title:") or data.startswith("suggest_tags:"):
        action, video_id = data.split(":", 1)
        await query.edit_message_text("⏳ Generating AI suggestion...")
        if "title" in action:
            r = await TOOLS["GenerateTitles"].execute(topic=video_id)
        else:
            r = await TOOLS["GenerateTags"].execute(title=video_id, topic="manhwa recap")
        await query.edit_message_text(f"💡 *AI Suggestion*\n```\n{r.get('raw','')[:800]}\n```", parse_mode=ParseMode.MARKDOWN)
        return

    # Confirm/Decline write
    if data.startswith("confirm:") or data.startswith("decline:"):
        action, token = data.split(":", 1)
        pending = pop_pending(token)
        if not pending:
            await query.edit_message_text("⚠️ Request expired.")
            return
        if action == "decline":
            await query.edit_message_text("❌ *Declined.* No changes made.", parse_mode=ParseMode.MARKDOWN)
            return
        field, video_id, new_value = pending["field"], pending["video_id"], pending["new_value"]
        tool_map = {"title": "UpdateTitle", "description": "UpdateDescription", "tags": "UpdateTags"}
        kwargs = {"video_id": video_id, "confirmed": True,
                  f"new_{field}": new_value}
        try:
            await TOOLS[tool_map[field]].execute(**kwargs)
            await query.edit_message_text(f"✅ *{field.title()} updated on YouTube!*\n`{video_id}`", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await query.edit_message_text(f"❌ Error: `{e}`", parse_mode=ParseMode.MARKDOWN)


# ── Message Handler ────────────────────────────────────────────────────────────
@admin_only
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # Reply keyboard shortcuts
    if text in MENU_MAP:
        cmd = MENU_MAP[text]
        handlers_map = {
            "channel": cmd_channel, "videos": cmd_videos, "growth": cmd_growth,
            "retention": cmd_retention, "ctr": cmd_ctr, "seo": cmd_seo,
            "report": cmd_report, "strategy": cmd_strategy,
        }
        if cmd in handlers_map:
            await handlers_map[cmd](update, context)
        return

    # AI agent for free text
    await typing(update)
    response = await run_agent(text)
    await _send(update, response, reply_markup=MAIN_MENU)


# ── Build App ──────────────────────────────────────────────────────────────────
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
