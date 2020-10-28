from typing import List
import pytest
from datetime import datetime
from sqlalchemy.orm.session import Session
from digirent.database.enums import FurnishType, HouseType
from digirent.app import Application
from digirent.database.models import Apartment, Landlord

user_point = (44.77873, 29.01727)  # lat, long
points_within_5km_from_user_point = [
    (44.76304761, 28.99951908),
    (44.78763955, 28.99037194),
    (44.78155248, 29.01414248),
    (44.78716179, 29.05170142),
    (44.78261635, 29.00617414),
]
points_exceeding_5km_from_user_point = [
    (5.9341792, 10.0),
    (5.95260307, 10.87772012),
    (5.93982001, 10.86846242),
    (5.89213167, 10.87484201),
    (5.93900162, 10.86466191),
]
points = points_within_5km_from_user_point + points_exceeding_5km_from_user_point


def create_apartment_at(
    application: Application, session, landlord, index, latitude, longitude
) -> Apartment:
    apartment_create_data = dict(
        name=f"Apartment Name {index}",
        monthly_price=450.70 + index,
        utilities_price=320.15 + index,
        address=f"some address {index}",
        country=f"Nigeria{index}",
        state=f"Kano{index}",
        city=f"Kano{index}",
        description=f"Apartment description {index}",
        house_type=HouseType.DUPLEX,
        bedrooms=3 + index,
        bathrooms=4 + index,
        size=1200 + index,
        longitude=longitude,
        latitude=latitude,
        furnish_type=FurnishType.FURNISHED,
        available_from=datetime.now().date(),
        available_to=datetime.now().date(),
        amenities=[],
    )
    return application.create_apartment(session, landlord, **apartment_create_data)


@pytest.fixture
def apartments(
    application: Application, session: Session, landlord: Landlord
) -> List[Apartment]:
    return [
        create_apartment_at(application, session, landlord, index, *point)
        for index, point in enumerate(points)
    ]


def test_aparment_service_get_apartments_within_5km_of_a_point(
    application: Application, apartments: List[Apartment], session: Session
):
    pass
    # result = application.apartment_service.get_apartments_within(
    #     session, *user_point, 5000
    # )
    # assert len(result) == 5
