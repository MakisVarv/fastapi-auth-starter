import pytest
from sqlalchemy.orm import Session

from app.application.common.sorting import SortOptions
from app.application.errors import UserNotFoundError
from app.domain.entities.role import Role
from app.domain.entities.user import User
from app.infrastructure.repositories.role_repository import SqlAlchemyRoleRepository
from app.infrastructure.repositories.user_repository import SqlAlchemyUserRepository


def make_user(
    *,
    role: Role,
    email: str,
    first_name: str = "Test",
    last_name: str = "User",
    phone: str | None = None,
    password_hash: str = "test-password-hash",
    is_active: bool = True,
) -> User:
    return User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        password_hash=password_hash,
        is_active=is_active,
        role=role,
    )


def test_add_and_get_by_email_persists_user(db_session: Session) -> None:
    user_repository = SqlAlchemyUserRepository(db_session)
    role_repository = SqlAlchemyRoleRepository(db_session)

    admin_role = role_repository.get_by_name("Admin")
    assert admin_role is not None

    user = make_user(
        role=admin_role,
        email="alice@example.com",
        first_name="Alice",
        last_name="Stone",
        phone="+30-123456789",
    )

    user_repository.add(user)
    db_session.commit()
    db_session.expire_all()

    persisted_user = user_repository.get_by_email("alice@example.com")

    assert persisted_user is not None
    assert persisted_user.id == user.id
    assert persisted_user.first_name == "Alice"
    assert persisted_user.last_name == "Stone"
    assert persisted_user.email == "alice@example.com"
    assert persisted_user.phone == "+30-123456789"
    assert persisted_user.password_hash == "test-password-hash"
    assert persisted_user.is_active is True

    assert persisted_user.role.id == admin_role.id
    assert persisted_user.role.name == "Admin"

    assert {permission.id for permission in persisted_user.role.permissions} == {
        permission.id for permission in admin_role.permissions
    }


def test_update_persists_user_changes(db_session: Session) -> None:
    user_repository = SqlAlchemyUserRepository(db_session)
    role_repository = SqlAlchemyRoleRepository(db_session)

    user_role = role_repository.get_by_name("User")
    admin_role = role_repository.get_by_name("Admin")

    assert user_role is not None
    assert admin_role is not None

    user = make_user(
        role=user_role,
        email="before@example.com",
        first_name="Before",
        last_name="User",
    )

    user_repository.add(user)
    db_session.commit()

    user.first_name = "After"
    user.last_name = "Updated"
    user.email = "after@example.com"
    user.phone = "+30-987654321"
    user.password_hash = "updated-password-hash"
    user.is_active = False
    user.role = admin_role

    user_repository.update(user)
    db_session.commit()
    db_session.expire_all()

    persisted_user = user_repository.get_by_email("after@example.com")

    assert persisted_user is not None
    assert persisted_user.id == user.id
    assert persisted_user.first_name == "After"
    assert persisted_user.last_name == "Updated"
    assert persisted_user.phone == "+30-987654321"
    assert persisted_user.password_hash == "updated-password-hash"
    assert persisted_user.is_active is False
    assert persisted_user.role.id == admin_role.id


def test_update_missing_user_raises_user_not_found(
    db_session: Session,
) -> None:
    user_repository = SqlAlchemyUserRepository(db_session)
    role_repository = SqlAlchemyRoleRepository(db_session)

    user_role = role_repository.get_by_name("User")
    assert user_role is not None

    missing_user = make_user(
        role=user_role,
        email="missing@example.com",
    )

    with pytest.raises(UserNotFoundError):
        user_repository.update(missing_user)


def test_count_by_role_returns_correct_count(db_session: Session) -> None:
    user_repository = SqlAlchemyUserRepository(db_session)
    role_repository = SqlAlchemyRoleRepository(db_session)

    user_role = role_repository.get_by_name("User")
    admin_role = role_repository.get_by_name("Admin")

    assert user_role is not None
    assert admin_role is not None

    user_repository.add(
        make_user(
            role=user_role,
            email="user-one@example.com",
        )
    )
    user_repository.add(
        make_user(
            role=user_role,
            email="user-two@example.com",
        )
    )
    user_repository.add(
        make_user(
            role=admin_role,
            email="admin-one@example.com",
        )
    )

    db_session.commit()

    assert user_repository.count_by_role(user_role.id) == 2
    assert user_repository.count_by_role(admin_role.id) == 1


