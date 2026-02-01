from abc import ABC
from typing import Callable

from asyncpg.exceptions import ForeignKeyViolationError
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from architectonics.core.models.base_model import BaseModel
from architectonics.infrastructure.entities.base_entity import BaseEntity
from architectonics.infrastructure.repositories.base_exceptions import (
    IntegrityErrorException,
    ObjectAlreadyExistsException,
    ObjectNotFoundException,
)


class BaseRepository(ABC):
    _entity: type[BaseEntity] = NotImplemented
    _session: Callable = NotImplemented
    _integrity_error: type[IntegrityError] = IntegrityError

    def get_session(self) -> AsyncSession:
        return self._session()

    @property
    def model_fields(self):
        return self._entity.__table__.columns

    async def create_model(
        self,
        model: BaseModel,
    ) -> BaseModel:

        entity: BaseEntity = self._entity.from_model(
            model=model,
        )

        async with self.get_session() as session:
            session.add(entity)

            try:
                await session.commit()
            except self._integrity_error as e:
                raise ObjectAlreadyExistsException(e)

            return entity.to_model()

    async def get_model_by_id(
        self,
        model_id: str,
    ) -> BaseModel | None:

        statement = select(
            self._entity,
        ).where(
            self._entity.id == model_id,
        )

        async with self.get_session() as session:

            result = await session.execute(
                statement=statement,
            )

            entity = result.scalars().first()

            if entity is None:
                return None

            return entity.to_model()

    async def update_model(
        self,
        model: BaseModel,
    ) -> BaseModel:

        updated_values = model.to_update_dict()

        update_statement = (
            update(
                self._entity,
            )
            .where(
                self._entity.id == model.id,
            )
            .values(
                **updated_values,
            )
        )

        async with self.get_session() as session:
            try:
                result = await session.execute(update_statement)

                await session.commit()
            except self._integrity_error as e:
                orig = getattr(e.orig, "__cause__", None)

                if isinstance(orig, ForeignKeyViolationError):
                    raise ObjectNotFoundException()

                raise IntegrityErrorException(e)

            return model

    async def delete_model(
        self,
        model_id: str,
    ) -> None:

        statement = delete(
            self._entity,
        ).where(
            self._entity.id == model_id,
        )

        async with self.get_session() as session:
            result = await session.execute(
                statement=statement,
            )

            if result.rowcount == 0:
                raise ObjectNotFoundException()

            await session.commit()

    async def get_models_list(
        self,
    ) -> list[BaseModel]:

        statement = select(
            self._entity,
        )

        async with self.get_session() as session:

            result = await session.execute(
                statement=statement,
            )

            models = result.scalars().all()

            return [model.to_model() for model in models]
