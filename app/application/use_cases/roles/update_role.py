from typing import TypedDict
from uuid import UUID

from app.application.errors import (
    AuthorizationError,
    AuthorizationReason,
    ProtectedRoleModificationError,
    RoleAlreadyExist,
    RoleNotFoundError,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.authorization import (
    PROTECTED_ROLE_NAMES,
    can_manage_role,
    can_set_role_level,
)
from app.domain.entities.role import Role
from app.domain.entities.user import User


class RoleUpdates(TypedDict, total=False):
    name: str
    description: str | None
    level: int


class UpdateRole:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    def execute(self, actor: User, role_id: UUID, updates: RoleUpdates) -> Role:
        allowed_fields = {"name", "description", "level"}
        with self.uow:
            role = self.uow.roles.get_by_id(role_id)
            if role is None:
                raise RoleNotFoundError()
            if not can_manage_role(actor=actor, role=role):
                raise AuthorizationError(AuthorizationReason.CANNOT_MANAGE_ROLE)
            if role.name in PROTECTED_ROLE_NAMES and (
                "name" in updates or "level" in updates
            ):
                raise ProtectedRoleModificationError()
            if "level" in updates:
                level = updates["level"]
                if not can_set_role_level(actor=actor, level=level):
                    raise AuthorizationError(AuthorizationReason.CANNOT_SET_ROLE_LEVEL)
            if "name" in updates:
                existing = self.uow.roles.get_by_name(name=updates["name"])
                if existing is not None and existing.id != role.id:
                    raise RoleAlreadyExist()
            for field, value in updates.items():
                if field in allowed_fields:
                    setattr(role, field, value)
            self.uow.roles.update(role)
            self.uow.commit()
            return role
