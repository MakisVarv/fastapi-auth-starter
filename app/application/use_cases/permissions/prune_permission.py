from app.application.common.permissions import PERMISSIONS
from app.application.ports.unit_of_work import UnitOfWork


class PrunePermission:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    def execute(self, permission_name: str) -> None:
        with self.uow:
            configured_names = {permission["name"] for permission in PERMISSIONS}

            if permission_name in configured_names:
                raise ValueError(
                    f"Permission '{permission_name}' is still registered and cannot be pruned."
                )

            permission = self.uow.permissions.get_by_name(permission_name)

            if permission is None:
                raise ValueError(f"Permission '{permission_name}' does not exist.")
            roles = self.uow.roles.list_all()

            for role in roles:
                assigned_permission = next(
                    (
                        existing
                        for existing in role.permissions
                        if existing.id == permission.id
                    ),
                    None,
                )

                if assigned_permission is None:
                    continue

                role.permissions.remove(assigned_permission)

                self.uow.roles.remove_permission(
                    role=role,
                    permission=permission,
                )
            self.uow.permissions.delete(permission)
            self.uow.commit()
