import dependency_injector.containers as containers
import dependency_injector.providers as providers
from digirent.core.services.file_service import FileService
from digirent.database.models import (
    Admin,
    Amenity,
    ApartmentApplication,
    BookingRequest,
    Landlord,
    Tenant,
)
from digirent.database.services.base import DBService
from digirent.database.services.user import UserService
from digirent.database.services.apartment import ApartmentService
from . import Application


class ServiceContainer(containers.DeclarativeContainer):
    user_service = providers.Singleton(UserService)
    admin_service = providers.Singleton(DBService, model_class=Admin)
    landlord_service = providers.Singleton(DBService, model_class=Landlord)
    tenant_service = providers.Singleton(DBService, model_class=Tenant)
    apartment_service = providers.Singleton(ApartmentService)
    amenity_service = providers.Singleton(DBService, model_class=Amenity)
    apartment_application_service = providers.Singleton(
        DBService, model_class=ApartmentApplication
    )
    booking_request_service = providers.Singleton(DBService, model_class=BookingRequest)
    file_service = providers.Singleton(FileService)


class ApplicationContainer(containers.DeclarativeContainer):
    app = providers.Singleton(
        Application,
        user_service=ServiceContainer.user_service,
        admin_service=ServiceContainer.admin_service,
        landlord_service=ServiceContainer.landlord_service,
        tenant_service=ServiceContainer.tenant_service,
        apartment_service=ServiceContainer.apartment_service,
        amenity_service=ServiceContainer.amenity_service,
        apartment_application_service=ServiceContainer.apartment_application_service,
        booking_request_service=ServiceContainer.booking_request_service,
        file_service=ServiceContainer.file_service,
    )
