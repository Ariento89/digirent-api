from fastapi.testclient import TestClient
from sqlalchemy.orm.session import Session
from digirent.database.enums import ApartmentApplicationStatus, ContractStatus
from digirent.database.models import Landlord, Tenant, Apartment, ApartmentApplication


def test_tenant_apply_for_apartment_ok(
    client: TestClient,
    session: Session,
    tenant: Tenant,
    apartment: Apartment,
    tenant_auth_header: dict,
):
    assert not session.query(ApartmentApplication).count()
    response = client.post(
        f"/api/applications/{apartment.id}", headers=tenant_auth_header
    )
    result = response.json()
    assert response.status_code == 201
    assert isinstance(result, dict)
    assert "tenantId" in result
    assert "apartmentId" in result
    assert "id" in result
    assert result["tenantId"] == str(tenant.id)
    assert result["apartmentId"] == str(apartment.id)
    assert session.query(ApartmentApplication).count()
    apartment_application = session.query(ApartmentApplication).get(result["id"])
    assert apartment_application.status == ApartmentApplicationStatus.NEW
    assert apartment_application
    assert apartment_application.tenant == tenant
    assert apartment_application.apartment == apartment


def test_landlord_apply_for_apartment_fail(
    client: TestClient,
    session: Session,
    apartment: Apartment,
    landlord_auth_header: dict,
):
    assert not session.query(ApartmentApplication).count()
    response = client.post(
        f"/api/applications/{apartment.id}", headers=landlord_auth_header
    )
    assert response.status_code == 403
    assert not session.query(ApartmentApplication).count()


def test_landlord_reject_tenants_application_ok(
    client: TestClient,
    new_apartment_application: ApartmentApplication,
    session: Session,
    landlord_auth_header: dict,
):
    assert new_apartment_application.status == ApartmentApplicationStatus.NEW
    response = client.post(
        f"/api/applications/{new_apartment_application.id}/reject",
        headers=landlord_auth_header,
    )
    result = response.json()
    assert response.status_code == 200
    assert isinstance(result, dict)
    session.expire_all()
    rejected_apartment_application = session.query(ApartmentApplication).get(
        new_apartment_application.id
    )
    assert rejected_apartment_application.status == ApartmentApplicationStatus.REJECTED


def test_landlord_consider_tenants_application_ok(
    client: TestClient,
    new_apartment_application: ApartmentApplication,
    session: Session,
    landlord_auth_header: dict,
):
    assert new_apartment_application.status == ApartmentApplicationStatus.NEW
    response = client.post(
        f"/api/applications/{new_apartment_application.id}/consider",
        headers=landlord_auth_header,
    )
    result = response.json()
    assert response.status_code == 200
    assert isinstance(result, dict)
    session.expire_all()
    new_apartment_application = session.query(ApartmentApplication).get(
        new_apartment_application.id
    )
    assert new_apartment_application.status == ApartmentApplicationStatus.CONSIDERED


def test_another_landlord_reject_tenants_application_fail(
    client: TestClient,
    new_apartment_application: ApartmentApplication,
    session: Session,
    another_landlord_auth_header: dict,
):
    assert new_apartment_application.status == ApartmentApplicationStatus.NEW
    response = client.post(
        f"/api/applications/{new_apartment_application.id}/reject",
        headers=another_landlord_auth_header,
    )
    assert response.status_code == 404
    session.expire_all()
    new_apartment_application = session.query(ApartmentApplication).get(
        new_apartment_application.id
    )
    assert new_apartment_application.status == ApartmentApplicationStatus.NEW


def test_another_landlord_consider_tenants_application_fail(
    client: TestClient,
    new_apartment_application: ApartmentApplication,
    session: Session,
    another_landlord_auth_header: dict,
):
    assert new_apartment_application.status == ApartmentApplicationStatus.NEW
    response = client.post(
        f"/api/applications/{new_apartment_application.id}/consider",
        headers=another_landlord_auth_header,
    )
    assert response.status_code == 404
    session.expire_all()
    new_apartment_application = session.query(ApartmentApplication).get(
        new_apartment_application.id
    )
    assert new_apartment_application.status == ApartmentApplicationStatus.NEW


def test_landlord_fetch_apartment_applications(
    client: TestClient,
    apartment: Apartment,
    session: Session,
    new_apartment_application,
    landlord: Landlord,
    landlord_auth_header,
):
    assert (
        session.query(ApartmentApplication)
        .join(Apartment)
        .filter(ApartmentApplication.apartment_id == apartment.id)
        .filter(Apartment.landlord_id == landlord.id)
        .count()
    )
    response = client.get(
        f"/api/applications/{apartment.id}", headers=landlord_auth_header
    )
    assert response.status_code == 200
    result = response.json()
    assert isinstance(result, list)
    assert len(result) == 1


def test_tenant_fetch_applications(
    client: TestClient,
    apartment: Apartment,
    session: Session,
    new_apartment_application,
    landlord: Landlord,
    tenant_auth_header,
):
    assert (
        session.query(ApartmentApplication)
        .join(Apartment)
        .filter(ApartmentApplication.apartment_id == apartment.id)
        .filter(Apartment.landlord_id == landlord.id)
        .count()
    )
    response = client.get("/api/applications/", headers=tenant_auth_header)
    assert response.status_code == 200
    result = response.json()
    assert isinstance(result, list)
    assert len(result) == 1


