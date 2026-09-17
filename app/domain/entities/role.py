from dataclasses import dataclass, field
from uuid import UUID, uuid4

from app.domain.entities.permission import Permission


@dataclass
class Role:
    name: str
    level: int
    description: str | None = None
    id: UUID = field(default_factory=uuid4)
    permissions: list[Permission] = field(default_factory=list)

    def has_permission(self, permission_name: str) -> bool:
        return any(
            permission.name == permission_name for permission in self.permissions
        )
