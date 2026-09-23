from fastapi import APIRouter, Depends

from app.api.dependencies.auth import require_permission
from app.api.dependencies.roles import get_list_roles
from app.api.schemas.role import RoleResponse
from app.application.use_cases.roles.list_roles import ListRoles

router = APIRouter(prefix="/roles", tags=["users"])


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
