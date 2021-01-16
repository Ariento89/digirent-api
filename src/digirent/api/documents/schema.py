from digirent.api.schema import BaseSchema


class FileUploadResponseSchema(BaseSchema):
    status: str
    message: str
