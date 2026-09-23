from app.application.errors import (
    AuthorizationError,
    AuthorizationReason,
    RoleAlreadyExist,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.authorization import can_set_role_level
from app.domain.entities.role import Role
from app.domain.entities.user import User


class CreateRole:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    def execute(
        self, actor: User, name: str, description: str | None, level: int
    ) -> Role:
        with self.uow:
            existing = self.uow.roles.get_by_name(name=name)
            if existing is not None:
                raise RoleAlreadyExist()
            if not can_set_role_level(actor, level):
                raise AuthorizationError(AuthorizationReason.CANNOT_SET_ROLE_LEVEL)

            role = Role(name=name, description=description, level=level)
            self.uow.roles.add(role)
            self.uow.commit()
            return role
