from services.api_client import search_anime, get_anime_detail
from models.anime import Anime


async def perform_search(query: str, page: int = 0) -> list[Anime]:
    return await search_anime(query, page)


async def get_detail(subject_id: str | None = None, slug: str | None = None) -> Anime | None:
    return await get_anime_detail(subject_id, slug)
