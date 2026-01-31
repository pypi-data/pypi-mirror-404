from dataclasses import dataclass, fields


@dataclass
class BaseModelValidationErrors:

    def has_errors(self) -> bool:
        for f in fields(self):
            value = getattr(self, f.name)

            if isinstance(value, list) and len(value) > 0:
                return True

        return False
