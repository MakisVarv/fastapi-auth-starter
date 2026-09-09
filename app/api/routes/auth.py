from fastapi import APIRouter, Depends

from app.api.dependencies.use_cases import get_login_user, get_register_user
from app.api.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
)
from app.application.use_cases.login_user import LoginUser
from app.application.use_cases.register_user import RegisterUser
from app.application.errors import (
    InactiveUserError,
    InvalidCredentialsError,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse)
def register(
    payload: RegisterRequest,
    use_case: RegisterUser = Depends(get_register_user),
) -> RegisterResponse:
    user = use_case.execute(
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=str(payload.email),
        password=payload.password,
    )

    return RegisterResponse(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        is_active=user.is_active,
    )


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    use_case: LoginUser = Depends(get_login_user),
) -> LoginResponse:
    access_token = use_case.execute(
        email=str(payload.email),
        password=payload.password,
    )

    return LoginResponse(access_token=access_token)
