from fastapi import APIRouter, Cookie, Depends, Response

from app.api.dependencies.auth import (
    get_current_user,
    get_login_user,
    get_logout_session,
    get_refresh_session,
    get_register_user,
    get_update_current_user,
)
from app.api.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    UpdateMeRequest,
)
from app.api.schemas.common import MessageResponse
from app.api.schemas.user import UserResponse
from app.application.errors import InvalidRefreshTokenError
from app.application.use_cases.login_user import LoginUser
from app.application.use_cases.logout_session import LogoutSession
from app.application.use_cases.refresh_session import RefreshSession
from app.application.use_cases.register_user import RegisterUser
from app.application.use_cases.update_current_user import UpdateCurrentUser
from app.domain.entities.user import User
from app.infrastructure.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
def register(
    payload: RegisterRequest,
    use_case: RegisterUser = Depends(get_register_user),
) -> UserResponse:

    user = use_case.execute(
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=str(payload.email),
        password=payload.password,
        phone=payload.phone,
    )
    return UserResponse.model_validate(user)


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    response: Response,
    use_case: LoginUser = Depends(get_login_user),
) -> LoginResponse:

    result = use_case.execute(
        email=str(payload.email),
        password=payload.password,
    )

    response.set_cookie(
        key="refresh_token",
        value=result.refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRES_DAYS * 24 * 60 * 60,
    )

    return LoginResponse(
        access_token=result.access_token, user=UserResponse.model_validate(result.user)
    )


@router.post("/logout", response_model=MessageResponse)
def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    use_case: LogoutSession = Depends(get_logout_session),
) -> MessageResponse:

    if refresh_token is not None:
        try:
            use_case.execute(refresh_token=refresh_token)
        except InvalidRefreshTokenError:
            pass

    response.delete_cookie("refresh_token")

    return MessageResponse(message="Logged out successfully.")


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    use_case: RefreshSession = Depends(get_refresh_session),
) -> AccessTokenResponse:

    if refresh_token is None:
        raise InvalidRefreshTokenError()

    result = use_case.execute(refresh_token=refresh_token)

    response.set_cookie(
        key="refresh_token",
        value=result.refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRES_DAYS * 24 * 60 * 60,
    )

    return AccessTokenResponse(
        access_token=result.access_token,
    )


@router.get("/me", response_model=UserResponse)
def me(
    response: Response, current_user: User = Depends(get_current_user)
) -> UserResponse:

    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
def update_me(
    payload: UpdateMeRequest,
    current_user: User = Depends(get_current_user),
    use_case: UpdateCurrentUser = Depends(get_update_current_user),
) -> UserResponse:
    updates = payload.model_dump(exclude_unset=True)

    new_user = use_case.execute(user_id=current_user.id, updates=updates)

    return UserResponse.model_validate(new_user)
