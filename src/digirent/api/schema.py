import inflection
from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime


class BaseSchema(BaseModel):
    class Config:
        extra = "forbid"
        alias_generator = inflection.camelize
        allow_population_by_field_name = True


class IdSchema(BaseSchema):
    id: UUID


class OrmSchema(IdSchema):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class BasePaginationSchema(BaseSchema):
    page: int
    page_size: int
    count: int
