from typing import Any, List, Optional, Union
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime


def to_camel_case(text: str):
    """Converts a given text to camel case

    Arguments:
        text {str} -- text to be converted
    """
    splitted_text: List[str] = text.split("_")
    return splitted_text[0].lower() + "".join(
        word.capitalize() for word in splitted_text[1:]
    )


class BaseSchema(BaseModel):
    class Config:
        extra = "forbid"
        alias_generator = to_camel_case
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
