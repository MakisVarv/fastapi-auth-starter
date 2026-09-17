from app.application.errors import PermissionDeniedError, RoleNotFoundError
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.entities.user import User


class RequirePermission:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    def execute(self, user: User, permission_name: str) -> None:
        with self.uow:
            role = self.uow.roles.get_by_id(user.role_id)
            if role is None:
                raise RoleNotFoundError
            has_permission = role.has_permission(permission_name=permission_name)
            if not has_permission:
                raise PermissionDeniedError
