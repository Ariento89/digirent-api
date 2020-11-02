from digirent.core.config import MOLLIE_API_KEY
from mollie.api.client import Client

mollie_client = Client()

mollie_client.set_api_key(MOLLIE_API_KEY)
