from typing import List
from sqlalchemy.orm.session import Session
from sqlalchemy import func
from .base import DBService
from ..models import Apartment


class ApartmentService(DBService[Apartment]):
    def __init__(self) -> None:
        super().__init__(Apartment)

    def get_apartments_within(
        self, session: Session, latitude: float, longitude: float, radius: float = 5
    ) -> List[Apartment]:
        """Returns all apartments withing a certain raidus from a certain location"""
        center = "POINT({} {})".format(longitude, latitude)
        return (
            session.query(Apartment)
            .filter(func.ST_Distance_Sphere(Apartment.location, center) < radius)
            .all()
        )
