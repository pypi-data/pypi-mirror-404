from __future__ import annotations

from typing import Generic, TypeVar

from architectonics.core.result.error_message import ErrorMessage

TValue = TypeVar("TValue")
TValidationErrors = TypeVar("TValidationErrors")


class ServiceResult(
    Generic[
        TValue,
        TValidationErrors,
    ],
):
    __slots__ = (
        "_value",
        "_validation_errors",
        "_error_message",
    )

    def __init__(
        self,
        value: TValue | None = None,
        validation_errors: TValidationErrors | None = None,
        error_message: ErrorMessage | None = None,
    ) -> None:
        self._value = value
        self._validation_errors = validation_errors
        self._error_message = error_message

    @property
    def value(self) -> TValue | None:
        return self._value

    @property
    def validation_errors(self) -> TValidationErrors | None:
        return self._validation_errors

    @property
    def error_message(self) -> ErrorMessage | None:
        return self._error_message

    @property
    def is_validation_error(self) -> bool:
        return self._validation_errors is not None

    @property
    def is_success(self) -> bool:
        return self._value is not None and self._validation_errors is None and self._error_message is None

    @classmethod
    def success(cls, value: TValue) -> ServiceResult[TValue, TValidationErrors]:
        return cls(
            value=value,
        )

    @classmethod
    def validation_failure(cls, validation_errors: TValidationErrors) -> ServiceResult[TValue, TValidationErrors]:
        return cls(
            validation_errors=validation_errors,
        )

    @classmethod
    def failure(cls, error_message: str) -> ServiceResult[TValue, TValidationErrors]:
        return cls(
            error_message=ErrorMessage(
                message=error_message,
            ),
        )
