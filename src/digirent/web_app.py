from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import digirent.core.config as config
from digirent.api.auth.router import router as auth_router
from digirent.api.me.router import router as me_router
from digirent.api.user.router import router as user_router
from digirent.api.amenity.router import router as amenity_router


def get_app():
    app = FastAPI(title=config.PROJECT_NAME, openapi_url="/api/openapi.json")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(config.ALLOWED_HOSTS),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(me_router, prefix="/api/me", tags=["Me"])
    app.include_router(user_router, prefix="/api/users", tags=["Users"])
    app.include_router(amenity_router, prefix="/api/amenities", tags=["Amenities"])
    return app


app: FastAPI = get_app()
