"""Telegram bot — admin-only, animepahe-style HTML UI."""
import os
import uuid
import json
import logging
import asyncio
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes,
)
from telegram.constants import ParseMode, ChatAction
from app.config import TELEGRAM_BOT_TOKEN, TELEGRAM_ADMIN_ID
from app.agent import run_agent
from app.report_engine import generate_report
from app.tools.write_tools import add_pending, pop_pending
from app.tools.registry import TOOLS

logger = logging.getLogger(__name__)

DIV = "──────────────────"

def _box(title: str, lines: list[str]) -> str:
    body = "\n".join(f"・ {l}" for l in lines)
    return f"<b><blockquote>✦ {title} ✦</blockquote>\n{DIV}\n<blockquote>{body}</blockquote>\n{DIV}</b>"

def _bar(value: float, max_val: float, width: int = 10) -> str:
    filled = int((value / max_val) * width) if max_val > 0 else 0
    return "█" * filled + "░" * (width - filled)

MAIN_MENU = ReplyKeyboardMarkup(
    [
        ["Channel", "Videos", "Growth"],
        ["Retention", "CTR", "SEO"],
        ["Competitors", "Report", "Strategy"],
    ],
    resize_keyboard=True,
    input_field_placeholder="Ask anything or choose a command...",
)

MENU_MAP = {
    "Channel": "channel", "Videos": "videos", "Growth": "growth",
    "Retention": "retention", "CTR": "ctr", "SEO": "seo",
    "Competitors": "competitors", "Report": "report", "Strategy": "strategy",
}


def admin_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != TELEGRAM_ADMIN_ID:
            await update.message.reply_text("Access Denied.")
            return
        return await func(update, context)
    return wrapper


def _fmt_titles(d: dict) -> str:
    titles = d.get("titles", [])
    cur = d.get("current_score")
    lines = [f"<b><blockquote>✦ ᴄᴛʀ-ᴏᴘᴛɪᴍɪᴢᴇᴅ ᴛɪᴛʟᴇs ✦</blockquote>\n{DIV}</b>"]
    if cur:
        lines.append(f"<b><blockquote>ᴄᴜʀʀᴇɴᴛ sᴄᴏʀᴇ: {cur['score']}/100</blockquote></b>")
    for i, t in enumerate(titles, 1):
        bar = _bar(t["score"], 100, 8)
        lines.append(
            f"\n<b>{i}.</b> <i>{t['title']}</i>\n"
            f"   {bar} {t['score']}/100 — {', '.join(t.get('reasons', []))}"
        )
    return "\n".join(lines)
    await update.message.chat.send_action(ChatAction.TYPING)


async def _send(update: Update, text: str, reply_markup=None):
    for i in range(0, len(text), 4000):
        try:
            await update.message.reply_text(
                text[i:i+4000],
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup if i == 0 else None,
            )
        except Exception:
            await update.message.reply_text(text[i:i+4000], reply_markup=reply_markup if i == 0 else None)


def _fmt_channel(d: dict) -> str:
    rows = d.get("analytics_28d") or []
    views_28 = int(rows[0][0]) if rows and rows[0] else 0
    mins_28  = int(rows[0][1]) if rows and len(rows[0]) > 1 else 0
    return _box("ᴄʜᴀɴɴᴇʟ ɪɴꜰᴏ", [
        f"ɴᴀᴍᴇ: <b>{d.get('title', 'N/A')}</b>",
        f"sᴜʙsᴄʀɪʙᴇʀs: {int(d.get('subscribers') or 0):,}",
        f"ᴛᴏᴛᴀʟ ᴠɪᴇᴡs: {int(d.get('total_views') or 0):,}",
        f"ᴠɪᴅᴇᴏs: {d.get('video_count', '?')}",
        f"ᴠɪᴇᴡs (28ᴅ): {views_28:,}",
        f"ᴡᴀᴛᴄʜ ᴛɪᴍᴇ (28ᴅ): {mins_28:,} ᴍɪɴs",
    ])


