from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    TENANT = "tenant"
    LANDLORD = "landlord"


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"


class HouseType(str, Enum):
    DUPLEX = "duplex"
    BUNGALOW = "bungalow"
    FLAT = "flat"


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
    SIGNED = "signed"
    EXPIRED = "expired"
    DECLINED = "declined"
    CANCELED = "canceled"
    COMPLETED = "completed"
