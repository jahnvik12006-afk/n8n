from ui.theme import box_top, box_bot, kv_line, tag_bold, tag_pre
from ui.html_builder import build_button, build_inline_keyboard


def start_dialog(first_name: str) -> str:
    lines = [
        box_top(36),
        tag_bold("AutoAnimeBot"),
        "",
        tag_pre(f"Welcome    : {first_name}"),
        "",
        "Send any anime name to search.",
        "",
        "Commands:",
        "<code>/help</code>    - This message",
        "<code>/trending</code>- Trending anime",
        "<code>/latest</code>  - Latest anime",
        "<code>/content</code> - Content lists (anime,bollywood,hollywood...)",
        "<code>/post</code>    - Post anime by slug",
        "<code>/admin</code>   - Admin panel",
        "<code>/jobs</code>    - View job queue",
        "<code>/stats</code>   - Bot statistics",
        "<code>/listsub</code> - List channels",
        box_bot(36),
    ]
    return "\n".join(lines)


def ask_start_episode(slug: str, language: str) -> str:
    lines = [
        box_top(36),
        tag_bold("Multiple Upload"),
        "",
        tag_pre(f"Slug       : {slug}"),
        tag_pre(f"Language   : {language}"),
        "",
        "Send the start episode number.",
        box_bot(36),
    ]
    return "\n".join(lines, build_button("Cancel", f"cancel_flow:{slug}"))


def ask_end_episode(slug: str, language: str, start_ep: int) -> str:
    lines = [
        box_top(36),
        tag_bold("Multiple Upload"),
        "",
        tag_pre(f"Slug       : {slug}"),
        tag_pre(f"Language   : {language}"),
        tag_pre(f"Start Ep   : {start_ep}"),
        "",
        "Send the end episode number.",
        box_bot(36),
    ]
    return "\n".join(lines, build_button("Cancel", f"cancel_flow:{slug}"))


def job_queued_card(job_id: str, slug: str, episode_count: int, language: str, channel: str) -> str:
    lines = [
        box_top(36),
        tag_bold("Job Queued"),
        "",
        tag_pre(f"Job ID     : {job_id}"),
        tag_pre(f"Title      : {slug}"),
        tag_pre(f"Language   : {language}"),
        tag_pre(f"Channel    : {channel}"),
        tag_pre(f"Episodes   : {episode_count}"),
        "",
        "You will be notified when complete.",
        box_bot(36),
    ]
    return "\n".join(lines, build_button("Cancel", f"cancel:{job_id}"))
