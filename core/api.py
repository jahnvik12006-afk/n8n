import hashlib
from urllib.parse import urlencode

from core.config import config
from core.http_client import HttpClient
from core.logger import logger
from core.retry import with_retry


def _headers():
    return {
        "Content-Type": "application/json;charset=UTF-8",
        "x-platform": "h5",
        "x-device": "web",
        "version-code": "200",
        "Origin": "https://moviebox.org",
        "Referer": "https://moviebox.org/",
    }


@with_retry()
async def api_post(endpoint: str, body: dict, extra_headers: dict | None = None) -> dict:
    url = f"{config.API_BASE}{endpoint}"
    hdrs = {**_headers(), **(extra_headers or {})}
    client = HttpClient.get()
    resp = await client.post(url, json=body, headers=hdrs)
    resp.raise_for_status()
    return resp.json()


@with_retry()
async def api_get(endpoint: str, params: dict | None = None, extra_headers: dict | None = None) -> dict:
    url = f"{config.API_BASE}{endpoint}"
    hdrs = {**_headers(), **(extra_headers or {})}
    client = HttpClient.get()
    resp = await client.get(url, params=params, headers=hdrs)
    resp.raise_for_status()
    return resp.json()


async def fetch_search_results(keyword: str, page: int = 0, per_page: int = 28, subject_type: int = 0) -> dict:
    return await api_post("/subject/search", {
        "keyword": keyword,
        "page": str(page),
        "perPage": per_page,
        "subjectType": subject_type,
    })


async def fetch_subject_detail(subject_id: str | None = None, detail_path: str | None = None) -> dict:
    params = {}
    if subject_id:
        params["subjectId"] = subject_id
    if detail_path:
        params["detailPath"] = detail_path
    return await api_get("/subject/detail", params=params)


async def fetch_trending(page: int = 0, per_page: int = 18) -> dict:
    return await api_get("/subject/trending", {"page": str(page), "perPage": per_page})


async def fetch_recommendations(subject_id: str, page: int = 1, per_page: int = 12) -> dict:
    return await api_post("/subject/detail-rec", {
        "subjectId": subject_id,
        "page": str(page),
        "perPage": per_page,
    })


async def fetch_play_info(subject_id: str, detail_path: str, season: int = 0, episode: int = 0) -> dict:
    params = {
        "subjectId": subject_id,
        "detailPath": detail_path,
        "platform": "h5",
        "deviceType": "web",
        "deviceModel": "chrome",
    }
    if season > 0:
        params["season"] = str(season)
    if episode > 0:
        params["episode"] = str(episode)

    url = f"{config.API_PLAY_BASE}?{urlencode(params)}"
    client = HttpClient.get()
    hdrs = {
        **_headers(),
        "Authorization": f"Bearer {config.API_TOKEN}",
    }
    resp = await client.get(url, headers=hdrs)
    resp.raise_for_status()
    return resp.json()


async def fetch_content_list(content_type: str, page: int = 1, per_page: int = 12) -> dict:
    return await api_get("/subject/content", {
        "type": content_type,
        "page": str(page),
        "perPage": per_page,
    })
