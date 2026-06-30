from models.anime import Anime


def extract_episode_range(anime: Anime, start: int, end: int) -> list[dict]:
    episodes = []
    for ep_num in range(start, end + 1):
        episodes.append({
            "season": anime.season or 1,
            "episode": ep_num,
        })
    return episodes


def get_available_languages(anime: Anime) -> list[str]:
    return anime.languages or ["Dual Audio"]


def get_audio_track_id(language: str, anime: Anime) -> str | None:
    for dub in anime.dubs:
        if language.lower() in dub.get("lanName", "").lower():
            return dub.get("subjectId")
    return None
