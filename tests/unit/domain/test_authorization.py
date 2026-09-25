from app.domain.authorization import (
    MAX_ROLE_LEVEL,
    can_assign_role,
    can_manage_role,
    can_manage_user,
    can_set_role_level,
)
from app.domain.entities.role import Role
from app.domain.entities.user import User


def make_user(
    *,
    role_level: int,
    role_name: str = "User",
) -> User:
    return User(
        first_name="Test",
        last_name="User",
        email="test@example.com",
        password_hash="hash",
        role=Role(
            name=role_name,
            level=role_level,
        ),
    )


def test_max_level_user_can_manage_any_user() -> None:
    actor = make_user(
        role_level=MAX_ROLE_LEVEL,
        role_name="Admin",
    )
    target = make_user(
        role_level=MAX_ROLE_LEVEL,
        role_name="Admin",
    )

    assert can_manage_user(actor, target) is True


def test_user_can_manage_lower_level_user() -> None:
    actor = make_user(role_level=80)
    target = make_user(role_level=40)

    assert can_manage_user(actor, target) is True


def test_user_cannot_manage_same_level_user() -> None:
    actor = make_user(role_level=50)
    target = make_user(role_level=50)

    assert can_manage_user(actor, target) is False


def test_user_cannot_manage_higher_level_user() -> None:
    actor = make_user(role_level=40)
    target = make_user(role_level=80)

    assert can_manage_user(actor, target) is False


def test_max_level_user_can_assign_any_role() -> None:
    actor = make_user(
        role_level=MAX_ROLE_LEVEL,
        role_name="Admin",
    )
    role = Role(
        name="Admin",
        level=MAX_ROLE_LEVEL,
    )

    assert can_assign_role(actor, role) is True


def test_user_can_assign_lower_level_role() -> None:
    actor = make_user(role_level=80)
    role = Role(
        name="Support",
        level=40,
    )

    assert can_assign_role(actor, role) is True


def test_user_cannot_assign_same_level_role() -> None:
    actor = make_user(role_level=50)
    role = Role(
        name="Peer",
        level=50,
    )

    assert can_assign_role(actor, role) is False


def test_user_cannot_assign_higher_level_role() -> None:
    actor = make_user(role_level=40)
    role = Role(
        name="Manager",
        level=80,
    )

    assert can_assign_role(actor, role) is False


def test_max_level_user_can_manage_any_role() -> None:
    actor = make_user(
        role_level=MAX_ROLE_LEVEL,
        role_name="Admin",
    )
    role = Role(
        name="Admin",
        level=MAX_ROLE_LEVEL,
    )

    assert can_manage_role(actor, role) is True


def test_user_can_manage_lower_level_role() -> None:
    actor = make_user(role_level=80)
    role = Role(
        name="Support",
        level=40,
    )

    assert can_manage_role(actor, role) is True


def test_user_cannot_manage_same_level_role() -> None:
    actor = make_user(role_level=50)
    role = Role(
        name="Peer",
        level=50,
    )

    assert can_manage_role(actor, role) is False


def test_user_cannot_manage_higher_level_role() -> None:
    actor = make_user(role_level=40)
    role = Role(
        name="Manager",
        level=80,
    )

    assert can_manage_role(actor, role) is False


def test_max_level_user_can_set_any_role_level() -> None:
    actor = make_user(
        role_level=MAX_ROLE_LEVEL,
        role_name="Admin",
    )

    assert (
        can_set_role_level(
            actor,
            MAX_ROLE_LEVEL,
        )
        is True
    )


def test_user_can_set_lower_role_level() -> None:
    actor = make_user(role_level=80)

    assert (
        can_set_role_level(
            actor,
            40,
        )
        is True
    )


def test_user_cannot_set_same_role_level() -> None:
    actor = make_user(role_level=50)

    assert (
        can_set_role_level(
            actor,
            50,
        )
        is False
    )


def test_user_cannot_set_higher_role_level() -> None:
    actor = make_user(role_level=40)

    assert (
        can_set_role_level(
            actor,
            80,
        )
        is False
    )
