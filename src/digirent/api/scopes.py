from typing import List


ME_READ = "me:read"
ME_WRITE = "me:write"
APARTMENTS_READ = "apartments:read"
APARTMENT_READ = "apartment:read"
APARTMENTS_WRITE = "apartments:write"
APARTMENT_WRITE = "apartment:write"
APARTMENTS_APPLICATIONS_READ = "apartments_applications:read"
APARTMENTS_APPLICATION_READ = "apartments_application:read"
APARTMENTS_APPLICATIONS_WRITE = "apartments_applications:write"
APARTMENTS_APPLICATION_WRITE = "apartments_application:write"
USER_READ = "user:read"
USER_WRITE = "user:write"
USERS_READ = "users:read"
USERS_WRITE = "users:write"
AMENITY_READ = "amenity:read"
AMENITY_WRITE = "amenity:write"
AMENITIES_READ = "amenities:read"
AMENITIES_WRITE = "amenities:write"
INVITE_READ = "invite:read"
INVITES_READ = "invites:read"
INVITES_WRITE = "invites:write"
INVITE_WRITE = "invite:write"


TENANT_SCOPES = [
    ME_READ,
    ME_WRITE,
    APARTMENT_READ,
    APARTMENTS_READ,
    APARTMENTS_APPLICATION_READ,
    APARTMENTS_APPLICATIONS_READ,
    APARTMENTS_APPLICATION_WRITE,
    USER_READ,
    AMENITIES_READ,
    AMENITY_READ,
    INVITE_READ,
    INVITES_READ,
    INVITE_WRITE,
]

LANDLORD_SCOPES = [
    ME_READ,
    ME_WRITE,
    APARTMENT_READ,
    APARTMENTS_READ,
    APARTMENT_WRITE,
    APARTMENTS_WRITE,
    APARTMENTS_APPLICATION_READ,
    APARTMENTS_APPLICATIONS_READ,
    APARTMENTS_APPLICATION_WRITE,
    APARTMENTS_APPLICATIONS_WRITE,
    USER_READ,
    USERS_READ,
    AMENITIES_READ,
    AMENITY_READ,
    INVITE_READ,
    INVITE_WRITE,
    INVITES_READ,
    INVITES_WRITE,
]

ADMIN_SCOPES = [
    ME_READ,
    ME_WRITE,
    APARTMENTS_READ,
    APARTMENT_READ,
    APARTMENTS_WRITE,
    APARTMENT_WRITE,
    APARTMENTS_APPLICATIONS_READ,
    APARTMENTS_APPLICATION_READ,
    APARTMENTS_APPLICATIONS_WRITE,
    APARTMENTS_APPLICATION_WRITE,
    USER_READ,
    USER_WRITE,
    USERS_READ,
    USERS_WRITE,
    AMENITY_READ,
    AMENITY_WRITE,
    AMENITIES_READ,
    AMENITIES_WRITE,
    INVITE_READ,
    INVITES_READ,
    INVITES_WRITE,
    INVITE_WRITE,
]

scope_dict = {
    ME_READ: "Read profile information",
    ME_WRITE: "Update profile infomation",
    APARTMENTS_READ: "Fetch multiple apartments",
    APARTMENT_READ: "Read a single apartment",
    APARTMENTS_WRITE: "Create a new apartment",
    APARTMENT_WRITE: "Update existing apartment",
    APARTMENTS_APPLICATIONS_READ: "Read multiple apartment applications",
    APARTMENTS_APPLICATION_READ: "Read a single apartment applications",
    APARTMENTS_APPLICATIONS_WRITE: "Create a new apartment application",
    APARTMENTS_APPLICATION_WRITE: "Update existing apartment application",
    USER_READ: "Read a single user",
    USER_WRITE: "Update a user",
    USERS_READ: "Read multiple users",
    USERS_WRITE: "Add a new user",
    AMENITY_READ: "Read a single amenity",
    AMENITY_WRITE: "Update existing amenity",
    AMENITIES_READ: "Read multiple amenities",
    AMENITIES_WRITE: "Add a new amenity",
    INVITE_READ: "Read a single booking request invite",
    INVITES_READ: "Read multiple booking request invite",
    INVITES_WRITE: "Create a new invite",
    INVITE_WRITE: "Update existing invite",
}


def is_allowed(required_scope: str, permitted_scopes: List[str]):
    required_scope_name, required_scope_action = required_scope.split(":")
    splitted_permitted_scopes = [
        permitted_scope.split(":") for permitted_scope in permitted_scopes
    ]
    return any(
        required_scope_name == permitted_scope_name
        and (
            required_scope_action == permitted_scope_action
            or permitted_scope_action == "write"
        )
        for permitted_scope_name, permitted_scope_action in splitted_permitted_scopes
    )
