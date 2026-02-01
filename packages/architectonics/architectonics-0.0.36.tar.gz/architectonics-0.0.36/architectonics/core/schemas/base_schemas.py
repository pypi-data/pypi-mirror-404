from pydantic import BaseModel, Field


class ObjectNotFoundResponseSchema(BaseModel):
    detail: str = Field()


class ObjectAlreadyExistsResponseSchema(BaseModel):
    detail: str = Field()


class ObjectDeletedResponseSchema(BaseModel):
    detail: str = Field()


class NotImplementedResponseSchema(BaseModel):
    detail: str = Field()


class UnauthorizedResponseSchema(BaseModel):
    detail: str = Field()
