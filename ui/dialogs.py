from ui.theme import box_top, box_bot, kv_emoji, tag_bold
from ui.html_builder import build_button


def start_dialog(first_name: str) -> str:
    lines = [
        box_top(36),
        tag_bold("🤖 AutoAnimeBot v2.0"),
        "",
        f"Welcome, {tag_bold(first_name)}!",
        "",
        "Send any anime name to search.",
        "",
        "<b>Commands:</b>",
        "<code>/help</code>          - This message",
        "<code>/trending</code>      - Trending anime",
        "<code>/latest</code>        - Latest anime",
        "<code>/content</code>       - Content lists",
        "<code>/post &lt;slug&gt;</code>  - Post by slug",
        "<code>/admin</code>         - Admin panel",
        "<code>/jobs</code>          - View job queue",
        "<code>/stats</code>         - Bot statistics",
        "<code>/listsub</code>       - List channels",
        box_bot(36),
    ]
    return "\n".join(lines)


def ask_start_episode(slug: str, language: str) -> tuple[str, str]:
    lines = [
        box_top(36),
        tag_bold("📦 Multiple Upload"),
        "",
        kv_emoji("🔗", "Slug", slug),
        kv_emoji("🔊", "Audio", language),
        "",
        "Send the <b>start</b> episode number:",
        box_bot(36),
    ]
    return "\n".join(lines), build_button("Cancel", f"cancel_flow:{slug}")


def ask_end_episode(slug: str, language: str, start_ep: int) -> tuple[str, str]:
    lines = [
        box_top(36),
        tag_bold("📦 Multiple Upload"),
        "",
        kv_emoji("🔗", "Slug", slug),
        kv_emoji("🔊", "Audio", language),
        kv_emoji("▶", "Start Ep", str(start_ep)),
        "",
        "Send the <b>end</b> episode number:",
        box_bot(36),
    ]
    return "\n".join(lines), build_button("Cancel", f"cancel_flow:{slug}")


def job_queued_card(job_id: str, slug: str, episode_count: int, language: str, channel: str) -> tuple[str, str]:
    lines = [
        box_top(36),
        tag_bold("✅ Job Queued"),
        "",
        kv_emoji("🆔", "Job ID", job_id),
        kv_emoji("🎬", "Title", slug),
        kv_emoji("🔊", "Audio", language),
        kv_emoji("📢", "Channel", channel),
        kv_emoji("📺", "Episodes", str(episode_count)),
        "",
        "You will be notified when complete.",
        box_bot(36),
    ]
    return "\n".join(lines), build_button("Cancel", f"cancel:{job_id}")
