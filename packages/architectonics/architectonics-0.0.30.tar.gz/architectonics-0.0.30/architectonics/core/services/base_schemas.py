from pydantic import BaseModel


class BaseModelCreateSchema(BaseModel):
    pass


class BaseModelCreateErrorsSchema(BaseModel):
    pass


class BaseModelGetSchema(BaseModel):
    pass


class BaseModelUpdateSchema(BaseModel):
    pass


class BaseModelUpdateErrorsSchema(BaseModel):
    pass
