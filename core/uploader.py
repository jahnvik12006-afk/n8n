from core.logger import logger


async def upload_to_channel(channel_id: str, cdn_url: str, subject: dict, season: int, episode: int, language: str) -> bool:
    caption = _build_caption(subject, season, episode, language)

    try:
        from core.streamer import stream_video_to_channel
        return await stream_video_to_channel(channel_id, cdn_url, caption)
    except Exception as e:
        logger.exception("Upload to %s failed: %s", channel_id, e)
        return False


def _build_caption(subject: dict, season: int, episode: int, language: str) -> str:
    title = subject.get("title", "Unknown")
    lines = [
        "<b>{}</b>".format(title),
        "",
    ]
    if season > 0:
        lines.append("Season {} | Episode {}".format(season, episode))
    if language:
        lines.append("Language: {}".format(language))
    lines.append("")
    lines.append("╭────────────────")
    lines.append("<pre>{} : {}</pre>".format("Title", title))
    if season > 0:
        lines.append("<pre>{}  : S{}E{}</pre>".format("Episode", season, episode))
    lines.append("<pre>{} : {}</pre>".format("Language", language if language else "Unknown"))
    lines.append("╰────────────────")
    return "\n".join(lines)
