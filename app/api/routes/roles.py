from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies.auth import get_current_user, require_permission
from app.api.dependencies.roles import (
    CreateRole,
    get_create_role,
    get_list_roles,
    get_role_use_case,
)
from app.api.schemas.role import CreateRoleRequest, RoleResponse
from app.application.use_cases.roles.get_role import GetRole
from app.application.use_cases.roles.list_roles import ListRoles
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
