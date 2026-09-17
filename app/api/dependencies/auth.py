from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.dependencies.use_cases import get_current_user_use_case
from app.application.errors import InvalidAccessTokenError
from app.application.use_cases.get_current_user import GetCurrentUser
from app.application.use_cases.require_permission import RequirePermission
from app.domain.entities.user import User
from app.infrastructure.database.session import SessionFactory
from app.infrastructure.uow.sqlalchemy import SqlAlchemyUnitOfWork

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    use_case: GetCurrentUser = Depends(get_current_user_use_case),
) -> User:
    if credentials is None:
        raise InvalidAccessTokenError()
    user = use_case.execute(credentials.credentials)
    return user


def get_require_permission() -> RequirePermission:
    uow = SqlAlchemyUnitOfWork(SessionFactory)
    return RequirePermission(uow=uow)


def require_permission(permission_name: str):
    def dependency(
        user: User = Depends(get_current_user),
        use_case: RequirePermission = Depends(get_require_permission),
    ):
        use_case.execute(user, permission_name)

    return dependency