def test_process_apartment_application(
    client: TestClient,
    considered_apartment_application: ApartmentApplication,
    landlord_auth_header: dict,
    session: Session,
):
    assert not considered_apartment_application.contract
    response = client.post(
        f"/api/applications/{considered_apartment_application.id}/process",
        headers=landlord_auth_header,
    )
    assert response.status_code == 200
    session.expire_all()
    assert (
        considered_apartment_application.status == ApartmentApplicationStatus.PROCESSING
    )
    assert considered_apartment_application.contract
    assert considered_apartment_application.contract.status == ContractStatus.NEW


def test_process_another_tenants_application_when_one_is_currently_being_processed(
    client: TestClient,
    another_considered_application: ApartmentApplication,
    process_apartment_application: ApartmentApplication,
    landlord_auth_header: dict,
    session: Session,
):
    response = client.post(
        f"/api/applications/{another_considered_application.id}/process",
        headers=landlord_auth_header,
    )
    assert response.status_code == 400
    assert (
        another_considered_application.status == ApartmentApplicationStatus.CONSIDERED
    )


def test_event_handler_tenant_signed_document(client: TestClient):
    data = {
        "uuid": "ea0d844f-ceba-41ab-a069-fafaff5a34ed",
        "status": "ok",
        "event_type": "signed",
        "timestamp": "2020-10-23T11:40:13.565667Z",
        "team": {
            "name": "Shaibudev",
            "subdomain": "shbdev",
            "url": "https://shbdev.signrequest.com/api/v1/teams/shbdev/",
        },
        "document": {
            "team": {
                "name": "Shaibudev",
                "subdomain": "shbdev",
                "url": "https://shbdev.signrequest.com/api/v1/teams/shbdev/",
            },
            "uuid": "27a7c1ec-66ee-40fd-b195-094601dc4dd6",
            "user": None,
            "file_as_pdf": "https://signrequest-pro.s3.amazonaws.com/original_pdfs/2020/10/23/acebcbaf7a797b5b25922a5e7e85920af121e080/digirentcontracttemplate2_1docx.pdf?AWSAccessKeyId=AKIAIFC5SSMNRPLY3AMQ&Signature=c%2FlBdLhqU2CMKioapwcKhV15WjE%3D&Expires=1603453813",
            "name": "3dbbe1e8-5e07-4dfa-b51c-97a34f1139a1-mydocument.docx",
            "external_id": "3dbbe1e8-5e07-4dfa-b51c-97a34f1139a1",
            "file": "https://signrequest-pro.s3.amazonaws.com/docs/2020/10/23/6362c5ceade3b9b98ddd01b25f9224e605a1fd46/digirentcontracttemplate2_1.docx?AWSAccessKeyId=AKIAIFC5SSMNRPLY3AMQ&Signature=xMDdr2EOwiyYFIeJUP3NVOCuH%2B8%3D&Expires=1603453813",
            "file_from_url": None,
            "events_callback_url": None,
            "template": "https://shbdev.signrequest.com/api/v1/templates/9b9de3ee-c282-46fd-9470-d8833d030953/",
            "prefill_tags": [],
            "integrations": [],
            "file_from_sf": None,
            "auto_delete_days": None,
            "auto_expire_days": None,
            "pdf": "https://signrequest-pro.s3.amazonaws.com/pdfs/2020/10/23/4bf2f2711e59b0384c29e5985e2a928da10af76e/3dbbe1e8-5e07-4dfa-b51c-97a34f1139a1-mydocument_signed.pdf?AWSAccessKeyId=AKIAIFC5SSMNRPLY3AMQ&Signature=V5vdg0ao71eelaS2%2BXVpyRWxpUg%3D&Expires=1603453813",
            "status": "si",
            "signrequest": {
                "from_email": "noreply@digirent.com",
                "from_email_name": "Digirent Contractor",
                "is_being_prepared": False,
                "prepare_url": None,
                "redirect_url": None,
                "redirect_url_declined": None,
                "required_attachments": [],
                "disable_attachments": False,
                "disable_text_signatures": False,
                "disable_text": False,
                "disable_date": False,
                "disable_emails": False,
                "disable_upload_signatures": False,
                "force_signature_color": None,
                "disable_blockchain_proof": None,
                "text_message_verification_locked": None,
                "subject": "Sign this document",
                "message": "This is the email for you to sign this contract for your apartment",
                "who": "o",
                "send_reminders": False,
                "signers": [
                    {
                        "email": "noreply@digirent.com",
                        "display_name": "noreply@digirent.com",
                        "first_name": "",
                        "last_name": "",
                        "email_viewed": False,
                        "viewed": False,
                        "signed": False,
                        "downloaded": False,
                        "signed_on": None,
                        "needs_to_sign": False,
                        "approve_only": False,
                        "notify_only": False,
                        "in_person": False,
                        "order": 0,
                        "language": None,
                        "force_language": False,
                        "emailed": False,
                        "verify_phone_number": None,
                        "verify_bank_account": None,
                        "declined": False,
                        "declined_on": None,
                        "forwarded": False,
                        "forwarded_on": None,
                        "forwarded_to_email": None,
                        "forwarded_reason": None,
                        "message": None,
                        "embed_url_user_id": None,
                        "inputs": [],
                        "use_stamp_for_approve_only": False,
                        "embed_url": None,
                        "attachments": [],
                        "redirect_url": None,
                        "redirect_url_declined": None,
                        "after_document": None,
                        "integrations": [],
                    },
                    {
                        "email": "tellshaibu@gmail.com",
                        "display_name": "tellshaibu@gmail.com",
                        "first_name": "",
                        "last_name": "",
                        "email_viewed": True,
                        "viewed": True,
                        "signed": True,
                        "downloaded": False,
                        "signed_on": "2020-10-23T11:38:41.106712Z",
                        "needs_to_sign": True,
                        "approve_only": False,
                        "notify_only": False,
                        "in_person": False,
                        "order": 0,
                        "language": None,
                        "force_language": False,
                        "emailed": True,
                        "verify_phone_number": None,
                        "verify_bank_account": None,
                        "declined": False,
                        "declined_on": None,
                        "forwarded": False,
                        "forwarded_on": None,
                        "forwarded_to_email": None,
                        "forwarded_reason": None,
                        "message": None,
                        "embed_url_user_id": None,
                        "inputs": [
                            {
                                "type": "s",
                                "page_index": 0,
                                "text": "",
                                "checkbox_value": None,
                                "date_value": None,
                                "external_id": None,
                                "placeholder_uuid": "a51ff074-a2d0-4b0e-a914-4cea75b258d1",
                            }
                        ],
                        "use_stamp_for_approve_only": False,
                        "embed_url": None,
                        "attachments": [],
                        "redirect_url": None,
                        "redirect_url_declined": None,
                        "after_document": None,
                        "integrations": [],
                    },
                    {
                        "email": "jnrshb35@gmail.com",
                        "display_name": "jnrshb35@gmail.com",
                        "first_name": "",
                        "last_name": "",
                        "email_viewed": True,
                        "viewed": True,
                        "signed": True,
                        "downloaded": False,
                        "signed_on": "2020-10-23T11:39:20.442194Z",
                        "needs_to_sign": True,
                        "approve_only": False,
                        "notify_only": False,
                        "in_person": False,
                        "order": 0,
                        "language": None,
                        "force_language": False,
                        "emailed": True,
                        "verify_phone_number": None,
                        "verify_bank_account": None,
                        "declined": False,
                        "declined_on": None,
                        "forwarded": False,
                        "forwarded_on": None,
                        "forwarded_to_email": None,
                        "forwarded_reason": None,
                        "message": None,
                        "embed_url_user_id": None,
                        "inputs": [
                            {
                                "type": "s",
                                "page_index": 0,
                                "text": "",
                                "checkbox_value": None,
                                "date_value": None,
                                "external_id": None,
                                "placeholder_uuid": None,
                            }
                        ],
                        "use_stamp_for_approve_only": False,
                        "embed_url": None,
                        "attachments": [],
                        "redirect_url": None,
                        "redirect_url_declined": None,
                        "after_document": None,
                        "integrations": [],
                    },
                ],
                "uuid": "202b061b-7241-4a16-8cb2-e33c5262d8d1",
            },
            "api_used": True,
            "signing_log": {
                "pdf": "https://signrequest-pro.s3.amazonaws.com/logs/2020/10/23/3925c5b5e05ad963c7a3708eec96d0eb47295bc1/3dbbe1e8-5e07-4dfa-b51c-97a34f1139a1-mydocument_signing_log.pdf?AWSAccessKeyId=AKIAIFC5SSMNRPLY3AMQ&Signature=5z%2FlwdwucDVVgn2ceBUwjHxcUBA%3D&Expires=1603453813",
                "security_hash": "5e174be7d2af4e4c65bec631a52c6130fed773848da59adf0080f69430901c51",
            },
            "security_hash": "e3e5090eeab663cb2eec89452a2bd13eeb3ba03945c0b9fceb6edd03d236f8fa",
            "attachments": [],
            "auto_delete_after": None,
            "sandbox": True,
            "auto_expire_after": None,
            "processing": False,
        },
        "signer": None,
        "token_name": "Token",
        "event_time": "1603453213",
        "event_hash": "85c37518f93161076cbadb81bc8062696316bed60a6d231f18cd5d1a08ddd82d",
    }
    response = client.post("/api/applications/contract", json=data)
    assert response.status_code == 200


def test_event_handler_tenant_declined_document():
    raise Exception()


def test_event_handler_landlord_signed_document():
    raise Exception()


def test_event_handler_landlord_declined_document():
    raise Exception()


def test_landlord_confirm_keys_provided_to_tenant():
    raise Exception()


def test_tenant_confirm_apartment_keys_received_from_landlord():
    raise Exception()
