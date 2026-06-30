from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Anime:
    subject_id: str
    title: str
    slug: str
    subject_type: int
    description: str = ""
    genre: str = ""
    cover_url: str = ""
    country: str = ""
    imdb_rating: str = ""
    status: str = ""
    season: int = 0
    detail_path: str = ""
    has_resource: bool = False
    dubs: list[dict] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    max_episodes: int = 0
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_api(cls, data: dict) -> "Anime":
        subject = data.get("subject", data)
        resource = data.get("resource", {})
        seasons = resource.get("seasons", [])
        max_ep = 0
        for s in seasons:
            max_ep = max(max_ep, s.get("maxEp", 0))

        cover = subject.get("cover", {})
        dubs_list = subject.get("dubs", [])
        languages = [d.get("lanName", "") for d in dubs_list if d.get("lanName")]

        return cls(
            subject_id=str(subject.get("subjectId", "")),
            title=subject.get("title", "Unknown"),
            slug=subject.get("detailPath", ""),
            subject_type=subject.get("subjectType", 0),
            description=subject.get("description", ""),
            genre=subject.get("genre", ""),
            cover_url=cover.get("url", "") if isinstance(cover, dict) else "",
            country=subject.get("countryName", ""),
            imdb_rating=str(subject.get("imdbRatingValue", "")),
            season=subject.get("season", 0),
            detail_path=subject.get("detailPath", ""),
            has_resource=subject.get("hasResource", False),
            dubs=dubs_list,
            languages=languages,
            max_episodes=max_ep,
            raw=data,
        )
