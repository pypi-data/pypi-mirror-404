from architectonics.common.enums.step_type import StepType
from pydantic import BaseModel


class StepModelContract(BaseModel):
    id: str
    title: str | None
    icon: str | None
    is_publish: bool
    step_type: StepType
