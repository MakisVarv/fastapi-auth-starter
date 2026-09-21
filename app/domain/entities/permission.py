from dataclasses import dataclass, field
from uuid import UUID, uuid4

from app.domain.entities.base_entity import BaseEntity


@dataclass
class Permission(BaseEntity):
    name: str
    description: str | None = None
