from core.api import (
    fetch_search_results,
    fetch_subject_detail,
    fetch_trending,
    fetch_recommendations,
    fetch_play_info,
    fetch_content_list,
)
from core.cache import Cache
from core.config import config
from core.logger import logger
from models.anime import Anime


async def search_anime(keyword: str, page: int = 0, per_page: int = 28) -> list[Anime]:
    cache_key = f"search:{keyword.lower()}:{page}:{per_page}"
    cached = await Cache.get(cache_key)
    if cached:
        return [Anime.from_api(item) for item in __import__("json").loads(cached)]

    data = await fetch_search_results(keyword, page, per_page)
    results = []
    if data.get("code") == 0:
        records = data.get("data", {}).get("subjectList", [])
        if not records:
            records = data.get("data", {}).get("records", [])
        results = [Anime.from_api(item) for item in records]
        await Cache.set(cache_key, __import__("json").dumps(records), ttl=300)
    return results


async def get_anime_detail(subject_id: str | None = None, detail_path: str | None = None) -> Anime | None:
    cache_key = f"detail:{subject_id or ''}:{detail_path or ''}"
    cached = await Cache.get(cache_key)
    if cached:
        return Anime.from_api(__import__("json").loads(cached))

    data = await fetch_subject_detail(subject_id, detail_path)
    if data.get("code") == 0:
        subject_data = data.get("data", {})
        anime = Anime.from_api(subject_data)
        await Cache.set(cache_key, __import__("json").dumps(subject_data), ttl=7200)
        return anime
    return None


async def get_play_url(subject: dict, season: int, episode: int, language: str) -> str | None:
    subject_id = subject.get("subjectId", "")
    se = season if season > 0 else 0
    ep = episode if episode > 0 else 0

    data = await fetch_play_info(subject_id, se, ep)
    if data.get("code") == 0:
        streams = data.get("data", {}).get("streams", [])
        if streams:
            best = max(streams, key=lambda s: int(s.get("resolutions", "0").rstrip("p") or "0"))
            return best.get("url")
    logger.warning("No play URL for %s S%02dE%02d", subject.get("title", ""), season, episode)
    return None


async def get_recommendations(subject_id: str, page: int = 1, per_page: int = 12) -> list[Anime]:
    data = await fetch_recommendations(subject_id, page, per_page)
    results = []
    if data.get("code") == 0:
        records = data.get("data", {}).get("subjectList", [])
        if not records:
            records = data.get("data", {}).get("records", [])
        results = [Anime.from_api(item) for item in records]
    return results


async def get_trending(page: int = 0, per_page: int = 18) -> list[Anime]:
    cache_key = f"trending:{page}:{per_page}"
    cached = await Cache.get(cache_key)
    if cached:
        return [Anime.from_api(item) for item in __import__("json").loads(cached)]

    data = await fetch_trending(page, per_page)
    results = []
    if data.get("code") == 0:
        items = data.get("data", {}).get("subjectList", [])
        results = [Anime.from_api(item) for item in items]
        await Cache.set(cache_key, __import__("json").dumps(items), ttl=1800)
    return results


async def get_content_list(content_type: str, page: int = 1, per_page: int = 12) -> list[Anime]:
    cache_key = f"content:{content_type}:{page}:{per_page}"
    cached = await Cache.get(cache_key)
    if cached:
        return [Anime.from_api(item) for item in __import__("json").loads(cached)]

    data = await fetch_content_list(content_type, page, per_page)
    results = []
    if data.get("code") == 0:
        items = data.get("data", {}).get("subjectList", [])
        results = [Anime.from_api(item) for item in items]
        await Cache.set(cache_key, __import__("json").dumps(items), ttl=1800)
    return results
