from typing import List, TypeVar
from typing import Generic
from sqlalchemy.orm.session import Session
from uuid import UUID

T = TypeVar("T")


class DBService(Generic[T]):
    def __init__(self, model_class: T):
        self.model_calss = model_class

    def create(self, session: Session, commit=True, **create_data: dict) -> T:
        model = self.model_calss(**create_data)
        session.add(model)
        if commit:
            session.commit()
        return model

    def update(
        self, session: Session, model: T = None, commit=True, **create_data: dict
    ) -> T:
        assert isinstance(model, self.model_calss)
        for key, val in create_data.items():
            setattr(model, key, val)
        if commit:
            session.commit()
        return model

    def delete(self, session: Session, model: T = None, commit=True):
        assert isinstance(model, self.model_calss)
        session.delete(model)
        if commit:
            session.commit()
        return model

    def get(self, session: Session, model_id: UUID) -> T:
        return session.query(self.model_calss).get(model_id)

    def all(self, session: Session) -> List[T]:
        return session.query(self.model_calss).all()