def _fmt_videos(d: dict) -> str:
    videos = d.get("videos", [])
    if not videos:
        return "<b><blockquote>ɴᴏ ᴠɪᴅᴇᴏs ꜰᴏᴜɴᴅ.</blockquote></b>"
    max_views = videos[0]["views"] if videos else 1
    rows = []
    for i, v in enumerate(videos[:10], 1):
        bar = _bar(v["views"], max_views)
        rows.append(f"{i:>2}. {bar} {v['views']:,}\n    <i>{v['title'][:55]}</i>")
    body = "\n".join(rows)
    return f"<b><blockquote>✦ ᴠɪᴅᴇᴏ ʀᴀɴᴋɪɴɢs ✦</blockquote>\n{DIV}\n<blockquote>{body}</blockquote>\n{DIV}</b>"


def _fmt_growth(d: dict) -> str:
    rows = d.get("growth_data", [])
    if not rows:
        return "<b><blockquote>ɴᴏ ɢʀᴏᴡᴛʜ ᴅᴀᴛᴀ.</blockquote></b>"
    total_v = sum(int(r[1]) for r in rows if len(r) > 1)
    total_s = sum(int(r[2]) for r in rows if len(r) > 2)
    total_l = sum(int(r[3]) for r in rows if len(r) > 3)
    max_v = max((int(r[1]) for r in rows if len(r) > 1), default=1)
    summary = _box("ɢʀᴏᴡᴛʜ — ʟᴀsᴛ 28 ᴅᴀʏs", [
        f"ᴠɪᴇᴡs: {total_v:,}",
        f"sᴜʙs ɢᴀɪɴᴇᴅ: {total_s:,}",
        f"sᴜʙs ʟᴏsᴛ: {total_l:,}",
        f"ɴᴇᴛ: {total_s - total_l:+,}",
    ])
    daily = "\n".join(
        f"・ {r[0]}  {_bar(int(r[1]), max_v, 8)}  {int(r[1]):,}"
        for r in rows[-7:] if len(r) > 1
    )
    return f"{summary}\n<b><blockquote>ᴅᴀɪʟʏ (ʟᴀsᴛ 7ᴅ)\n{daily}</blockquote></b>"


def _fmt_ctr(d: dict) -> str:
    rows = d.get("ctr_data", [])
    if not rows:
        return "<b><blockquote>ɴᴏ ᴅᴀᴛᴀ.</blockquote></b>"
    total_views = sum(int(r[1]) for r in rows if len(r) > 1)
    total_mins = sum(int(r[2]) for r in rows if len(r) > 2)
    max_v = max((int(r[1]) for r in rows if len(r) > 1), default=1)
    summary = _box("ᴠɪᴇᴡs & ᴡᴀᴛᴄʜ ᴛɪᴍᴇ — 28ᴅ", [
        f"ᴛᴏᴛᴀʟ ᴠɪᴇᴡs: {total_views:,}",
        f"ᴡᴀᴛᴄʜ ᴛɪᴍᴇ: {total_mins:,} ᴍɪɴs",
    ])
    daily = "\n".join(
        f"・ {r[0]}  {_bar(int(r[1]), max_v, 8)}  {int(r[1]):,}"
        for r in rows[-7:] if len(r) > 1
    )
    return f"{summary}\n<b><blockquote>ᴅᴀɪʟʏ (ʟᴀsᴛ 7ᴅ)\n{daily}</blockquote></b>"


def _fmt_seo(d: dict) -> str:
    items = []
    for v in d.get("seo_data", [])[:5]:
        t = "OK" if 40 <= v["title_length"] <= 70 else "!"
        desc = "OK" if v["description_length"] > 200 else "!"
        tags = "OK" if v["tag_count"] >= 10 else "!"
        items.append(
            f"<i>{v['title'][:45]}</i>\n"
            f"   ᴛɪᴛʟᴇ {v['title_length']}ᴄʜ [{t}]  ᴅᴇsᴄ {v['description_length']}ᴄʜ [{desc}]  ᴛᴀɢs {v['tag_count']} [{tags}]"
        )
    body = "\n\n".join(items)
    return f"<b><blockquote>✦ sᴇᴏ ᴀᴜᴅɪᴛ ✦</blockquote>\n{DIV}\n<blockquote>{body}</blockquote>\n{DIV}</b>"


