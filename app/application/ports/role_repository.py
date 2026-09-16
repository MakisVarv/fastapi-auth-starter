from typing import Protocol
from uuid import UUID

from app.domain.entities.role import Role


class RoleRepository(Protocol):

    def get_by_id(self, role_id: UUID) -> Role | None: ...

    def get_by_name(self, name: str) -> Role | None: ...
