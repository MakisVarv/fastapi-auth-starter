from app.domain.entities.permission import Permission
from app.domain.entities.role import Role


def test_role_has_permission_returns_true_when_permission_exists() -> None:
    role = Role(
        name="Support",
        level=40,
        permissions=[
            Permission(name="user.read"),
            Permission(name="user.update"),
        ],
    )

    assert role.has_permission("user.read") is True


def test_role_has_permission_returns_false_when_permission_is_missing() -> None:
    role = Role(
        name="Support",
        level=40,
        permissions=[
            Permission(name="user.read"),
        ],
    )

    assert role.has_permission("user.delete") is False


def test_role_has_permission_returns_false_when_role_has_no_permissions() -> None:
    role = Role(
        name="Support",
        level=40,
    )

    assert role.has_permission("user.read") is False
