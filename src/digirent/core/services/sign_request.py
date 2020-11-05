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


def get_list_of_events(document_external_id: UUID, page: int = 1, page_size: int = 20):
    api_instance = signrequest_client.EventsApi()
    return api_instance.events_list(
        # document__uuid='document__uuid_example',
        document__external_id=str(document_external_id),
        # document__signrequest__who='document__signrequest__who_example',
        # document__signrequest__from_email='document__signrequest__from_email_example',
        # document__status='document__status_example',
        # document__user__email='document__user__email_example',
        # document__user__first_name='document__user__first_name_example',
        # document__user__last_name='document__user__last_name_example',
        # delivered='delivered_example',
        # delivered_on='delivered_on_example',
        # timestamp='timestamp_example',
        # status='status_example',
        # event_type='event_type_example',
        page=page,
        limit=page_size,
    )


def get_event(event_id: str):
    api_instance = signrequest_client.EventsApi()
    return api_instance.events_read(event_id)


def get_list_of_documents(
    document_external_id: UUID, page: int = 1, page_size: int = 20
):
    api_instance = signrequest_client.EventsApi()
    api_instance = signrequest_client.DocumentsApi()
    return api_instance.documents_list(
        page=page, limit=page_size, external_id=str(document_external_id)
    )


def get_document(document_id: str):
    api_instance = signrequest_client.DocumentsApi()
    return api_instance.documents_read(document_id)
