from ui.theme import (
    tag_bold, tag_code, kv_line,
    box_top, box_bot, box_line,
    SYMBOLS,
)


def build_search_card(anime: dict) -> str:
    title = anime.get("title", "Unknown")
    slug = anime.get("detailPath", "")
    subject_type = anime.get("subjectType", 0)
    genre = anime.get("genre", "")
    country = anime.get("countryName", "")
    rating = anime.get("imdbRatingValue", "")
    season = anime.get("season", 0)
    desc = anime.get("description", "")
    if len(desc) > 100:
        desc = desc[:100] + "..."

    type_label = "Movie" if subject_type == 1 else "Series"

    lines = [
        box_top(36),
        tag_bold(title),
        "",
        kv_line("Slug", slug),
        kv_line("Type", type_label),
    ]
    if genre:
        lines.append(kv_line("Genre", genre))
    if country:
        lines.append(kv_line("Country", country))
    if rating:
        lines.append(kv_line("Rating", rating))
    if season:
        lines.append(kv_line("Season", str(season)))
    lines.append(f"{SYMBOLS['split']}{box_line(36)}")
    if desc:
        lines.append(f"{SYMBOLS['line_v']} {tag_code(desc[:60])}")
    lines.append(box_bot(36))
    return "\n".join(lines)


def build_detail_card(anime: dict) -> str:
    title = anime.get("title", "Unknown")
    slug = anime.get("detailPath", "")
    subject_type = anime.get("subjectType", 0)
    genre = anime.get("genre", "")
    country = anime.get("countryName", "")
    rating = anime.get("imdbRatingValue", "")
    season = anime.get("season", 0)
    desc = anime.get("description", "")
    has_res = anime.get("hasResource", False)
    dubs = anime.get("dubs", [])
    languages = ", ".join(d.get("lanName", "") for d in dubs if d.get("lanName")) or "N/A"

    type_label = "Movie" if subject_type == 1 else "Series"

    lines = [
        box_top(36),
        tag_bold(title),
        "",
        kv_line("Slug", slug),
        kv_line("Type", type_label),
        kv_line("Genre", genre),
        kv_line("Country", country),
        kv_line("Rating", rating),
        kv_line("Status", "Available" if has_res else "N/A"),
    ]
    if subject_type == 2 and season:
        lines.append(kv_line("Season", str(season)))
    lines.append(kv_line("Languages", languages))
    lines.append(f"{SYMBOLS['split']}{box_line(36)}")
    if desc:
        for chunk in [desc[i:i+56] for i in range(0, len(desc), 56)]:
            lines.append(f"{SYMBOLS['line_v']} {tag_code(chunk)}")
    lines.append(box_bot(36))
    return "\n".join(lines)


def build_upload_progress_card(job_id: str, status: str, title: str, season: int, episode: int, progress: str) -> str:
    lines = [
        box_top(36),
        tag_bold("Upload Progress"),
        "",
        kv_line("Job ID", job_id),
        kv_line("Title", title),
        kv_line("Status", status),
    ]
    if season > 0:
        lines.append(kv_line("Episode", f"S{season}E{episode}"))
    lines.append(kv_line("Progress", progress))
    lines.append(box_bot(36))
    return "\n".join(lines)


def build_promo_card(subject: dict, season: int, episode: int, language: str) -> str:
    title = subject.get("title", "Unknown")
    lines = [
        box_top(36),
        tag_bold(title),
        "",
        kv_line("Language", language),
    ]
    if season > 0:
        lines.append(kv_line("Episode", f"S{season}E{episode}"))
    lines.append(box_bot(36))
    return "\n".join(lines)


def build_job_card(job: dict) -> str:
    job_id = job.get("job_id", "")
    status = job.get("status", "Unknown")
    title = job.get("slug", job.get("subject", {}).get("title", "Unknown"))
    channel = job.get("channel_name", job.get("channel_id", ""))
    progress = f"{job.get('episodes', [])} eps"
    created = str(job.get("created_at", ""))[:19]

    lines = [
        box_top(36),
        tag_bold(f"Job {job_id[:8]}"),
        "",
        kv_line("Title", title),
        kv_line("Status", status),
        kv_line("Channel", channel),
        kv_line("Progress", progress),
        kv_line("Created", created),
    ]
    if job.get("error"):
        lines.append(kv_line("Error", job["error"][:40]))
    lines.append(box_bot(36))
    return "\n".join(lines)


def build_stats_card(stats: dict) -> str:
    lines = [
        box_top(36),
        tag_bold("Bot Statistics"),
        "",
        kv_line("Total Jobs", str(stats.get("total_jobs", 0))),
        kv_line("Completed", str(stats.get("completed", 0))),
        kv_line("Failed", str(stats.get("failed", 0))),
        kv_line("Pending", str(stats.get("pending", 0))),
        kv_line("Running", str(stats.get("running", 0))),
        kv_line("Channels", str(stats.get("channels", 0))),
        kv_line("Cache Mem", str(stats.get("cache_memory", 0))),
        kv_line("Cache DB", str(stats.get("cache_db", 0))),
        box_bot(36),
    ]
    return "\n".join(lines)
