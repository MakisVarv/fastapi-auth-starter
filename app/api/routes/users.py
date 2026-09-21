from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.dependencies.auth import (
    get_current_user,
    require_permission,
)
from app.api.dependencies.users import (
    get_change_status,
    get_create_user,
    get_list_users,
    get_update_user,
    get_user_use_case,
)
from app.api.query.sorting import parse_sort
from app.api.schemas.common import PaginatedResponse, PaginationResponse
from app.api.schemas.user import (
    ChangeRoleRequest,
    CreateUserRequest,
    UpdateUserRequest,
    UserListParams,
    UserResponse,
    UserStatusRequest,
)
from app.application.use_cases.users.change_user_role import ChangeUserRole
from app.application.use_cases.users.change_user_status import ChangeUserStatus
from app.application.use_cases.users.create_user import CreateUser
from app.application.use_cases.users.get_user import GetUser
from app.application.use_cases.users.list_users import ListUsers
from app.application.use_cases.users.update_user import UpdateUser
from app.domain.entities.user import User

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
def get_user(
    user_id: UUID, use_case: GetUser = Depends(get_user_use_case)
) -> UserResponse:
    user = use_case.execute(user_id)
    return UserResponse.model_validate(user)


@router.post(
    "",
    status_code=201,
    response_model=UserResponse,
    dependencies=[Depends(require_permission("user.create"))],
)
def create_user(
    payload: CreateUserRequest,
    current_user: User = Depends(get_current_user),
    use_case: CreateUser = Depends(get_create_user),
) -> UserResponse:

    user = use_case.execute(
        actor=current_user,
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=str(payload.email),
        password=payload.password,
        phone=payload.phone,
        role_id=payload.role_id,
    )
    return UserResponse.model_validate(user)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(require_permission("user.update"))],
)
def update_user(
    payload: UpdateUserRequest,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    use_case: UpdateUser = Depends(get_update_user),
) -> UserResponse:
    updates = payload.model_dump(exclude_unset=True)
    user = use_case.execute(actor=current_user, user_id=user_id, updates=updates)
    return UserResponse.model_validate(user)


@router.patch(
    "/{user_id}/status",
    response_model=UserResponse,
    dependencies=[Depends(require_permission("user.update"))],
)
def change_user_status(
    payload: UserStatusRequest,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    use_case: ChangeUserStatus = Depends(get_change_status),
) -> UserResponse:
    user = use_case.execute(
        actor=current_user, user_id=user_id, is_active=payload.is_active
    )
    return UserResponse.model_validate(user)


@router.patch(
    "/{user_id}/role",
    response_model=UserResponse,
    dependencies=[Depends(require_permission("user.change_role"))],
)
def change_user_role(
    payload: ChangeRoleRequest,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    use_case: ChangeUserRole = Depends(get_change_status),
) -> UserResponse:
    user = use_case.execute(
        actor=current_user, user_id=user_id, role_id=payload.role_id
    )
    return UserResponse.model_validate(user)
