from ui.theme import box_top, box_bot, kv_line, tag_bold, tag_pre
from ui.html_builder import build_button, build_inline_keyboard


def start_dialog(first_name: str) -> str:
    lines = [
        box_top(36),
        tag_bold("AutoAnimeBot"),
        "",
        tag_pre(f"Welcome    : {first_name}"),
        "",
        "Send an anime name to search.",
        "",
        "Commands:",
        "<code>/help</code>  - Show this message",
        "<code>/admin</code> - Admin panel",
        "<code>/post</code>  - Post anime by slug",
        box_bot(36),
    ]
    return "\n".join(lines)
