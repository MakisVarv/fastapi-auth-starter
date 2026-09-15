from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.models import PermissionModel, RoleModel

PERMISSIONS: list[dict[str, str]] = [
    # Users
    {"name": "user.read", "description": "Read user information"},
    {"name": "user.create", "description": "Create users"},
    {"name": "user.update", "description": "Update users"},
    {"name": "user.delete", "description": "Delete users"},
    {"name": "user.change_role", "description": "Change a user's role"},
    # Roles
    {"name": "role.read", "description": "Read roles"},
    {"name": "role.create", "description": "Create roles"},
    {"name": "role.update", "description": "Update roles"},
    {"name": "role.delete", "description": "Delete roles"},
    {
        "name": "role.assign_permission",
        "description": "Assign or remove permissions from roles",
    },
    # Permissions
    {"name": "permission.read", "description": "Read permissions"},
    # Dashboard
    {"name": "dashboard.read", "description": "View dashboard"},
]
ROLES: list[dict[str, str | int]] = [
    {"name": "Admin", "description": "Full system administrator", "level": 100},
    {"name": "User", "description": "Standard system user", "level": 10},
]

ROLE_PERMISSIONS: dict[str, list[str]] = {
    "Admin": [permission["name"] for permission in PERMISSIONS]
}


def seed_permissions(session: Session) -> None:

    print("Starting permission seed...")

    for permission in PERMISSIONS:

        print(permission["name"])

        existing = session.scalar(
            select(PermissionModel).where(PermissionModel.name == permission["name"])
        )

        if existing:
            print(f"{permission['name']} already exists")
            continue

        print(f"Adding {permission['name']}")

        session.add(
            PermissionModel(
                id=uuid4(),
                name=permission["name"],
                description=permission["description"],
            )
        )

    session.commit()

    print("Commit completed.")


def seed_roles(session: Session) -> None:
    print("Starting roles seed")
    for role in ROLES:

        print(role["name"])

        existing = session.scalar(
            select(RoleModel).where(RoleModel.name == role["name"])
        )

        if existing:
            print(f"{role['name']} already exists")
            continue

        print(f"Adding {role['name']}")

        session.add(
            RoleModel(
                id=uuid4(),
                name=role["name"],
                description=role["description"],
                level=role["level"],
            )
        )

    session.commit()

    print("Commit completed.")


def seed_role_permissions(session: Session) -> None:
    print("Starting role-permission seed...")

    for role_name, permission_names in ROLE_PERMISSIONS.items():
        role = session.scalar(select(RoleModel).where(RoleModel.name == role_name))

        if role is None:
            raise RuntimeError(f"Role '{role_name}' does not exist.")

        existing_permissions = {permission.name for permission in role.permissions}

        for permission_name in permission_names:
            if permission_name in existing_permissions:
                print(f"{role_name} already has {permission_name}")
                continue

            permission = session.scalar(
                select(PermissionModel).where(PermissionModel.name == permission_name)
            )

            if permission is None:
                raise RuntimeError(f"Permission '{permission_name}' does not exist.")

            print(f"Assigning {permission_name} to {role_name}")
            role.permissions.append(permission)

    session.commit()
    print("Role-permission commit completed.")


if __name__ == "__main__":

    from app.infrastructure.database.session import SessionFactory

    with SessionFactory() as session:
        seed_permissions(session)
        seed_roles(session)
        seed_role_permissions(session)
