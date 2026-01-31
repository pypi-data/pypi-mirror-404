from starlette.status import (
    HTTP_200_OK,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_422_UNPROCESSABLE_CONTENT,
)

from architectonics.core.models.base_model import BaseModel
from architectonics.core.result.service_result import ServiceResult
from architectonics.core.services.base_schemas import (
    BaseModelCreateSchema,
    BaseModelUpdateSchema,
)
from architectonics.core.validation.base_model_validation_errors import BaseModelValidationErrors
from architectonics.infrastructure.repositories.base_exceptions import (
    IntegrityErrorException,
    ObjectAlreadyExistsException,
    ObjectNotFoundException,
)
from architectonics.infrastructure.repositories.base_repository import BaseRepository


class BaseService:
    _repository: BaseRepository = NotImplemented

    async def get_models_list(
        self,
    ) -> ServiceResult[list[BaseModel], BaseModelValidationErrors]:

        models = await self._repository.get_models_list()

        return ServiceResult[list[BaseModel], BaseModelValidationErrors].success(models)

    """async def validate(self, model: BaseModel) -> BaseModelValidationErrors:

        errors = BaseModelValidationErrors()

        return errors

    async def create_model(
        self,
        model: BaseModel,
    ) -> ServiceResult[BaseModel, BaseModelValidationErrors]:

        model_errors = await self.validate(model)

        if model_errors.has_errors():
            return None, model_errors, HTTP_422_UNPROCESSABLE_CONTENT

        try:
            model = await self._repository.create_model(
                values=values,
            )
        except ObjectAlreadyExistsException:
            return None, "object_already_exist", HTTP_409_CONFLICT

        return model, None, HTTP_200_OK

    async def get_model(
        self,
        model_id: str,
    ) -> tuple[BaseModel | None, str | None, int]:

        try:
            model = await self._repository.get_model(
                model_id=model_id,
            )
        except ObjectNotFoundException:
            return None, "object_not_found", HTTP_404_NOT_FOUND

        return model, None, HTTP_200_OK

    async def update_model(
        self,
        model_id: str,
        update_schema: BaseModelUpdateSchema,
    ) -> tuple[BaseModel | None, str | dict[str, list[str]] | None, int]:

        schema_dict = update_schema.model_dump(by_alias=False)

        attrs, errors = await self._validate_values(**schema_dict)

        if errors:
            return None, errors, HTTP_422_UNPROCESSABLE_CONTENT

        try:
            model = await self._repository.update_model(
                model_id=model_id,
                values=attrs,
            )
        except IntegrityErrorException as e:
            return None, f"{e}", HTTP_404_NOT_FOUND
        except ObjectNotFoundException:
            return None, "object_not_found", HTTP_404_NOT_FOUND

        return model, None, HTTP_200_OK

    async def delete_model(
        self,
        model_id: str,
    ) -> tuple[None | str, str | dict[str, list[str]] | None, int]:

        _, errors, status_code = await self.get_model(
            model_id=model_id,
        )

        if errors:
            return None, errors, status_code

        await self._repository.delete_model(
            model_id=model_id,
        )

        return "object_deleted", None, HTTP_200_OK"""
