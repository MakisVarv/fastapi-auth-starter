from enum import Enum

from app.domain.entities.role import Role
from app.domain.entities.user import User

MAX_ROLE_LEVEL = 100
PROTECTED_ROLE_NAMES = {"Admin", "User"}


def can_manage_user(actor: User, target: User) -> bool:
    if actor.role.level == MAX_ROLE_LEVEL:
        return True
    if actor.role.level <= target.role.level:
        return False
    return True


def can_assign_role(actor: User, role: Role) -> bool:
    if actor.role.level == MAX_ROLE_LEVEL:
        return True

    if actor.role.level <= role.level:
        return False
    return True
