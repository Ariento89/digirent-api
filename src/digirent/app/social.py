from authlib.integrations.starlette_client import OAuth
from digirent.core.config import config

oauth = OAuth(config)

oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

oauth.register(
    name="facebook",
    authorize_url="https://www.facebook.com/v8.0/dialog/oauth",
    access_token_url="https://graph.facebook.com/v8.0/oauth/access_token",
    client_kwargs={"scope": "email"},
)
