import dependency_injector.containers as containers
import dependency_injector.providers as providers
from digirent.core.services.auth import AuthService
from digirent.core.services.user import UserService
from . import Application


class ServiceContainer(containers.DeclarativeContainer):
    user_service = providers.Singleton(UserService)
    auth_service = providers.Singleton(AuthService, user_service=user_service)


class ApplicationContainer(containers.DeclarativeContainer):
    app = providers.Singleton(
        Application,
        auth_service=ServiceContainer.auth_service,
        user_service=ServiceContainer.user_service,
    )
