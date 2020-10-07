from digirent.core.services.file_service import FileService
from digirent.database.services.user import UserService
from digirent.database.models import (
    Admin,
    Amenity,
    Apartment,
    ApartmentApplication,
    Landlord,
    Tenant,
)
from digirent.database.services.base import DBService


class ApplicationBase:
    def __init__(
        self,
        user_service: UserService,
        landlord_service: DBService[Landlord],
        tenant_service: DBService[Tenant],
        apartment_service: DBService[Apartment],
        amenity_service: DBService[Amenity],
        admin_service: DBService[Admin],
        apartment_application_service: DBService[ApartmentApplication],
        file_service: FileService,
    ) -> None:
        self.user_service: UserService = user_service
        self.admin_service = admin_service
        self.landlord_service = landlord_service
        self.tenant_service = tenant_service
        self.apartment_service = apartment_service
        self.amenity_service = amenity_service
        self.file_service = file_service
        self.apartment_application_service = apartment_application_service
