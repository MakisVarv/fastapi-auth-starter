from typing import cast
from uuid import UUID

import pytest

from app.application.errors import (
    AuthorizationError,
    AuthorizationReason,
    EmailAlreadyRegisteredError,
    RoleNotFoundError,
)
from app.application.ports.password_hasher import PasswordHasher
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.users.create_user import CreateUser
from app.domain.entities.role import Role
from app.domain.entities.user import User


class FakeUserRepository:
    def __init__(self, existing_user: User | None = None) -> None:
        self.existing_user = existing_user
        self.requested_email: str | None = None
        self.added_user: User | None = None

    def get_by_email(self, email: str) -> User | None:
        self.requested_email = email

        if self.existing_user is not None and self.existing_user.email == email:
            return self.existing_user

        return None

    def add(self, user: User) -> None:
        self.added_user = user


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
    def __init__(
        self,
        *,
        role: Role | None,
        existing_user: User | None = None,
    ) -> None:
        self.users = FakeUserRepository(existing_user)
        self.roles = FakeRoleRepository(role)
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        pass

    def commit(self) -> None:
        self.committed = True


class FakePasswordHasher:
    def __init__(self) -> None:
        self.hashed_passwords: list[str] = []

    def hash(self, password: str) -> str:
        self.hashed_passwords.append(password)
        return f"hashed:{password}"

    def verify(
        self,
        password: str,
        password_hash: str,
    ) -> bool:
        raise NotImplementedError


def make_actor(level: int = 80) -> User:
    return User(
        first_name="Actor",
        last_name="User",
        email="actor@example.com",
        password_hash="actor-hash",
        role=Role(
            name="Manager",
            level=level,
        ),
    )


def make_existing_user(
    *,
    email: str,
) -> User:
    return User(
        first_name="Existing",
        last_name="User",
        email=email,
        password_hash="existing-hash",
        role=Role(
            name="User",
            level=10,
        ),
    )


def test_create_user_adds_user_hashes_password_and_commits() -> None:
    actor = make_actor()

    target_role = Role(
        name="Support",
        level=40,
    )

    uow = FakeUnitOfWork(role=target_role)
    password_hasher = FakePasswordHasher()

    use_case = CreateUser(
        uow=cast(UnitOfWork, uow),
        password_hasher=cast(PasswordHasher, password_hasher),
    )

    result = use_case.execute(
        actor=actor,
        first_name="Alice",
        last_name="Stone",
        email="alice@example.com",
        password="plain-password",
        role_id=target_role.id,
        phone="+30-123456789",
    )

    assert result is uow.users.added_user

    assert result.first_name == "Alice"
    assert result.last_name == "Stone"
    assert result.email == "alice@example.com"
    assert result.phone == "+30-123456789"
    assert result.password_hash == "hashed:plain-password"
    assert result.role is target_role
    assert result.is_active is True

    assert uow.roles.requested_id == target_role.id
    assert password_hasher.hashed_passwords == ["plain-password"]
    assert uow.committed is True


def test_create_user_normalizes_email() -> None:
    actor = make_actor()

    target_role = Role(
        name="Support",
        level=40,
    )

    uow = FakeUnitOfWork(role=target_role)
    password_hasher = FakePasswordHasher()

    use_case = CreateUser(
        uow=cast(UnitOfWork, uow),
        password_hasher=cast(PasswordHasher, password_hasher),
    )

    result = use_case.execute(
        actor=actor,
        first_name="Alice",
        last_name="Stone",
        email="  ALICE@EXAMPLE.COM  ",
        password="plain-password",
        role_id=target_role.id,
    )

    assert uow.users.requested_email == "alice@example.com"
    assert result.email == "alice@example.com"


def test_create_user_rejects_missing_role() -> None:
    actor = make_actor()

    missing_role = Role(
        name="Missing",
        level=40,
    )

    uow = FakeUnitOfWork(role=None)
    password_hasher = FakePasswordHasher()

    use_case = CreateUser(
        uow=cast(UnitOfWork, uow),
        password_hasher=cast(PasswordHasher, password_hasher),
    )

    with pytest.raises(RoleNotFoundError):
        use_case.execute(
            actor=actor,
            first_name="Alice",
            last_name="Stone",
            email="alice@example.com",
            password="plain-password",
            role_id=missing_role.id,
        )

    assert uow.users.added_user is None
    assert password_hasher.hashed_passwords == []
    assert uow.committed is False


def test_create_user_rejects_role_actor_cannot_assign() -> None:
    actor = make_actor(level=50)

    target_role = Role(
        name="Manager",
        level=50,
    )

    uow = FakeUnitOfWork(role=target_role)
    password_hasher = FakePasswordHasher()

    use_case = CreateUser(
        uow=cast(UnitOfWork, uow),
        password_hasher=cast(PasswordHasher, password_hasher),
    )

    with pytest.raises(AuthorizationError) as exc_info:
        use_case.execute(
            actor=actor,
            first_name="Alice",
            last_name="Stone",
            email="alice@example.com",
            password="plain-password",
            role_id=target_role.id,
        )

    assert exc_info.value.reason == AuthorizationReason.CANNOT_ASSIGN_ROLE

    assert uow.users.added_user is None
    assert password_hasher.hashed_passwords == []
    assert uow.committed is False


def test_create_user_rejects_duplicate_email() -> None:
    actor = make_actor()

    target_role = Role(
        name="Support",
        level=40,
    )

    existing_user = make_existing_user(
        email="existing@example.com",
    )

    uow = FakeUnitOfWork(
        role=target_role,
        existing_user=existing_user,
    )
    password_hasher = FakePasswordHasher()

    use_case = CreateUser(
        uow=cast(UnitOfWork, uow),
        password_hasher=cast(PasswordHasher, password_hasher),
    )

    with pytest.raises(EmailAlreadyRegisteredError):
        use_case.execute(
            actor=actor,
            first_name="Another",
            last_name="User",
            email="  EXISTING@EXAMPLE.COM ",
            password="plain-password",
            role_id=target_role.id,
        )

    assert uow.users.requested_email == "existing@example.com"
    assert uow.users.added_user is None
    assert password_hasher.hashed_passwords == []
    assert uow.committed is False
