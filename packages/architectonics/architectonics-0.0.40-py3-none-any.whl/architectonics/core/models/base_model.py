from dataclasses import asdict, dataclass, field
from datetime import datetime
import uuid


@dataclass(
    kw_only=True,
)
class BaseModel:
    id: str = field(
        default_factory=lambda: str(uuid.uuid4()),
    )

    created_at: datetime = field(
        default_factory=datetime.utcnow,
    )

    updated_at: datetime = field(
        default_factory=datetime.utcnow,
    )

    def to_update_dict(self) -> dict[str, any]:
        now = datetime.utcnow()

        values = {k: v for k, v in asdict(self).items() if k not in {"id", "created_at"} and v is not None}

        values["updated_at"] = now
        self.updated_at = now

        return values
