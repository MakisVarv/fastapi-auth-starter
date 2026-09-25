from uuid import uuid4

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.models import PermissionModel, RoleModel
from app.infrastructure.models.user import UserModel
from app.infrastructure.security.password_hasher import Argon2PasswordHasher


class SeedSettings(BaseSettings):
    ADMIN_EMAIL: str | None = None
    ADMIN_PASSWORD: str | None = None
    ADMIN_FIRST_NAME: str = "System"
    ADMIN_LAST_NAME: str = "Admin"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


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


def seed_admin(session: Session) -> None:
    print("Starting admin seed...")
    seed_settings = SeedSettings()

    if not seed_settings.ADMIN_EMAIL or not seed_settings.ADMIN_PASSWORD:
        raise RuntimeError("ADMIN_EMAIL and ADMIN_PASSWORD must be configured.")

    email = seed_settings.ADMIN_EMAIL.strip().lower()
    password = seed_settings.ADMIN_PASSWORD
    first_name = seed_settings.ADMIN_FIRST_NAME
    last_name = seed_settings.ADMIN_LAST_NAME

    if not email:
        raise RuntimeError("ADMIN_EMAIL must not be empty.")

    if len(password) < 8:
        raise RuntimeError("ADMIN_PASSWORD must be at least 8 characters.")
    existing = session.scalar(select(UserModel).where(UserModel.email == email))

    admin_role = session.scalar(select(RoleModel).where(RoleModel.name == "Admin"))
    if admin_role is None:
        raise RuntimeError("Admin role does not exist.")

    if existing:
        if existing.role_id != admin_role.id:
            existing.role_id = admin_role.id
            session.commit()
            print("Existing user promoted to Admin.")
        else:
            print("Admin user already exists.")

        return

    password_hasher = Argon2PasswordHasher()
    password_hash = password_hasher.hash(password)
    admin = UserModel(
        id=uuid4(),
        first_name=first_name,
        last_name=last_name,
        email=email,
        password_hash=password_hash,
        role_id=admin_role.id,
    )
    session.add(admin)
    session.commit()
    print("Admin user created.")


if __name__ == "__main__":

    from app.infrastructure.database.session import SessionFactory

    with SessionFactory() as session:
        seed_permissions(session)
        seed_roles(session)
        seed_role_permissions(session)
        seed_admin(session)
