from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from core.utils import utcnow


@dataclass
class User:
    telegram_id: int
    is_admin: bool = False
    username: str = ""
    first_name: str = ""
    cooldown_until: Optional[datetime] = None
    created_at: datetime = field(default_factory=utcnow)
    last_active: datetime = field(default_factory=utcnow)

    def to_dict(self) -> dict:
        return {
            "telegram_id": self.telegram_id,
            "is_admin": self.is_admin,
            "username": self.username,
            "first_name": self.first_name,
            "cooldown_until": self.cooldown_until,
            "created_at": self.created_at,
            "last_active": self.last_active,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
