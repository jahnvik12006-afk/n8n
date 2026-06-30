from ui.theme import box_top, box_bot, box_split, kv_line, kv_emoji, tag_bold, tag_code, SYMBOLS


def error_card(error_msg: str) -> str:
    lines = [
        box_top(36),
        "❌ " + tag_bold("Error"),
        "",
        f"{SYMBOLS['line_v']} {tag_code(error_msg[:200])}",
        box_bot(36),
    ]
    return "\n".join(lines)


def admin_panel() -> str:
    lines = [
        box_top(36),
        tag_bold("⚙ Admin Panel"),
        "",
        kv_emoji("📊", "/stats", "Bot statistics"),
        kv_emoji("📋", "/jobs", "View job queue"),
        kv_emoji("💾", "/cache", "Cache management"),
        kv_emoji("📜", "/logs", "Recent logs"),
        kv_emoji("📢", "/setmain", "Set main channel"),
        kv_emoji("➕", "/addsub", "Add sub-channel"),
        kv_emoji("➖", "/removesub", "Remove sub-channel"),
        kv_emoji("📋", "/listsub", "List channels"),
        kv_emoji("📨", "/broadcast", "Broadcast message"),
        kv_emoji("🚫", "/cancel", "Cancel a job"),
        kv_emoji("🔄", "/reload", "Reload config"),
        box_bot(36),
    ]
    return "\n".join(lines)


def channel_list(channels: list[dict]) -> str:
    lines = [
        box_top(36),
        tag_bold("📢 Configured Channels"),
        "",
    ]
    for ch in channels:
        name = ch.get("name", "?")
        cid = ch.get("channel_id", "")
        lines.append(kv_line(name, cid))
    lines.append(box_bot(36))
    return "\n".join(lines)
