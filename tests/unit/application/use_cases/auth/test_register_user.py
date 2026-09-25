from typing import cast

import pytest

from app.application.errors import (
    EmailAlreadyRegisteredError,
    RegistrationRoleNotFoundError,
)
from app.application.ports.password_hasher import PasswordHasher
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.auth.register_user import RegisterUser
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
        self.requested_name: str | None = None

    def get_by_name(self, name: str) -> Role | None:
        self.requested_name = name

        if self.role is not None and self.role.name == name:
            return self.role

        return None


class FakeUnitOfWork:
    def __init__(
        self,
        *,
        existing_user: User | None = None,
        role: Role | None,
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


def make_existing_user(
    *,
    email: str = "existing@example.com",
) -> User:
    role = Role(
        name="User",
        level=10,
    )

    return User(
        first_name="Existing",
        last_name="User",
        email=email,
        password_hash="existing-hash",
        role=role,
    )


def test_register_creates_user_hashes_password_and_commits() -> None:
    user_role = Role(
        name="User",
        level=10,
    )

    uow = FakeUnitOfWork(
        role=user_role,
    )
    password_hasher = FakePasswordHasher()

    use_case = RegisterUser(
        uow=cast(UnitOfWork, uow),
        password_hasher=cast(PasswordHasher, password_hasher),
    )

    result = use_case.execute(
        first_name="Alice",
        last_name="Stone",
        email="alice@example.com",
        password="plain-password",
        phone="+30-123456789",
    )

    assert result is uow.users.added_user

    assert result.first_name == "Alice"
    assert result.last_name == "Stone"
    assert result.email == "alice@example.com"
    assert result.phone == "+30-123456789"
    assert result.password_hash == "hashed:plain-password"
    assert result.role is user_role
    assert result.is_active is True

    assert uow.roles.requested_name == "User"
    assert password_hasher.hashed_passwords == ["plain-password"]
    assert uow.committed is True


def test_register_normalizes_email_before_lookup_and_creation() -> None:
    user_role = Role(
        name="User",
        level=10,
    )

    uow = FakeUnitOfWork(
        role=user_role,
    )
    password_hasher = FakePasswordHasher()

    use_case = RegisterUser(
        uow=cast(UnitOfWork, uow),
        password_hasher=cast(PasswordHasher, password_hasher),
    )

    result = use_case.execute(
        first_name="Alice",
        last_name="Stone",
        email="  ALICE@EXAMPLE.COM  ",
        password="plain-password",
    )

    assert uow.users.requested_email == "alice@example.com"
    assert result.email == "alice@example.com"


def test_register_rejects_existing_email() -> None:
    existing_user = make_existing_user(
        email="existing@example.com",
    )

    user_role = Role(
        name="User",
        level=10,
    )

    uow = FakeUnitOfWork(
        existing_user=existing_user,
        role=user_role,
    )
    password_hasher = FakePasswordHasher()

    use_case = RegisterUser(
        uow=cast(UnitOfWork, uow),
        password_hasher=cast(PasswordHasher, password_hasher),
    )

    with pytest.raises(EmailAlreadyRegisteredError):
        use_case.execute(
            first_name="Another",
            last_name="User",
            email="  EXISTING@EXAMPLE.COM ",
            password="plain-password",
        )

    assert uow.users.requested_email == "existing@example.com"
    assert uow.users.added_user is None
    assert password_hasher.hashed_passwords == []
    assert uow.committed is False


def test_register_rejects_missing_registration_role() -> None:
    uow = FakeUnitOfWork(
        role=None,
    )
    password_hasher = FakePasswordHasher()

    use_case = RegisterUser(
        uow=cast(UnitOfWork, uow),
        password_hasher=cast(PasswordHasher, password_hasher),
    )

    with pytest.raises(RegistrationRoleNotFoundError):
        use_case.execute(
            first_name="Alice",
            last_name="Stone",
            email="alice@example.com",
            password="plain-password",
        )

    assert uow.roles.requested_name == "User"
    assert uow.users.added_user is None
    assert password_hasher.hashed_passwords == []
    assert uow.committed is False
