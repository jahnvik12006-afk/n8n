from ui.theme import box_top, box_bot, kv_line, tag_bold, tag_code, SYMBOLS


def error_card(error_msg: str) -> str:
    lines = [
        box_top(36),
        tag_bold("Error"),
        "",
        f"{SYMBOLS['line_v']} {tag_code(error_msg[:200])}",
        box_bot(36),
    ]
    return "\n".join(lines)


def admin_panel() -> str:
    lines = [
        box_top(36),
        tag_bold("Admin Panel"),
        "",
        kv_line("/stats", "Bot statistics"),
        kv_line("/jobs", "View job queue"),
        kv_line("/cache", "Cache management"),
        kv_line("/logs", "Recent logs"),
        kv_line("/setmain", "Set main channel"),
        kv_line("/addsub", "Add sub-channel"),
        kv_line("/removesub", "Remove sub-channel"),
        kv_line("/listsub", "List channels"),
        kv_line("/broadcast", "Broadcast message"),
        kv_line("/cancel", "Cancel a job"),
        kv_line("/reload", "Reload config"),
        box_bot(36),
    ]
    return "\n".join(lines)


def channel_list(channels: list[dict]) -> str:
    lines = [
        box_top(36),
        tag_bold("Configured Channels"),
        "",
    ]
    for ch in channels:
        name = ch.get("name", "?")
        cid = ch.get("channel_id", "")
        lines.append(kv_line(name, cid))
    lines.append(box_bot(36))
    return "\n".join(lines)
