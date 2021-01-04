from datetime import datetime
from typing import List, Optional
from digirent.api.schema import BaseSchema, OrmSchema


class TagSchema(BaseSchema):
    name: str
    updated_at: Optional[datetime]
    created_at: Optional[datetime]

    class Config:
        orm_mode = True


class BlogPostBaseSchema(BaseSchema):
    title: str
    content: str


class BlogPostCreateSchema(BlogPostBaseSchema):
    tags: List[str]


class BlogPostUpdateSchema(BlogPostCreateSchema):
    pass


class BlogPostSchema(BlogPostBaseSchema, OrmSchema):
    tags: List[TagSchema]
