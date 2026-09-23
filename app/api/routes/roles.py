from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies.auth import require_permission
from app.api.dependencies.roles import GetRole, get_list_roles, get_role
from app.api.schemas.role import RoleResponse
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
def get_user(role_id: UUID, use_case: GetRole = Depends(get_role)) -> RoleResponse:
    user = use_case.execute(role_id)
    return RoleResponse.model_validate(user)
