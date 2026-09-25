from typing import cast
from uuid import UUID, uuid4

import pytest

from app.application.errors import PermissionNotFoundError
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.permissions.get_permission import GetPermission
from app.domain.entities.permission import Permission


class FakePermissionRepository:
    def __init__(self, permission: Permission | None) -> None:
        self.permission = permission
        self.requested_id: UUID | None = None

    def get_by_id(
        self,
        permission_id: UUID,
    ) -> Permission | None:
        self.requested_id = permission_id

        if self.permission is not None and self.permission.id == permission_id:
            return self.permission

        return None


class FakeUnitOfWork:
    def __init__(self, permission: Permission | None) -> None:
        self.permissions = FakePermissionRepository(permission)

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        pass


def test_get_permission_returns_permission() -> None:
    permission = Permission(
        name="user.read",
        description="Read users",
    )

    uow = FakeUnitOfWork(permission)

    use_case = GetPermission(
        uow=cast(UnitOfWork, uow),
    )

    result = use_case.execute(permission.id)

    assert result is permission
    assert uow.permissions.requested_id == permission.id


def test_get_permission_rejects_missing_permission() -> None:
    missing_id = uuid4()

    uow = FakeUnitOfWork(None)

    use_case = GetPermission(
        uow=cast(UnitOfWork, uow),
    )

    with pytest.raises(PermissionNotFoundError):
        use_case.execute(missing_id)

    assert uow.permissions.requested_id == missing_id