def test_list_paginated_applies_filters(db_session: Session) -> None:
    user_repository = SqlAlchemyUserRepository(db_session)
    role_repository = SqlAlchemyRoleRepository(db_session)

    user_role = role_repository.get_by_name("User")
    admin_role = role_repository.get_by_name("Admin")

    assert user_role is not None
    assert admin_role is not None

    user_repository.add(
        make_user(
            role=user_role,
            email="alice@example.com",
            first_name="Alice",
            last_name="Stone",
            is_active=True,
        )
    )
    user_repository.add(
        make_user(
            role=user_role,
            email="bob@example.com",
            first_name="Bob",
            last_name="Smith",
            is_active=False,
        )
    )
    user_repository.add(
        make_user(
            role=admin_role,
            email="carol@example.com",
            first_name="Carol",
            last_name="Jones",
            is_active=True,
        )
    )

    db_session.commit()

    search_result = user_repository.list_paginated(
        page=1,
        page_size=20,
        sort_options=SortOptions(field="first_name"),
        search="stone",
        role=None,
        is_active=None,
    )

    assert len(search_result.items) == 1
    assert search_result.items[0].email == "alice@example.com"

    role_result = user_repository.list_paginated(
        page=1,
        page_size=20,
        sort_options=SortOptions(field="first_name"),
        search=None,
        role="admin",
        is_active=None,
    )

    assert len(role_result.items) == 1
    assert role_result.items[0].email == "carol@example.com"

    active_result = user_repository.list_paginated(
        page=1,
        page_size=20,
        sort_options=SortOptions(field="first_name"),
        search=None,
        role=None,
        is_active=False,
    )

    assert len(active_result.items) == 1
    assert active_result.items[0].email == "bob@example.com"


def test_list_paginated_returns_correct_sorting_and_metadata(
    db_session: Session,
) -> None:
    user_repository = SqlAlchemyUserRepository(db_session)
    role_repository = SqlAlchemyRoleRepository(db_session)

    user_role = role_repository.get_by_name("User")
    assert user_role is not None

    for first_name, email in [
        ("Charlie", "charlie@example.com"),
        ("Alice", "alice@example.com"),
        ("Bob", "bob@example.com"),
    ]:
        user_repository.add(
            make_user(
                role=user_role,
                email=email,
                first_name=first_name,
            )
        )

    db_session.commit()

    first_page = user_repository.list_paginated(
        page=1,
        page_size=2,
        sort_options=SortOptions(field="first_name"),
        search=None,
        role=None,
        is_active=None,
    )

    assert [user.first_name for user in first_page.items] == [
        "Alice",
        "Bob",
    ]
    assert first_page.page == 1
    assert first_page.page_size == 2
    assert first_page.total == 3
    assert first_page.total_pages == 2
    assert first_page.has_next is True
    assert first_page.has_previous is False

    second_page = user_repository.list_paginated(
        page=2,
        page_size=2,
        sort_options=SortOptions(field="first_name"),
        search=None,
        role=None,
        is_active=None,
    )

    assert [user.first_name for user in second_page.items] == ["Charlie"]
    assert second_page.page == 2
    assert second_page.total == 3
    assert second_page.total_pages == 2
    assert second_page.has_next is False
    assert second_page.has_previous is True


def test_list_paginated_can_sort_by_role(db_session: Session) -> None:
    user_repository = SqlAlchemyUserRepository(db_session)
    role_repository = SqlAlchemyRoleRepository(db_session)

    user_role = role_repository.get_by_name("User")
    admin_role = role_repository.get_by_name("Admin")

    assert user_role is not None
    assert admin_role is not None

    user_repository.add(
        make_user(
            role=user_role,
            email="regular@example.com",
        )
    )
    user_repository.add(
        make_user(
            role=admin_role,
            email="administrator@example.com",
        )
    )

    db_session.commit()

    result = user_repository.list_paginated(
        page=1,
        page_size=20,
        sort_options=SortOptions(field="role"),
        search=None,
        role=None,
        is_active=None,
    )

    assert [user.role.name for user in result.items] == [
        "Admin",
        "User",
    ]
