SYMBOLS = {
    "box_top": "╭",
    "box_bot": "╰",
    "line_h": "─",
    "line_v": "│",
    "split": "├",
    "end": "└",
    "bullet": "■",
    "bullet_sm": "□",
    "diamond": "◆",
    "diamond_sm": "◇",
    "arrow_up": "▲",
    "arrow_down": "▼",
    "arrow_right": "▶",
    "arrow_left": "◀",
}


def box_line(width: int = 40) -> str:
    return SYMBOLS["line_h"] * width


def box_top(width: int = 40) -> str:
    return f"{SYMBOLS['box_top']}{box_line(width)}"


def box_bot(width: int = 40) -> str:
    return f"{SYMBOLS['box_bot']}{box_line(width)}"


def box_split(width: int = 40) -> str:
    return f"{SYMBOLS['split']}{box_line(width)}"


def tag_bold(text: str) -> str:
    return f"<b>{text}</b>"


def tag_code(text: str) -> str:
    return f"<code>{text}</code>"


def tag_pre(text: str) -> str:
    return f"<pre>{text}</pre>"


def kv_line(key: str, value: str) -> str:
    return f"{SYMBOLS['line_v']} {tag_code(f'{key:<12}: {value}')}"


def kv_emoji(emoji: str, key: str, value: str) -> str:
    return f"{SYMBOLS['line_v']} {emoji} {tag_code(f'{key:<8}: {value}')}"
