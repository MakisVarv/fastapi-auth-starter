from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.dependencies.use_cases import get_current_user_use_case
from app.application.errors import InvalidAccessTokenError
from app.application.use_cases.get_current_user import GetCurrentUser
from app.domain.entities.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    use_case: GetCurrentUser = Depends(get_current_user_use_case),
) -> User:
    if credentials is None:
        raise InvalidAccessTokenError()
    user = use_case.execute(credentials.credentials)
    return user
