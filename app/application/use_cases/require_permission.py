from app.application.errors import PermissionDeniedError
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.entities.user import User


class RequirePermission:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    def execute(self, user: User, permission_name: str) -> None:
        if not user.role.has_permission(permission_name):
            raise PermissionDeniedError()
