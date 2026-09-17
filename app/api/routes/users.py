from fastapi import APIRouter

from app.api.schemas.common import PaginatedResponse
from app.api.schemas.user import UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "",
    response_model=PaginatedResponse[UserResponse],
)
def list_users():
    