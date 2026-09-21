from dataclasses import dataclass, field
from uuid import UUID, uuid4

from app.domain.entities.base_entity import BaseEntity
from app.domain.entities.permission import Permission


@dataclass
class Role(BaseEntity):
    name: str
    level: int
    description: str | None = None
    permissions: list[Permission] = field(default_factory=list)

    def has_permission(self, permission_name: str) -> bool:
        return any(
            permission.name == permission_name for permission in self.permissions
        )
