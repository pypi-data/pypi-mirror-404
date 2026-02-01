from dataclasses import dataclass

from architectonics.core.models.base_model import BaseModel


@dataclass
class DeletedModel(BaseModel):
    id: str
