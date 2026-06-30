import os
import uuid

import aiofiles

from core.config import config
from core.http_client import HttpClient
from core.logger import logger
from core.retry import with_retry


@with_retry()
async def download_episode(subject: dict, season: int, episode: int, language: str) -> str | None:
    play_url = await _resolve_play_url(subject, season, episode, language)
    if not play_url:
        logger.error("No play URL resolved for %s S%02dE%02d", subject.get("title", ""), season, episode)
        return None

    file_name = f"{uuid.uuid4().hex}.mp4"
    file_path = os.path.join(config.TEMP_DIR, file_name)
    os.makedirs(config.TEMP_DIR, exist_ok=True)

    try:
        await _download_file(play_url, file_path)
        return file_path
    except Exception as e:
        logger.exception("Download failed for %s: %s", play_url, e)
        if os.path.exists(file_path):
            os.remove(file_path)
        return None


async def _resolve_play_url(subject: dict, season: int, episode: int, language: str) -> str | None:
    from services.api_client import get_play_url
    return await get_play_url(subject, season, episode, language)


@with_retry()
async def _download_file(url: str, file_path: str):
    client = HttpClient.get()
    headers = {
        "Referer": "https://moviebox.org/",
        "Origin": "https://moviebox.org",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    async with client.stream("GET", url, headers=headers) as resp:
        resp.raise_for_status()
        async with aiofiles.open(file_path, "wb") as f:
            async for chunk in resp.aiter_bytes(chunk_size=1048576):
                await f.write(chunk)
    logger.info("Downloaded: %s -> %s", url.split("?")[0], file_path)
