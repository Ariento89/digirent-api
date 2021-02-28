from authlib.integrations.starlette_client import OAuth
from digirent.core.config import config
from digirent.util import generate_apple_client_secret

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
    client_kwargs={"scope": "email user_gender"},
)


oauth.register(
    name="apple",
    authorize_url="https://appleid.apple.com/auth/authorize",
    access_token_url="https://appleid.apple.com/auth/token",
    client_secret=generate_apple_client_secret(),
)
