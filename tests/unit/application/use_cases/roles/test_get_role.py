from typing import cast
from uuid import UUID, uuid4

import pytest

from app.application.errors import RoleNotFoundError
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.roles.get_role import GetRole
from app.domain.entities.role import Role


class FakeRoleRepository:
    def __init__(self, role: Role | None) -> None:
        self.role = role
        self.requested_id: UUID | None = None

    def get_by_id(self, role_id: UUID) -> Role | None:
        self.requested_id = role_id

        if self.role is not None and self.role.id == role_id:
            return self.role

        return None


class FakeUnitOfWork:
    def __init__(self, role: Role | None) -> None:
        self.roles = FakeRoleRepository(role)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        pass


def test_get_role_returns_role() -> None:
    role = Role(
        name="Support",
        level=50,
    )

    uow = FakeUnitOfWork(role)

    use_case = GetRole(
        uow=cast(UnitOfWork, uow),
    )

    result = use_case.execute(role.id)

    assert result is role
    assert uow.roles.requested_id == role.id


def test_get_role_rejects_missing_role() -> None:
    missing_id = uuid4()

    uow = FakeUnitOfWork(None)

    use_case = GetRole(
        uow=cast(UnitOfWork, uow),
    )

    with pytest.raises(RoleNotFoundError):
        use_case.execute(missing_id)

    assert uow.roles.requested_id == missing_id