def _fmt_retention(d: dict) -> str:
    rows = d.get("retention_data", [])
    if not rows:
        return "<b><blockquote>ɴᴏ ʀᴇᴛᴇɴᴛɪᴏɴ ᴅᴀᴛᴀ.</blockquote></b>"
    # rows: [day, avgViewDuration, avgViewPercentage]
    max_pct = max((float(r[2]) for r in rows if len(r) > 2), default=100)
    avg_dur = sum(float(r[1]) for r in rows if len(r) > 1) / len(rows)
    avg_pct = sum(float(r[2]) for r in rows if len(r) > 2) / len(rows)
    summary = _box("ʀᴇᴛᴇɴᴛɪᴏɴ — ʟᴀsᴛ 28 ᴅᴀʏs", [
        f"ᴀᴠɢ ᴠɪᴇᴡ ᴅᴜʀ: {avg_dur:.0f}s",
        f"ᴀᴠɢ ᴠɪᴇᴡ %: {avg_pct:.1f}%",
    ])
    daily = "\n".join(
        f"・ {r[0]}  {_bar(float(r[2]), max_pct, 10)}  {float(r[2]):.1f}%"
        for r in rows if len(r) > 2
    )
    return f"{summary}\n<b><blockquote>{daily}</blockquote></b>"


@admin_only
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    await _send(update,
        f"<b><blockquote>✦ ʜɪsᴜᴄʟᴀᴡ ᴠ2.0 ✦</blockquote>\n{DIV}\n"
        f"<blockquote>ᴡᴇʟᴄᴏᴍᴇ, {name}!\n"
        f"ᴀɪ ʏᴏᴜᴛᴜʙᴇ ᴍᴀɴᴀɢᴇʀ ꜰᴏʀ ʜɪɴᴅɪ ᴍᴀɴʜᴡᴀ ᴄʜᴀɴɴᴇʟ.\n"
        f"ᴜsᴇ ᴍᴇɴᴜ ʙᴇʟᴏᴡ ᴏʀ ᴊᴜsᴛ ᴛʏᴘᴇ ʏᴏᴜʀ ǫᴜᴇsᴛɪᴏɴ.</blockquote>\n{DIV}</b>",
        reply_markup=MAIN_MENU,
    )


@admin_only
async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Analytics", callback_data="menu:analytics"),
         InlineKeyboardButton("Updates", callback_data="menu:updates")],
        [InlineKeyboardButton("AI Features", callback_data="menu:ai"),
         InlineKeyboardButton("About", callback_data="menu:about")],
    ])
    await _send(update, f"<b><blockquote>ʜᴇʟᴘ ᴍᴇɴᴜ — ᴄʜᴏᴏsᴇ ᴀ ᴄᴀᴛᴇɢᴏʀʏ</blockquote></b>", reply_markup=keyboard)


@admin_only
async def cmd_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await typing(update)
    result = await TOOLS["AnalyzeChannel"].execute()
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("Growth", callback_data="quick:growth"),
        InlineKeyboardButton("CTR", callback_data="quick:ctr"),
        InlineKeyboardButton("SEO", callback_data="quick:seo"),
    ]])
    await _send(update, _fmt_channel(result), reply_markup=keyboard)


@admin_only
async def cmd_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await typing(update)
    result = await TOOLS["AnalyzeVideos"].execute(max_results=10)
    videos = result.get("videos", [])
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(v['title'][:35], callback_data=f"video:{v['id']}")]
        for v in videos[:5]
    ])
    await _send(update, _fmt_videos(result), reply_markup=keyboard)


