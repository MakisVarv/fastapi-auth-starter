import sys

from app.application.use_cases.permissions.prune_permission import PrunePermission
from app.infrastructure.database.session import SessionFactory
from app.infrastructure.uow.sqlalchemy import SqlAlchemyUnitOfWork

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python -m scripts.prune_permission <permission_name>")

    permission_name = sys.argv[1]

    uow = SqlAlchemyUnitOfWork(SessionFactory)

    PrunePermission(uow).execute(permission_name)

    print(f"Pruned permission: {permission_name}")
