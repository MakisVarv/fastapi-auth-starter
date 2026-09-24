from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from app.domain.entities.permission import Permission


class PermissionRepository(Protocol):

    def list_all(self) -> Sequence[Permission]: ...

    def get_by_id(self, permission_id: UUID, /) -> Permission | None: ...
