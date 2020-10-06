from ..schema import BaseSchema, OrmSchema


class BaseAmenitySchema(BaseSchema):
    title: str


class AmenityCreateSchema(BaseAmenitySchema):
    pass


class AmenitySchema(OrmSchema, BaseAmenitySchema):
    pass
