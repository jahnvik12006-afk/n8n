from dataclasses import dataclass


@dataclass
class Episode:
    subject_id: str
    season: int
    episode: int
    title: str = ""
    download_url: str = ""
    language: str = ""
    quality: str = ""
    size: int = 0
    duration: int = 0

    @classmethod
    def from_play_data(cls, subject_id: str, season: int, episode: int, data: dict, language: str = "") -> "Episode":
        streams = data.get("streams", [])
        best = max(streams, key=lambda s: int(s.get("resolutions", "0").rstrip("p") or "0")) if streams else {}
        return cls(
            subject_id=subject_id,
            season=season,
            episode=episode,
            download_url=best.get("url", ""),
            language=language,
            quality=best.get("resolutions", ""),
            size=best.get("size", 0),
            duration=best.get("duration", 0),
        )
