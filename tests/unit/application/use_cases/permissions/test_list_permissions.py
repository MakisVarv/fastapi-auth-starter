from collections.abc import Sequence
from typing import cast

from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.permissions.list_permissions import (
    ListPermissions,
)
from app.domain.entities.permission import Permission


class FakePermissionRepository:
    def __init__(
        self,
        permissions: Sequence[Permission],
    ) -> None:
        self.permissions = permissions
        self.list_called = False

    def list_all(self) -> Sequence[Permission]:
        self.list_called = True
        return self.permissions


class FakeUnitOfWork:
    def __init__(
        self,
        permissions: Sequence[Permission],
    ) -> None:
        self.permissions = FakePermissionRepository(permissions)

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        pass


def test_list_permissions_returns_repository_permissions() -> None:
    permissions = [
        Permission(
            name="user.read",
            description="Read users",
        ),
        Permission(
            name="role.read",
            description="Read roles",
        ),
    ]

    uow = FakeUnitOfWork(permissions)

    use_case = ListPermissions(
        uow=cast(UnitOfWork, uow),
    )

    result = use_case.execute()

    assert result is permissions
    assert uow.permissions.list_called is True


def test_list_permissions_returns_empty_sequence() -> None:
    permissions: list[Permission] = []

    uow = FakeUnitOfWork(permissions)

    use_case = ListPermissions(
        uow=cast(UnitOfWork, uow),
    )

    result = use_case.execute()

    assert result == []
    assert uow.permissions.list_called is True
