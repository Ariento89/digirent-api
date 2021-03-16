from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from digirent.api.middlewares import ChatManagerMiddleware
import digirent.core.config as config
from digirent.api.auth.router import router as auth_router
from digirent.api.me.router import router as me_router
from digirent.api.user.router import router as user_router
from digirent.api.amenity.router import router as amenity_router
from digirent.api.apartments.router import router as apartments_router
from digirent.api.apartment_applications.router import router as applications_router
from digirent.api.invites.router import router as invites_router
from digirent.api.signrequest.router import router as signerequest_router
from digirent.api.payments.router import router as payments_router
from digirent.api.invoices.router import router as invoice_router
from digirent.api.chat.router import router as chat_router
from digirent.api.blog.router import router as blog_router
from digirent.api.documents.router import router as documents_router
from digirent.api.notifications.router import router as notifications_router


def get_api_app():
    """
    Returns and configures a FastAPI application
    for api endpoints
    """

    api = FastAPI(title=config.PROJECT_NAME, root_path="/api")

    api.add_middleware(
        CORSMiddleware,
        allow_origins=list(config.ALLOWED_HOSTS),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    api.add_middleware(SessionMiddleware, secret_key=config.SECRET_KEY)
    api.add_middleware(ChatManagerMiddleware)

    api.include_router(auth_router, prefix="/auth", tags=["Authentication"])
    api.include_router(me_router, prefix="/me", tags=["Me"])
    api.include_router(user_router, prefix="/users", tags=["Users"])
    api.include_router(amenity_router, prefix="/amenities", tags=["Amenities"])
    api.include_router(apartments_router, prefix="/apartments", tags=["Apartments"])
    api.include_router(
        applications_router, prefix="/applications", tags=["Apartment Applications"]
    )
    api.include_router(invites_router, prefix="/invites", tags=["Invites"])
    api.include_router(
        signerequest_router, prefix="/signrequest", tags=["Signrequest Helpers"]
    )
    api.include_router(payments_router, prefix="/payments", tags=["Payments"])
    api.include_router(invoice_router, prefix="/invoices", tags=["Invoices"])
    api.include_router(chat_router, prefix="/chat", tags=["Chat"])
    api.include_router(blog_router, prefix="/blog", tags=["Blog"])
    api.include_router(documents_router, prefix="/documents", tags=["Documents"])
    app.include_router(
        notifications_router, prefix="/notifications", tags=["Notifications"]
    )
    return api


def get_app() -> FastAPI:
    """
    Construct main fastapi application and
    mount api application on path /api
    """
    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
    api_app = get_api_app()
    app.mount("/api", app=api_app)
    app.mount("/static", StaticFiles(directory=config.STATIC_PATH), name="static")
    return app


app: FastAPI = get_app()
