from abc import ABC, abstractmethod
from typing import Generic, Tuple, TypeVar
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.infrastructure.database.base import BaseModel

DomainT = TypeVar("DomainT")
ModelT = TypeVar("ModelT", bound=BaseModel)


class SqlAlchemyRepository(Generic[DomainT, ModelT], ABC):
    model_type: type[ModelT]

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, entity_id: UUID) -> DomainT | None:
        model = self.session.scalar(
            self._base_query().where(self.model_type.id == entity_id)
        )
        if model is None:
            return None
        return self._to_domain(model)

    def _base_query(self) -> Select[Tuple[ModelT]]:
        return select(self.model_type)

    @abstractmethod
    def _to_domain(self, model: ModelT) -> DomainT: ...
