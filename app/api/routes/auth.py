from fastapi import APIRouter, Depends

from app.api.dependencies.use_cases import get_register_user
from app.api.schemas.auth import RegisterRequest, RegisterResponse
from app.application.use_cases.register_user import RegisterUser

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse)
def register(
    payload: RegisterRequest,
    use_case: RegisterUser = Depends(get_register_user),
):
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
