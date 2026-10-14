from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.entities.base_entity import BaseEntity


@dataclass
class PasswordResetToken(BaseEntity):
    user_id: UUID
    token_hash: str
    expires_at: datetime
    used_at: datetime | None = None
