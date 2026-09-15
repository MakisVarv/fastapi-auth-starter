from typing import Protocol

from app.domain.entities.role import Role


class RoleRepository(Protocol):

    def get_by_name(self, name: str) -> Role | None: ...
