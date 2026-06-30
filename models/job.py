from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from core.utils import utcnow


@dataclass
class Job:
    job_id: str
    admin_id: int
    status: str = "Pending"
    subject: dict = field(default_factory=dict)
    slug: str = ""
    language: str = ""
    episodes: list[dict] = field(default_factory=list)
    channel_id: str = ""
    channel_name: str = ""
    message_id: int = 0
    retry_count: int = 0
    error: str = ""
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "admin_id": self.admin_id,
            "status": self.status,
            "subject": self.subject,
            "slug": self.slug,
            "language": self.language,
            "episodes": self.episodes,
            "channel_id": self.channel_id,
            "channel_name": self.channel_name,
            "message_id": self.message_id,
            "retry_count": self.retry_count,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Job":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
