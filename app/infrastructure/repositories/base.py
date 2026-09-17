from abc import ABC, abstractmethod
from typing import Generic, Tuple, TypeVar
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.application.common.pagination import Page
from app.infrastructure.database.base import BaseModel
from app.infrastructure.query.pagination import Pagination

DomainT = TypeVar("DomainT")
ModelT = TypeVar("ModelT", bound=BaseModel)


class SqlAlchemyRepository(Generic[DomainT, ModelT], ABC):
    model_type: type[ModelT]

    def __init__(self, session: Session) -> None:
        self.session = session

    def _paginate(
        self,
        statement: Select[tuple[ModelT]],
        count_statement: Select[tuple[int]],
        *,
        page: int,
        page_size: int,
    ) -> Page[DomainT]:
        models, metadata = Pagination.paginate(
            session=self.session,
            statement=statement,
            count_statement=count_statement,
            page=page,
            page_size=page_size,
        )
        items = [self._to_domain(model) for model in models]
        return Page(
            items=items,
            **metadata,
        )

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