@admin_only
async def cmd_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await _send(update, "Usage: `/video <video_id>`")
        return
    await typing(update)
    r = await TOOLS["AnalyzeVideo"].execute(video_id=context.args[0])
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("Suggest Title", callback_data=f"suggest_title:{r['id']}"),
        InlineKeyboardButton("Suggest Tags", callback_data=f"suggest_tags:{r['id']}"),
    ]])
    text = _box("ᴠɪᴅᴇᴏ ᴅᴇᴛᴀɪʟs", [
        f"ᴛɪᴛʟᴇ: <i>{r.get('title', 'N/A')[:60]}</i>",
        f"ᴠɪᴇᴡs: {int(r.get('views',0)):,}",
        f"ʟɪᴋᴇs: {int(r.get('likes',0)):,}",
        f"ᴄᴏᴍᴍᴇɴᴛs: {int(r.get('comments',0)):,}",
        f"ᴛᴀɢs: {len(r.get('tags',[]))}",
        f"ᴅᴇsᴄ: {len(r.get('description',''))} ᴄʜᴀʀs",
        f"ᴘᴜʙʟɪsʜᴇᴅ: {r.get('published_at','')[:10]}",
    ])
    await _send(update, text, reply_markup=keyboard)


@admin_only
async def cmd_growth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await typing(update)
    await _send(update, _fmt_growth(await TOOLS["AnalyzeGrowth"].execute()))


@admin_only
async def cmd_retention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await typing(update)
    video_id = context.args[0] if context.args else None
    await _send(update, _fmt_retention(await TOOLS["AnalyzeRetention"].execute(video_id=video_id)))


@admin_only
async def cmd_ctr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await typing(update)
    await _send(update, _fmt_ctr(await TOOLS["AnalyzeCTR"].execute()))


@admin_only
async def cmd_seo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await typing(update)
    await _send(update, _fmt_seo(await TOOLS["AnalyzeSEO"].execute()))


@admin_only
async def cmd_competitors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await _send(update, "Usage: `/competitors <channel_id1> [id2...]`")
        return
    await typing(update)
    result = await TOOLS["AnalyzeCompetitors"].execute(channel_ids=context.args)
    lines = [f"<b><blockquote>✦ ᴄᴏᴍᴘᴇᴛɪᴛᴏʀ ᴀɴᴀʟʏsɪs ✦</blockquote>\n{DIV}</b>"]
    for c in result.get("competitors", []):
        lines.append(
            f"\n<b><blockquote>{c['channel_title']}</blockquote></b>\n"
            f"<blockquote>・ sᴜʙs: {int(c.get('subscribers') or 0):,}  ᴠɪᴇᴡs: {int(c.get('total_views') or 0):,}</blockquote>"
        )
        for v in c.get("recent_videos", [])[:3]:
            lines.append(f"   <i>{v['title'][:50]}</i> — {v['views']:,} ᴠɪᴇᴡs")
    await _send(update, "\n".join(lines))


@admin_only
async def cmd_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("Generating report...")
    report = await generate_report()
    await msg.delete()
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Refresh", callback_data="quick:report")]])
    await _send(update, _box("ʀᴇᴘᴏʀᴛ", [report[:3000]]), reply_markup=keyboard)


@admin_only
async def cmd_strategy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await typing(update)
    # Fetch real channel info so LLM knows the actual niche
    ch = await TOOLS["AnalyzeChannel"].execute()
    result = await TOOLS["GenerateContentStrategy"].execute(
        channel_title=ch.get("title", ""),
        channel_description=ch.get("description", ""),
    )
    try:
        parsed = result if isinstance(result, dict) and "weekly" in result else json.loads(result.get("raw", "{}"))
        weekly = parsed.get("weekly", [])
        lines = [f"<b><blockquote>✦ ᴄᴏɴᴛᴇɴᴛ sᴛʀᴀᴛᴇɢʏ ✦</blockquote>\n{DIV}</b>"]
        for w in weekly:
            tip = f"\n   💡 {w['tip']}" if w.get("tip") else ""
            lines.append(
                f"\n<b><blockquote>・ {w.get('day','')}</blockquote></b>"
                f"\n<blockquote>{w.get('content','')}{tip}"
                f"\nTags: {', '.join(w.get('tags',[]))}</blockquote>"
            )
        await _send(update, "\n".join(lines))
    except Exception:
        await _send(update, _box("ᴄᴏɴᴛᴇɴᴛ sᴛʀᴀᴛᴇɢʏ", [str(result)[:3000]]))


