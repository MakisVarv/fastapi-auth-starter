from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.dependencies.auth import get_current_user, require_permission
from app.api.dependencies.roles import (
    get_create_role,
    get_delete_role,
    get_list_roles,
    get_role_use_case,
    get_update_role,
)
from app.api.schemas.role import CreateRoleRequest, RoleResponse, UpdateRoleRequest
from app.application.use_cases.roles.create_role import CreateRole
from app.application.use_cases.roles.delete_role import DeleteRole
from app.application.use_cases.roles.get_role import GetRole
from app.application.use_cases.roles.list_roles import ListRoles
from app.application.use_cases.roles.update_role import RoleUpdates, UpdateRole
from app.domain.entities.user import User

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get(
    "",
    response_model=list[RoleResponse],
    dependencies=[Depends(require_permission("role.read"))],
)
def list_roles(
    use_case: ListRoles = Depends(get_list_roles),
) -> list[RoleResponse]:
    roles = use_case.execute()

    return [RoleResponse.model_validate(role) for role in roles]


@router.get(
    "/{role_id}",
    response_model=RoleResponse,
    dependencies=[Depends(require_permission("role.read"))],
)
def get_role(
    role_id: UUID, use_case: GetRole = Depends(get_role_use_case)
) -> RoleResponse:
    role = use_case.execute(role_id)
    return RoleResponse.model_validate(role)


@router.post(
    "",
    status_code=201,
    response_model=RoleResponse,
    dependencies=[Depends(require_permission("role.create"))],
)
def create_role(
    payload: CreateRoleRequest,
    current_user: User = Depends(get_current_user),
    use_case: CreateRole = Depends(get_create_role),
) -> RoleResponse:
    role = use_case.execute(
        actor=current_user,
        name=payload.name,
        description=payload.description,
        level=payload.level,
    )
    return RoleResponse.model_validate(role)


@router.patch(
    "/{role_id}",
    response_model=RoleResponse,
    dependencies=[Depends(require_permission("role.update"))],
)
def update_role(
    role_id: UUID,
    payload: UpdateRoleRequest,
    current_user: User = Depends(get_current_user),
    use_case: UpdateRole = Depends(get_update_role),
) -> RoleResponse:
    updates = cast(
        RoleUpdates,
        payload.model_dump(exclude_unset=True),
    )
    role = use_case.execute(role_id=role_id, actor=current_user, updates=updates)
    return RoleResponse.model_validate(role)


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("role.delete"))],
)
def delete_user(
    role_id: UUID,
    current_user: User = Depends(get_current_user),
    use_case: DeleteRole = Depends(get_delete_role),
) -> None:
    use_case.execute(actor=current_user, role_id=role_id)
