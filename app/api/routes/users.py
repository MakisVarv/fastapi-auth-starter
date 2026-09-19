from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.dependencies.auth import require_permission
from app.api.dependencies.use_cases import get_list_users, get_user_case
from app.api.query.sorting import parse_sort
from app.api.schemas.common import PaginatedResponse, PaginationResponse
from app.api.schemas.user import UserListParams, UserResponse
from app.application.use_cases.get_user import GetUser
from app.application.use_cases.list_users import ListUsers

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "",
    response_model=PaginatedResponse[UserResponse],
    dependencies=[Depends(require_permission("user.read"))],
)
def list_users(
    payload: Annotated[UserListParams, Query()],
    use_case: ListUsers = Depends(get_list_users),
) -> PaginatedResponse[UserResponse]:
    sort_options = parse_sort(payload.sort)
    users = use_case.execute(
        page=payload.page,
        page_size=payload.page_size,
        sort_options=sort_options,
        is_active=payload.is_active,
        role=payload.role,
        search=payload.search,
    )
    items = [UserResponse.model_validate(user) for user in users.items]
    pagination = PaginationResponse.model_validate(users)
    return PaginatedResponse[UserResponse](items=items, pagination=pagination)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(require_permission("user.read"))],
)
def get_user(user_id: UUID, use_case: GetUser = Depends(get_user_case)) -> UserResponse:
    user = use_case.execute(user_id)
    return UserResponse.model_validate(user)