@admin_only
async def cmd_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await _send(update, "Usage: `/title <video_id> <new title>`")
        return
    video_id, new_title = context.args[0], " ".join(context.args[1:])
    token = str(uuid.uuid4())
    add_pending(token, {"video_id": video_id, "field": "title", "new_value": new_title})
    await _confirm_msg(update, token, "title", video_id, new_title)


@admin_only
async def cmd_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await _send(update, "Usage: `/description <video_id> <text>`")
        return
    video_id, new_desc = context.args[0], " ".join(context.args[1:])
    token = str(uuid.uuid4())
    add_pending(token, {"video_id": video_id, "field": "description", "new_value": new_desc})
    await _confirm_msg(update, token, "description", video_id, new_desc)


@admin_only
async def cmd_tags(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await _send(update, "Usage: `/tags <video_id> <tag1,tag2,...>`")
        return
    video_id, tags = context.args[0], context.args[1].split(",")
    token = str(uuid.uuid4())
    add_pending(token, {"video_id": video_id, "field": "tags", "new_value": tags})
    await _confirm_msg(update, token, "tags", video_id, ", ".join(tags))


async def _confirm_msg(update: Update, token: str, field: str, video_id: str, value: str):
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("Confirm", callback_data=f"confirm:{token}"),
        InlineKeyboardButton("Decline", callback_data=f"decline:{token}"),
    ]])
    await update.message.reply_text(
        _box(f"ᴜᴘᴅᴀᴛᴇ {field.upper()}", [
            f"ᴠɪᴅᴇᴏ: <code>{video_id}</code>",
            f"ɴᴇᴡ {field}: <i>{str(value)[:300]}</i>",
            "ᴛʜɪs ᴡɪʟʟ ᴜᴘᴅᴀᴛᴇ ʏᴏᴜᴛᴜʙᴇ ᴅɪʀᴇᴄᴛʟʏ.",
        ]),
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != TELEGRAM_ADMIN_ID:
        await query.answer("Access Denied.", show_alert=True)
        return
    await query.answer()
    data = query.data

    if data.startswith("menu:"):
        texts = {
            "analytics": _box("ᴀɴᴀʟʏᴛɪᴄs", ["/channel /videos /video /growth /retention /ctr /seo /competitors"]),
            "updates":   _box("ᴜᴘᴅᴀᴛᴇs", ["/title /description /tags", "ʀᴇǫᴜɪʀᴇ ᴄᴏɴꜰɪʀᴍᴀᴛɪᴏɴ"]),
            "ai":        _box("ᴀɪ ꜰᴇᴀᴛᴜʀᴇs", ["/report /strategy", "ᴏʀ ᴊᴜsᴛ ᴛʏᴘᴇ ʏᴏᴜʀ ǫᴜᴇsᴛɪᴏɴ"]),
            "about":     _box("ʜɪsᴜᴄʟᴀᴡ ᴠ2.0", ["ɢʀᴏǫ ʟʟᴍ + ʏᴏᴜᴛᴜʙᴇ ᴀᴘɪ + ᴛᴇʟᴇɢʀᴀᴍ", "ʜɪɴᴅɪ ᴍᴀɴʜᴡᴀ ᴄʜᴀɴɴᴇʟ ᴍᴀɴᴀɢᴇʀ"]),
        }
        await query.edit_message_text(texts.get(data.split(":")[1], ""), parse_mode=ParseMode.HTML)
        return

    if data.startswith("quick:"):
        cmd = data.split(":")[1]
        fns = {"growth": lambda: TOOLS["AnalyzeGrowth"].execute(),
               "ctr": lambda: TOOLS["AnalyzeCTR"].execute(),
               "seo": lambda: TOOLS["AnalyzeSEO"].execute(),
               "report": generate_report}
        fmts = {"growth": _fmt_growth, "ctr": _fmt_ctr, "seo": _fmt_seo}
        if cmd in fns:
            result = await fns[cmd]()
            text = fmts[cmd](result) if cmd in fmts else str(result)
            try:
                await query.edit_message_text(text, parse_mode=ParseMode.HTML)
            except Exception:
                await query.message.reply_text(text, parse_mode=ParseMode.HTML)
        return

    if data.startswith("video:"):
        r = await TOOLS["AnalyzeVideo"].execute(video_id=data.split(":")[1])
        await query.edit_message_text(
            _box("ᴠɪᴅᴇᴏ", [
                f"<i>{r.get('title','N/A')[:50]}</i>",
                f"ᴠɪᴇᴡs: {int(r.get('views',0)):,}  ʟɪᴋᴇs: {int(r.get('likes',0)):,}",
                f"ᴛᴀɢs: {len(r.get('tags',[]))}  ᴅᴇsᴄ: {len(r.get('description',''))} ᴄʜs",
            ]),
            parse_mode=ParseMode.HTML,
        )
        return

    if data.startswith("suggest_title:") or data.startswith("suggest_tags:"):
        action, video_id = data.split(":", 1)
        await query.edit_message_text("<b><blockquote>ɢᴇɴᴇʀᴀᴛɪɴɢ...</blockquote></b>", parse_mode=ParseMode.HTML)
        if "title" in action:
            r = await TOOLS["GenerateTitles"].execute(topic=video_id)
        else:
            r = await TOOLS["GenerateTags"].execute(title=video_id, topic="manhwa recap")
        await query.edit_message_text(
            f"<b><blockquote>✦ ᴀɪ sᴜɢɢᴇsᴛɪᴏɴ ✦</blockquote>\n{DIV}\n<blockquote>{r.get('raw','')[:800]}</blockquote>\n{DIV}</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    if data.startswith("confirm:") or data.startswith("decline:"):
        action, token = data.split(":", 1)
        pending = pop_pending(token)
        if not pending:
            await query.edit_message_text("Request expired.")
            return
        if action == "decline":
            await query.edit_message_text("<b><blockquote>ᴅᴇᴄʟɪɴᴇᴅ. ɴᴏ ᴄʜᴀɴɢᴇs ᴍᴀᴅᴇ.</blockquote></b>", parse_mode=ParseMode.HTML)
            return
        field, video_id, new_value = pending["field"], pending["video_id"], pending["new_value"]
        tool_map = {"title": "UpdateTitle", "description": "UpdateDescription", "tags": "UpdateTags"}
        kwargs = {"video_id": video_id, "confirmed": True, f"new_{field}": new_value}
        try:
            await TOOLS[tool_map[field]].execute(**kwargs)
            await query.edit_message_text(
                _box("ᴜᴘᴅᴀᴛᴇᴅ", [f"{field} ᴜᴘᴅᴀᴛᴇᴅ ✓", f"<code>{video_id}</code>"]),
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            await query.edit_message_text(f"<b><blockquote>ᴇʀʀᴏʀ: <code>{e}</code></blockquote></b>", parse_mode=ParseMode.HTML)


@admin_only
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text in MENU_MAP:
        handlers_map = {
            "channel": cmd_channel, "videos": cmd_videos, "growth": cmd_growth,
            "retention": cmd_retention, "ctr": cmd_ctr, "seo": cmd_seo,
            "report": cmd_report, "strategy": cmd_strategy,
        }
        if MENU_MAP[text] in handlers_map:
            await handlers_map[MENU_MAP[text]](update, context)
        return
    await typing(update)
    response = await run_agent(text)
    await _send(update, response, reply_markup=MAIN_MENU)


def build_application() -> Application:
    builder = Application.builder().token(TELEGRAM_BOT_TOKEN)
    if os.getenv("WEBHOOK_URL") or os.getenv("RENDER_EXTERNAL_URL"):
        builder = builder.updater(None)  # disable updater in webhook mode
    app = builder.build()
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
