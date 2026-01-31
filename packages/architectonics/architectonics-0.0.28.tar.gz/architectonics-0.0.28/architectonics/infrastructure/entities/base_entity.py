import uuid

from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import as_declarative

from architectonics.common.utils.utils import get_current_datetime
from architectonics.core.models.base_model import BaseModel


@as_declarative()
class BaseEntity:
    __abstract__ = True

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    created_at = Column(
        DateTime,
        default=get_current_datetime,
    )

    updated_at = Column(
        DateTime,
        default=get_current_datetime,
        onupdate=get_current_datetime,
    )

    PK_FIELD = "id"

    def to_model(self) -> BaseModel:
        raise NotImplementedError()
