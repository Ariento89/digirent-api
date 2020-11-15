from starlette.types import Scope, Receive, Send, ASGIApp
from digirent.api.chat.chat import ChatManager


class ChatManagerMiddleware:  # pylint: disable=too-few-public-methods
    """Middleware for providing a global :class:`~.ChatManager` instance to both HTTP
    and WebSocket scopes.

    Although it might seem odd to load the broadcast interface like this (as
    opposed to, e.g. providing a global) this both mimics the pattern
    established by starlette's existing DatabaseMiddlware, and describes a
    pattern for installing an arbitrary broadcast backend (Redis PUB-SUB,
    Postgres LISTEN/NOTIFY, etc) and providing it at the level of an individual
    request.
    """

    def __init__(self, app: ASGIApp):
        self.app = app
        self.chat_manager: ChatManager = ChatManager()

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] in ("lifespan", "http", "websocket"):
            scope["chat_manager"] = self.chat_manager
        await self.app(scope, receive, send)
