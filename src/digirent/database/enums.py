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


class ApartmentApplicationStage(str, Enum):
    REJECTED = "rejected"
    CONSIDERED = "considered"
    AWARDED = "awarded"


class BookingRequestStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
