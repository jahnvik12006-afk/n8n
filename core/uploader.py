import os

from core.bot import Bot
from core.logger import logger
from core.retry import with_retry


@with_retry()
async def upload_to_channel(channel_id: str, file_path: str, subject: dict, season: int, episode: int, language: str) -> bool:
    caption = _build_caption(subject, season, episode, language)
    bot = Bot.get()

    try:
        await bot.send_video(channel_id, file_path, caption=caption)
        logger.info("Uploaded %s to %s", file_path, channel_id)
        return True
    except Exception as e:
        logger.exception("Upload to %s failed: %s", channel_id, e)
        return False
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug("Deleted temp file: %s", file_path)


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
