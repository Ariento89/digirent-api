from datetime import datetime
from sqlalchemy.orm.session import Session
from digirent.database.enums import HouseType, UserRole
from digirent.database.models import User, LookingFor, BankDetail


def test_user_looking_for_relationship(session: Session):
    user = User(
        "fname",
        "lname",
        "email",
        "00000",
        "hashed",
        UserRole.TENANT,
        datetime.now().date(),
    )
    session.add(user)
    session.flush()
    lfor = LookingFor(
        house_type=HouseType.BUNGALOW,
        city="test city",
        max_budget=70.5,
        user_id=user.id,
    )
    session.add(lfor)
    session.commit()
    assert user.looking_for == lfor
    assert lfor.user == user


def test_user_bank_detail_relationship(session: Session):
    user = User(
        "fname",
        "lname",
        "email",
        "00000",
        "hashed",
        UserRole.TENANT,
        datetime.now().date(),
    )
    session.add(user)
    session.flush()
    bank = BankDetail(
        account_name="acc name", account_number="0012345678910", user_id=user.id
    )
    session.add(bank)
    session.commit()
    assert user.bank_detail == bank
    assert bank.user == user
