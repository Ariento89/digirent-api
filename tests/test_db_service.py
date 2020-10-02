from uuid import uuid4
from digirent.database.base import Base
from digirent.database.mixins import EntityMixin, TimestampMixin
from sqlalchemy import Column, String, Integer
from sqlalchemy.orm.session import Session

from digirent.database.services.base import DBService


class TModel(Base, EntityMixin, TimestampMixin):
    __tablename__ = "testmodels"
    title = Column(String)
    other = Column(Integer)


tmodel_service = DBService[TModel](TModel)


def test_create_model_ok(session: Session):
    model = tmodel_service.create(session, title="helo", other=4)
    assert isinstance(model, TModel)
    assert session.query(TModel).count() == 1


def test_update_model_complete_ok(session: Session):
    model = tmodel_service.create(session, title="helo", other=4)
    assert isinstance(model, TModel)
    assert session.query(TModel).count() == 1
    assert model.title == "helo"
    assert model.other == 4
    model = tmodel_service.update(session, model, title="new title", other=6)
    assert model.title == "new title"
    assert model.other == 6
    xmodel = session.query(TModel).get(model.id)
    assert xmodel.title == "new title"
    assert xmodel.other == 6


def test_update_model_partial_ok(session: Session):
    model = tmodel_service.create(session, title="helo", other=4)
    assert isinstance(model, TModel)
    assert session.query(TModel).count() == 1
    assert model.title == "helo"
    assert model.other == 4
    model = tmodel_service.update(session, model, other=6)
    assert model.title == "helo"
    assert model.other == 6
    xmodel = session.query(TModel).get(model.id)
    assert xmodel.title == "helo"
    assert xmodel.other == 6


def test_get_model_ok(session: Session):
    model = tmodel_service.create(session, title="helo", other=4)
    assert isinstance(model, TModel)
    assert session.query(TModel).count() == 1
    assert tmodel_service.get(session, model.id) == model


def test_get_non_existing_model_fail(session: Session):
    non_existing_uuid = uuid4()
    model = tmodel_service.get(session, non_existing_uuid)
    assert not model


def test_fetch_models_ok(session: Session):
    model = tmodel_service.create(session, title="helo", other=4)
    assert isinstance(model, TModel)
    assert session.query(TModel).count() == 1
    assert tmodel_service.all(session) == [model]
