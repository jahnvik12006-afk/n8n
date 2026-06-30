import json
from urllib.parse import urlencode

from core.config import config
from core.http_client import HttpClient
from core.logger import logger
from core.retry import with_retry

_JWT_TOKEN: str | None = None
_CONTENT_TYPES: dict[str, str] = {
    "trending-cinema": "5692654647815587592",
    "trending": "4516404531735022304",
    "bollywood": "414907768299210008",
    "south-indian": "3859721901924910512",
    "hollywood": "8019599703232971616",
    "asian": "5429170738815291968",
    "top-series": "4741626294545400336",
    "anime": "8434602210994128512",
    "reality-tv": "1255898847918934600",
    "indian-drama": "4903182713986896328",
    "korean-drama": "7878715743607948784",
    "chinese-drama": "8788126208987989488",
    "western-tv": "3910636007619709856",
    "turkish-drama": "5177200225164885656",
}


def _headers():
    return {
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "X-Client-Info": '{"timezone":"Asia/Calcutta"}',
        "X-Request-Lang": "en",
        "X-Forwarded-For": "103.21.58.192",
        "X-Real-IP": "103.21.58.192",
        "Origin": "https://h5.aoneroom.com",
        "Referer": "https://h5.aoneroom.com/",
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    }


def _content_headers():
    return {
        "Accept": "application/json",
        "X-Client-Info": '{"timezone":"Asia/Calcutta"}',
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    }


async def _fetch_jwt_token() -> str | None:
    global _JWT_TOKEN
    url = f"{config.API_BASE}/subject/search"
    body = {"keyword": "a", "page": "0", "perPage": 1, "subjectType": 0}
    hdrs = {
        **_headers(),
        "Content-Type": "application/json",
    }
    client = HttpClient.get()
    resp = await client.post(url, json=body, headers=hdrs)
    x_user = resp.headers.get("x-user")
    if x_user:
        try:
            user_data = json.loads(x_user)
            _JWT_TOKEN = user_data.get("token")
            return _JWT_TOKEN
        except Exception:
            pass
    logger.warning("Failed to fetch JWT token from x-user header (status %s)", resp.status_code)
    return None


async def _get_auth_headers() -> dict:
    global _JWT_TOKEN
    if not _JWT_TOKEN:
        await _fetch_jwt_token()
    hdrs = _headers()
    if _JWT_TOKEN:
        hdrs["Authorization"] = f"Bearer {_JWT_TOKEN}"
    return hdrs


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
    url = f"{config.API_BASE}/subject/search"
    body = {
        "keyword": keyword,
        "page": str(page),
        "perPage": per_page,
        "subjectType": subject_type,
    }
    hdrs = await _get_auth_headers()
    hdrs["Content-Type"] = "application/json"
    client = HttpClient.get()
    resp = await client.post(url, json=body, headers=hdrs)
    resp.raise_for_status()
    return resp.json()


async def fetch_subject_detail(subject_id: str | None = None, detail_path: str | None = None) -> dict:
    params = {}
    if subject_id:
        params["subjectId"] = subject_id
    if detail_path:
        params["detailPath"] = detail_path
    return await api_get("/detail", params=params, extra_headers=await _get_auth_headers())


async def fetch_trending(page: int = 0, per_page: int = 18) -> dict:
    return await api_get("/subject/trending", {"page": str(page), "perPage": per_page})


async def fetch_recommendations(subject_id: str, page: int = 1, per_page: int = 12) -> dict:
    return await api_post("/subject/detail-rec", {
        "subjectId": subject_id,
        "page": str(page),
        "perPage": per_page,
    })


async def fetch_play_info(subject_id: str, season: int = 0, episode: int = 0) -> dict:
    params = {
        "subjectId": subject_id,
        "se": str(season),
        "ep": str(episode),
    }
    hdrs = await _get_auth_headers()
    client = HttpClient.get()
    url = f"https://h5.aoneroom.com/wefeed-h5-bff/web/subject/play?{urlencode(params)}"
    resp = await client.get(url, headers=hdrs)
    resp.raise_for_status()
    return resp.json()


async def fetch_content_list(content_type: str, page: int = 1, per_page: int = 12) -> dict:
    type_id = _CONTENT_TYPES.get(content_type)
    if not type_id:
        return {"error": f"Invalid type: {content_type}"}
    url = f"{config.API_BASE}/ranking-list/content?id={type_id}&page={page}&perPage={per_page}"
    hdrs = _content_headers()
    client = HttpClient.get()
    resp = await client.get(url, headers=hdrs)
    resp.raise_for_status()
    return resp.json()
