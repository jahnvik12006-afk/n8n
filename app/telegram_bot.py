"""Telegram bot — admin-only, animepahe-style HTML UI."""
import os
import re
import uuid
import json
import logging
import asyncio
import tempfile
import httpx
from pathlib import Path
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
            f"\n{i}. <code>{t['title']}</code>\n"
            f"   {bar} {t['score']}/100"
        )
    lines.append(f"\n<i>Tap any title to copy</i>")
    return "\n".join(lines)


async def typing(update: Update):
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
        tc = v.get("tag_count", 0)
        dl = v.get("desc_len", 0)
        tag_flag = "✓" if tc >= 10 else "!"
        desc_flag = "✓" if dl >= 200 else "!"
        rows.append(
            f"{i:>2}. {bar} {v['views']:,}\n"
            f"    <i>{v['title'][:50]}</i>\n"
            f"    ᴛᴀɢs:{tc}[{tag_flag}] ᴅᴇsᴄ:{dl}ᴄ[{desc_flag}]"
        )
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
            f"<code>{v['title'][:60]}</code>\n"
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
            tip = f"\n   → {w['tip']}" if w.get("tip") else ""
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

    if data.startswith("dl:"):
        _, token, idx, kind = data.split(":")
        await _do_download(query, token, int(idx), kind)
        return

    if data.startswith("menu:"):
        texts = {
            "analytics": _box("ᴀɴᴀʟʏᴛɪᴄs", ["/channel /videos /video /growth /retention /ctr /seo /competitors"]),
            "updates":   _box("ᴜᴘᴅᴀᴛᴇs", ["/title /description /tags", "ʀᴇǫᴜɪʀᴇ ᴄᴏɴꜰɪʀᴍᴀᴛɪᴏɴ"]),
            "ai":        _box("ᴀɪ ᴛᴏᴏʟs", [
                "/hook <topic> — ᴠɪʀᴀʟ ᴏᴘᴇɴɪɴɢ ʜᴏᴏᴋs",
                "/thumbnail <topic> — ᴛʜᴜᴍʙɴᴀɪʟ ᴛᴇxᴛ",
                "/abtitle A | B — ᴄᴏᴍᴘᴀʀᴇ ᴛɪᴛʟᴇs",
                "/shorts <topic> — sʜᴏʀᴛs ɪᴅᴇᴀs",
                "/brief — ᴅᴀɪʟʏ ᴀᴄᴛɪᴏɴ ᴘʟᴀɴ",
                "/spy <@handle> — ᴄᴏᴍᴘᴇᴛɪᴛᴏʀ ᴀɴᴀʟʏsɪs",
                "/strategy /report — ᴄᴏɴᴛᴇɴᴛ ᴘʟᴀɴ",
            ]),
            "about":     _box("ʜɪsᴜᴄʟᴀᴡ ᴠ2.0", ["ɢʀᴏǫ ʟʟᴍ + ʏᴏᴜᴛᴜʙᴇ ᴀᴘɪ + ᴛᴇʟᴇɢʀᴀᴍ", "ʏᴏᴜᴛᴜʙᴇ ᴄʜᴀɴɴᴇʟ ᴍᴀɴᴀɢᴇʀ"]),
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


_YT_RE = re.compile(r'(https?://(?:www\.)?(?:youtube\.com/watch\S+|youtu\.be/\S+|twitter\.com/\S+|x\.com/\S+))', re.I)


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
    # Auto-detect YouTube/Twitter URL and trigger download flow
    m = _YT_RE.search(text)
    if m:
        context.args = [m.group(1)]
        await cmd_download(update, context)
        return
    await typing(update)
    response = await run_agent(text)
    await _send(update, response, reply_markup=MAIN_MENU)


# ── Extra tool commands ────────────────────────────────────────────────────

@admin_only
async def cmd_hook(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topic = " ".join(context.args)
    if not topic:
        await _send(update, "Usage: /hook <topic>"); return
    await typing(update)
    ch = await TOOLS["AnalyzeChannel"].execute()
    r = await TOOLS["GenerateViralHook"].execute(topic=topic, channel_title=ch.get("title", ""))
    hooks = r.get("hooks", [])
    lines = [f"<b><blockquote>✦ ᴠɪʀᴀʟ ʜᴏᴏᴋs ✦</blockquote>\n{DIV}</b>"]
    for i, h in enumerate(hooks, 1):
        lines.append(f"\n<b>{i}. [{h.get('style','').upper()}]</b>\n<code>{h.get('hook','')}</code>\n<i>→ {h.get('why','')}</i>")
    await _send(update, "\n".join(lines))


@admin_only
async def cmd_thumbnail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topic = " ".join(context.args)
    if not topic:
        await _send(update, "Usage: /thumbnail <topic>"); return
    await typing(update)
    ch = await TOOLS["AnalyzeChannel"].execute()
    r = await TOOLS["GenerateThumbnailText"].execute(topic=topic, channel_title=ch.get("title", ""))
    opts = r.get("options", [])
    lines = [f"<b><blockquote>✦ ᴛʜᴜᴍʙɴᴀɪʟ ᴛᴇxᴛ ✦</blockquote>\n{DIV}</b>"]
    for i, o in enumerate(opts, 1):
        lines.append(f"\n{i}. <code>{o.get('text','')}</code>\n   <i>{o.get('psychology','')} — {o.get('ctr_reason','')}</i>")
    lines.append(f"\n<i>Tap text to copy</i>")
    await _send(update, "\n".join(lines))


@admin_only
async def cmd_abtitle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await _send(update, 'Usage: /abtitle "Title A" "Title B"'); return
    await typing(update)
    full = " ".join(context.args)
    parts = full.split("|", 1)
    if len(parts) < 2:
        await _send(update, 'Split titles with | — /abtitle Title A | Title B'); return
    ch = await TOOLS["AnalyzeChannel"].execute()
    r = await TOOLS["CompareTitles"].execute(
        title_a=parts[0].strip(), title_b=parts[1].strip(),
        channel_title=ch.get("title", ""), channel_description=ch.get("description", ""),
    )
    winner = r.get("winner", "?")
    lines = [
        f"<b><blockquote>✦ ᴛɪᴛʟᴇ A/B ᴛᴇsᴛ ✦</blockquote>\n{DIV}</b>",
        f"\n<b>A:</b> <code>{parts[0].strip()}</code>  {_bar(r.get('score_a',0),100,8)} {r.get('score_a',0)}/100",
        f"<b>B:</b> <code>{parts[1].strip()}</code>  {_bar(r.get('score_b',0),100,8)} {r.get('score_b',0)}/100",
        f"\n<b>ᴡɪɴɴᴇʀ: {winner}</b>",
        f"\n<b>ʙᴇsᴛ ᴠᴇʀsɪᴏɴ:</b>\n<code>{r.get('improved','')}</code>",
    ]
    await _send(update, "\n".join(lines))


@admin_only
async def cmd_shorts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topic = " ".join(context.args)
    if not topic:
        await _send(update, "Usage: /shorts <topic>"); return
    await typing(update)
    ch = await TOOLS["AnalyzeChannel"].execute()
    r = await TOOLS["GenerateShortsIdeas"].execute(topic=topic, channel_title=ch.get("title", ""))
    shorts = r.get("shorts", [])
    lines = [f"<b><blockquote>✦ sʜᴏʀᴛs ɪᴅᴇᴀs ✦</blockquote>\n{DIV}</b>"]
    for i, s in enumerate(shorts, 1):
        tags = " ".join(f"#{t}" for t in s.get("hashtags", [])[:3])
        lines.append(
            f"\n{i}. <code>{s.get('title','')}</code>\n"
            f"   <b>Hook:</b> {s.get('hook','')}\n"
            f"   {s.get('outline','')}\n"
            f"   <i>{tags}</i>"
        )
    await _send(update, "\n".join(lines))


@admin_only
async def cmd_brief(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await typing(update)
    ch = await TOOLS["AnalyzeChannel"].execute()
    r = await TOOLS["GenerateDailyBrief"].execute(
        channel_title=ch.get("title", ""),
        channel_description=ch.get("description", ""),
        subscribers=ch.get("subscribers", 0),
        recent_views=ch.get("total_views", 0),
    )
    await _send(update, _box("ᴅᴀɪʟʏ ʙʀɪᴇꜰ", [
        f"↑ ᴜᴘʟᴏᴀᴅ ᴛɪᴍᴇ: {r.get('upload_time','')}",
        f"✦ ɪᴅᴇᴀ: {r.get('content_idea','')}",
        f"▶ sᴇᴏ: {r.get('seo_tip','')}",
        f"· ᴇɴɢᴀɢᴇ: {r.get('engagement_tip','')}",
        f"— {r.get('motivation','')}",
    ]))


@admin_only
async def cmd_spy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = " ".join(context.args)
    if not url:
        await _send(update, "Usage: /spy <channel_url or @handle>"); return
    await typing(update)
    r = await TOOLS["SpyCompetitor"].execute(channel_url=url)
    if "error" in r:
        await _send(update, _box("ᴇʀʀᴏʀ", [r["error"]])); return
    top = r.get("top_videos", [])[:3]
    top_lines = [f"・ <code>{v['title'][:50]}</code> — {v['views']:,} ᴠɪᴇᴡs" for v in top]
    patterns = [f"・ {p}" for p in r.get("winning_patterns", [])]
    steal = [f"・ {s}" for s in r.get("steal_ideas", [])]
    lines = [
        f"<b><blockquote>✦ sᴘʏ: {r.get('channel_name','')} ✦</blockquote>\n{DIV}</b>",
        f"<blockquote>sᴜʙs: {r.get('subscribers',0):,}  ᴠɪᴇᴡs: {r.get('total_views',0):,}</blockquote>",
        f"\n<b>ᴛᴏᴘ ᴠɪᴅᴇᴏs:</b>\n" + "\n".join(top_lines),
        f"\n<b>ᴡɪɴɴɪɴɢ ᴘᴀᴛᴛᴇʀɴs:</b>\n" + "\n".join(patterns),
        f"\n<b>sᴛᴇᴀʟ ɪᴅᴇᴀs:</b>\n" + "\n".join(steal),
    ]
    await _send(update, "\n".join(lines))


# { token: {formats, thumbnail, title} }
_dl_pending: dict = {}


@admin_only
async def cmd_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await _send(update, _box("ᴅᴏᴡɴʟᴏᴀᴅ", ["Usage: /download <YouTube URL>"]))
        return
    url = context.args[0]
    msg = await update.message.reply_text(
        f"<b><blockquote>◌ ꜰᴇᴛᴄʜɪɴɢ ꜰᴏʀᴍᴀᴛs...</blockquote></b>", parse_mode=ParseMode.HTML
    )
    try:
        data = await TOOLS["FetchDownloadFormats"].execute(url=url)
    except Exception as e:
        await msg.edit_text(f"<b><blockquote>ᴇʀʀᴏʀ: {e}</blockquote></b>", parse_mode=ParseMode.HTML)
        return

    formats = [f for f in data.get("formats", []) if f.get("content_type") in ("mp4", "m4a", "opus")]
    if not formats:
        await msg.edit_text("<b><blockquote>ɴᴏ ꜰᴏʀᴍᴀᴛs ꜰᴏᴜɴᴅ.</blockquote></b>", parse_mode=ParseMode.HTML)
        return

    token = str(uuid.uuid4())[:8]
    _dl_pending[token] = {"formats": formats, "thumbnail": data.get("thumbnail"), "orig_url": url}

    # Build quality keyboard — video formats first, then audio
    video_fmts = [f for f in formats if not f["is_audio"]]
    audio_fmts = [f for f in formats if f["is_audio"]]

    rows = []
    for i, f in enumerate(video_fmts[:4]):
        rows.append([InlineKeyboardButton(f"▶ {f['quality']}", callback_data=f"dl:{token}:{i}:v")])
    for i, f in enumerate(audio_fmts[:2]):
        rows.append([InlineKeyboardButton(f"♪ {f['quality']}", callback_data=f"dl:{token}:{i}:a")])

    keyboard = InlineKeyboardMarkup(rows)
    thumb = data.get("thumbnail", "")
    info_text = _box("ᴅᴏᴡɴʟᴏᴀᴅ", [
        f"ᴜʀʟ: <code>{url[:60]}</code>",
        "sᴇʟᴇᴄᴛ ǫᴜᴀʟɪᴛʏ ʙᴇʟᴏᴡ ↓",
    ])
    await msg.delete()
    if thumb:
        await update.message.reply_photo(photo=thumb, caption=info_text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    else:
        await update.message.reply_text(info_text, parse_mode=ParseMode.HTML, reply_markup=keyboard)


async def _do_download(query, token: str, fmt_idx: int, kind: str):
    pending = _dl_pending.get(token)
    if not pending:
        await query.edit_message_text("<b><blockquote>ᴇxᴘɪʀᴇᴅ. ꜰᴇᴛᴄʜ ᴀɢᴀɪɴ.</blockquote></b>", parse_mode=ParseMode.HTML)
        return

    video_fmts = [f for f in pending["formats"] if not f["is_audio"]]
    audio_fmts = [f for f in pending["formats"] if f["is_audio"]]
    fmt = (video_fmts if kind == "v" else audio_fmts)[fmt_idx]

    await query.edit_message_caption(
        caption=f"<b><blockquote>↓ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ <code>{fmt['quality']}</code>...\nᴘʟᴇᴀsᴇ ᴡᴀɪᴛ </blockquote></b>",
        parse_mode=ParseMode.HTML,
    ) if query.message.photo else await query.edit_message_text(
        f"<b><blockquote>↓ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ <code>{fmt['quality']}</code>...\nᴘʟᴇᴀsᴇ ᴡᴀɪᴛ </blockquote></b>",
        parse_mode=ParseMode.HTML,
    )

    ext = fmt["content_type"]
    tmp_path = Path(tempfile.gettempdir()) / f"hisuclaw_{token}.{ext}"

    try:
        async with httpx.AsyncClient(timeout=120, follow_redirects=True) as c:
            async with c.stream("GET", fmt["url"]) as r:
                r.raise_for_status()
                with open(tmp_path, "wb") as f:
                    async for chunk in r.aiter_bytes(65536):
                        f.write(chunk)

        caption = (
            f"<b><blockquote>✦ ᴅᴏᴡɴʟᴏᴀᴅ ᴄᴏᴍᴘʟᴇᴛᴇ ✦</blockquote>\n{DIV}\n"
            f"<blockquote>・ ǫᴜᴀʟɪᴛʏ: {fmt['quality']}\n"
            f"・ ꜰᴏʀᴍᴀᴛ: {ext.upper()}\n"
            f"! <i>ᴛʜɪs ꜰɪʟᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ 5 ᴍɪɴs</i></blockquote>\n{DIV}</b>"
        )

        chat_id = query.message.chat_id
        with open(tmp_path, "rb") as f:
            if kind == "v":
                sent = await query.get_bot().send_video(chat_id=chat_id, video=f, caption=caption, parse_mode=ParseMode.HTML)
            else:
                sent = await query.get_bot().send_audio(chat_id=chat_id, audio=f, caption=caption, parse_mode=ParseMode.HTML)

        # Schedule delete of message + temp file after 5 mins
        async def _cleanup():
            await asyncio.sleep(300)
            try:
                await sent.delete()
            except Exception:
                pass
            tmp_path.unlink(missing_ok=True)
            _dl_pending.pop(token, None)

        asyncio.create_task(_cleanup())

        # Delete the "downloading" status message
        try:
            await query.message.delete()
        except Exception:
            pass

    except Exception as e:
        tmp_path.unlink(missing_ok=True)
        await query.get_bot().send_message(
            chat_id=query.message.chat_id,
            text=f"<b><blockquote>ᴇʀʀᴏʀ: <code>{e}</code></blockquote></b>",
            parse_mode=ParseMode.HTML,
        )


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
    app.add_handler(CommandHandler("download", cmd_download))
    app.add_handler(CommandHandler("hook", cmd_hook))
    app.add_handler(CommandHandler("thumbnail", cmd_thumbnail))
    app.add_handler(CommandHandler("abtitle", cmd_abtitle))
    app.add_handler(CommandHandler("shorts", cmd_shorts))
    app.add_handler(CommandHandler("brief", cmd_brief))
    app.add_handler(CommandHandler("spy", cmd_spy))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    return app
