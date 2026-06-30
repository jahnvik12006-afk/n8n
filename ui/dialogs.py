from ui.theme import box_top, box_bot, kv_line, tag_bold
from ui.html_builder import build_button, build_inline_keyboard


def start_dialog(first_name: str) -> str:
    lines = [
        box_top(36),
        tag_bold("AutoAnimeBot"),
        "",
        kv_line("Welcome", first_name),
        "",
        "Send an anime name to search.",
        box_bot(36),
    ]
    return "\n".join(lines)


def ask_start_episode(slug: str, language: str) -> str:
    lines = [
        box_top(36),
        tag_bold("Multiple Upload"),
        "",
        kv_line("Slug", slug),
        kv_line("Language", language),
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
        kv_line("Slug", slug),
        kv_line("Language", language),
        kv_line("Start Ep", str(start_ep)),
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
        kv_line("Job ID", job_id),
        kv_line("Title", slug),
        kv_line("Language", language),
        kv_line("Channel", channel),
        kv_line("Episodes", str(episode_count)),
        "",
        "You will be notified when complete.",
        box_bot(36),
    ]
    return "\n".join(lines)
