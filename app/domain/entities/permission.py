from dataclasses import dataclass

from app.domain.entities.base_entity import BaseEntity


@dataclass
class Permission(BaseEntity):
    name: str
    description: str | None = None
