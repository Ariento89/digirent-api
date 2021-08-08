from enum import Enum


class UserRole(str, Enum):
    TENANT = "tenant"
    LANDLORD = "landlord"


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"


class HouseType(str, Enum):
    STUDIO = "studio"
    APARTMENT = "apartment"
    SHARED_ROOM = "shared_room"
    PRIVATE_ROOM = "private_room"


class FurnishType(str, Enum):
    FURNISHED = "furnished"
    UNFURNISHED = "unfurnished"


class ApartmentApplicationStatus(str, Enum):
    NEW = "new"
    REJECTED = "rejected"
    CONSIDERED = "considered"
    PROCESSING = "processing"
    AWARDED = "awarded"
    FAILED = "failed"
    COMPLETED = "completed"


class BookingRequestStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class SocialAccountType(str, Enum):
    GOOGLE = "google"
    FACEBOOK = "facebook"


class ContractStatus(str, Enum):
    NEW = "new"
    NO_CONTRACT = "no_contract"
    SIGNED = "signed"
    EXPIRED = "expired"
    DECLINED = "declined"
    CANCELED = "canceled"
    COMPLETED = "completed"


class InvoiceType(str, Enum):
    RENT = "rent"
    SUBSCRIPTION = "subscription"


class InvoiceStatus(str, Enum):
    PAID = "paid"
    PENDING = "pending"
    FAILED = "failed"


class NotificationType(str, Enum):
    CHAT = "chat"
    NEW_APARTMENT_APPLICATION = "new_apartment_application"
    REJECTED_APARTMENT_APPLICATION = "rejected_apartment_application"
    CONSIDERED_APARTMENT_APPLICATION = "considered_apartment_application"
    ACCEPTED_APARTMENT_APPLICATION = "accepted_apartment_application"
    PROCESSING_APARTMENT_APPLICATION = "processing_apartment_application"
    CONTRACT_SIGNED = "contract_signed"
    CONTRACT_DECLINED = "contract_declined"
    CONTRACT_EXPIRED = "contract_expired"
    CONTRACT_CANCELLED = "contract_cancelled"
    KEYS_PROVIDED = "keys_provided"
    KEYS_ACCEPTED = "keys_accepted"
    COMPLETED_APARTMENT_APPLICATION = "completed_apartment_application"


class ActivityTokenType(str, Enum):
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"
