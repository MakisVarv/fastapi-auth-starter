from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from app.api.dependencies.use_cases import get_list_users
from app.api.query.sorting import parse_sort
from app.api.schemas.common import PaginatedResponse
from app.api.schemas.user import UserListParams, UserResponse
from app.application.use_cases.list_users import ListUsers

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "",
    response_model=PaginatedResponse[UserResponse],
)
def list_users(
    response: Response,
    payload: Annotated[UserListParams, Query()],
    use_case: ListUsers = Depends(get_list_users),
) -> PaginatedResponse[UserResponse]:
    sort_options = parse_sort(payload.sort)
    users = use_case.execute(
        page=payload.page, page_size=payload.page_size, sort_options=sort_options
    )
    return PaginatedResponse[UserResponse].model_validate(users)
