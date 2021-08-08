from fastapi import APIRouter
from digirent.api.auth import auth_router, admin_auth_router
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


def get_normal_router() -> APIRouter:
    """
    Returns non admin routers
    """
    router = APIRouter()
    router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
    router.include_router(me_router, prefix="/me", tags=["Me"])
    router.include_router(user_router, prefix="/users", tags=["Users"])
    router.include_router(amenity_router, prefix="/amenities", tags=["Amenities"])
    router.include_router(apartments_router, prefix="/apartments", tags=["Apartments"])
    router.include_router(
        applications_router, prefix="/applications", tags=["Apartment Applications"]
    )
    router.include_router(invites_router, prefix="/invites", tags=["Invites"])
    router.include_router(
        signerequest_router, prefix="/signrequest", tags=["Signrequest Helpers"]
    )
    router.include_router(payments_router, prefix="/payments", tags=["Payments"])
    router.include_router(invoice_router, prefix="/invoices", tags=["Invoices"])
    router.include_router(chat_router, prefix="/chat", tags=["Chat"])
    router.include_router(blog_router, prefix="/blog", tags=["Blog"])
    router.include_router(documents_router, prefix="/documents", tags=["Documents"])
    router.include_router(
        notifications_router, prefix="/notifications", tags=["Notifications"]
    )
    return router


def get_admin_router() -> APIRouter:
    router = APIRouter()
    router.include_router(admin_auth_router, prefix="/auth", tags=["Authentication"])
    return router
