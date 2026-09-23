from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies.auth import require_permission
from app.api.dependencies.roles import get_list_roles, get_role_use_case
from app.api.schemas.role import RoleResponse
from app.application.use_cases.roles.get_role import GetRole
from app.application.use_cases.roles.list_roles import ListRoles

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
