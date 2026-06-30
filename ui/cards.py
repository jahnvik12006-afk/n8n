from ui.theme import (
    tag_bold, tag_code,
    box_top, box_bot, box_split,
    kv_line, kv_emoji,
    SYMBOLS,
)


def _stars(rating: str) -> str:
    try:
        r = float(rating)
        full = int(r // 2)
        half = 1 if r % 2 >= 1 else 0
        empty = 5 - full - half
        return "★" * full + "☆" * half + "☆" * empty
    except (ValueError, TypeError):
        return ""


def build_search_card(anime: dict) -> str:
    title = anime.get("title", "Unknown")
    slug = anime.get("detailPath", "")
    subject_type = anime.get("subjectType", 0)
    genre = anime.get("genre", "")
    country = anime.get("countryName", "")
    rating = anime.get("imdbRatingValue", "")
    desc = anime.get("description", "")
    if len(desc) > 100:
        desc = desc[:100] + "..."

    type_label = "Movie" if subject_type == 1 else "Series"

    lines = [
        box_top(36),
        tag_bold(title),
        "",
    ]
    if slug:
        lines.append(kv_line("Slug", slug))
    lines.append(kv_emoji("🎬", "Type", type_label))
    if genre:
        lines.append(kv_emoji("🏷", "Genre", genre))
    if country:
        lines.append(kv_emoji("🌍", "Country", country))
    if rating:
        lines.append(kv_emoji("⭐", "Rating", f"{rating}  {_stars(rating)}"))
    if desc:
        lines.append(box_split(36))
        for chunk in [desc[i:i+56] for i in range(0, len(desc), 56)]:
            lines.append(f"{SYMBOLS['line_v']} {tag_code(chunk)}")
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
    ]
    if slug:
        lines.append(kv_line("Slug", slug))
    lines.append(kv_emoji("🎬", "Type", type_label))
    if genre:
        lines.append(kv_emoji("🏷", "Genre", genre))
    if country:
        lines.append(kv_emoji("🌍", "Country", country))
    if rating:
        lines.append(kv_emoji("⭐", "Rating", f"{rating}  {_stars(rating)}"))
    lines.append(kv_emoji("📡", "Status", "Available" if has_res else "N/A"))
    if subject_type == 2 and season:
        lines.append(kv_emoji("📦", "Season", str(season)))
    lines.append(kv_emoji("🔊", "Audio", languages))
    if desc:
        lines.append(box_split(36))
        for chunk in [desc[i:i+56] for i in range(0, len(desc), 56)]:
            lines.append(f"{SYMBOLS['line_v']} {tag_code(chunk)}")
    lines.append(box_bot(36))
    return "\n".join(lines)


def build_upload_progress_card(job_id: str, status: str, title: str, season: int, episode: int, progress: str) -> str:
    status_emoji = {"Downloading": "⬇", "Uploading": "⬆", "Completed": "✅", "Failed": "❌", "Pending": "⏳"}
    emoji = status_emoji.get(status, "🔄")

    lines = [
        box_top(36),
        f"{emoji} {tag_bold(status)}",
        "",
        kv_line("Job ID", job_id),
        kv_line("Title", title),
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
        tag_bold("🎬 " + title),
        "",
        kv_emoji("🔊", "Audio", language),
    ]
    if season > 0:
        lines.append(kv_emoji("📺", "Episode", f"S{season}E{episode}"))
    lines.append(box_bot(36))
    return "\n".join(lines)


def build_job_card(job: dict) -> str:
    job_id = job.get("job_id", "")
    status = job.get("status", "Unknown")
    title = job.get("slug", job.get("subject", {}).get("title", "Unknown"))
    channel = job.get("channel_name", job.get("channel_id", ""))
    progress = f"{len(job.get('episodes', []))} eps"
    created = str(job.get("created_at", ""))[:19]

    lines = [
        box_top(36),
        tag_bold(f"📋 Job {job_id[:8]}"),
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
        tag_bold("📊 Bot Statistics"),
        "",
        kv_emoji("📋", "Total Jobs", str(stats.get("total_jobs", 0))),
        kv_emoji("✅", "Completed", str(stats.get("completed", 0))),
        kv_emoji("❌", "Failed", str(stats.get("failed", 0))),
        kv_emoji("⏳", "Pending", str(stats.get("pending", 0))),
        kv_emoji("🔄", "Running", str(stats.get("running", 0))),
        kv_emoji("📢", "Channels", str(stats.get("channels", 0))),
        kv_emoji("💾", "Cache Mem", str(stats.get("cache_memory", 0))),
        kv_emoji("🗄", "Cache DB", str(stats.get("cache_db", 0))),
        box_bot(36),
    ]
    return "\n".join(lines)
