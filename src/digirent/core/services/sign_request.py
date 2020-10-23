import signrequest_client
from uuid import UUID
from digirent.core.config import SIGNREQUEST_API_KEY, SIGNREQUEST_TEMPLATE_URL


default_configuration = signrequest_client.Configuration()
default_configuration.api_key["Authorization"] = SIGNREQUEST_API_KEY
default_configuration.api_key_prefix["Authorization"] = "Token"
signrequest_client.Configuration.set_default(default_configuration)

quick_create_api = signrequest_client.SignrequestQuickCreateApi()


def send_contract_sign_request(
    document_external_id: UUID, landlord_email: str, tenant_email: str
):
    file_extension = ".docx"
    from_email = "noreply@digirent.com"
    from_email_name = "Digirent Contract"
    email_subject = "Contract For Apartment"
    email_message = (
        "Sign the following contract to conclude your application for the apartment"
    )
    signers = [{"email": landlord_email}, {"email": tenant_email}]
    data = signrequest_client.SignRequestQuickCreate(
        signers=signers,
        external_id=str(document_external_id),
        name=f"{str(document_external_id)}-mydocument.{file_extension}",
        template=SIGNREQUEST_TEMPLATE_URL,
        from_email=from_email,
        from_email_name=from_email_name,
        subject=email_subject,
        message=email_message,
    )
    return quick_create_api.signrequest_quick_create_create(data)
