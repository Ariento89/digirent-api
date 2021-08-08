from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from digirent.api.middlewares import ChatManagerMiddleware
import digirent.core.config as config
from digirent.api.routers import get_admin_router, get_normal_router


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
    api.include_router(get_admin_router(), prefix="/admin")
    api.include_router(get_normal_router())
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
