from typing import cast

import pytest

from app.application.errors import (
    AuthorizationError,
    AuthorizationReason,
    RoleAlreadyExist,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.roles.create_role import CreateRole
from app.domain.entities.role import Role
from app.domain.entities.user import User


class FakeRoleRepository:
    def __init__(self, existing_role: Role | None = None) -> None:
        self.existing_role = existing_role
        self.requested_name: str | None = None
        self.added_role: Role | None = None

    def get_by_name(self, name: str) -> Role | None:
        self.requested_name = name

        if self.existing_role is not None and self.existing_role.name == name:
            return self.existing_role

        return None

    def add(self, role: Role) -> None:
        self.added_role = role


class FakeUnitOfWork:
    def __init__(self, existing_role: Role | None = None) -> None:
        self.roles = FakeRoleRepository(existing_role)
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        pass

    def commit(self) -> None:
        self.committed = True


def make_actor(level: int = 80) -> User:
    return User(
        first_name="Actor",
        last_name="User",
        email="actor@example.com",
        password_hash="hash",
        role=Role(name="Manager", level=level),
    )


def test_create_role_adds_role_and_commits() -> None:
    actor = make_actor()
    uow = FakeUnitOfWork()

    use_case = CreateRole(uow=cast(UnitOfWork, uow))

    result = use_case.execute(
        actor=actor,
        name="Support",
        description="Support team",
        level=50,
    )

    assert result is uow.roles.added_role
    assert result.name == "Support"
    assert result.description == "Support team"
    assert result.level == 50

    assert uow.roles.requested_name == "Support"
    assert uow.committed is True


def test_create_role_rejects_level_actor_cannot_set() -> None:
    actor = make_actor(level=50)
    uow = FakeUnitOfWork()

    use_case = CreateRole(uow=cast(UnitOfWork, uow))

    with pytest.raises(AuthorizationError) as exc_info:
        use_case.execute(
            actor=actor,
            name="Support",
            description=None,
            level=50,
        )

    assert exc_info.value.reason == AuthorizationReason.CANNOT_SET_ROLE_LEVEL
    assert uow.roles.requested_name is None
    assert uow.roles.added_role is None
    assert uow.committed is False


def test_create_role_rejects_duplicate_name() -> None:
    actor = make_actor()

    existing = Role(
        name="Support",
        level=40,
    )

    uow = FakeUnitOfWork(existing_role=existing)

    use_case = CreateRole(uow=cast(UnitOfWork, uow))

    with pytest.raises(RoleAlreadyExist):
        use_case.execute(
            actor=actor,
            name="Support",
            description=None,
            level=50,
        )

    assert uow.roles.added_role is None
    assert uow.committed is False
