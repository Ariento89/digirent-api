from datetime import datetime
import sys
from sqlalchemy.orm.session import Session
from digirent.database.base import SessionLocal
from digirent.app import Application
from digirent.app.error import ApplicationError
from digirent.app.container import ApplicationContainer


def __create_admin_user(
    first_name: str,
    last_name: str,
    username: str,
    phonenumber: str,
    email: str,
    password: str,
):
    app: Application = ApplicationContainer.app()
    session: Session = SessionLocal()
    try:
        app.create_admin(
            session,
            first_name,
            last_name,
            datetime.utcnow().date(),
            email,
            phonenumber,
            password,
        )
        session.close()
    except ApplicationError as e:
        print(str(e))


def create_admin_user():
    first_name: str
    last_name: str
    email: str
    username: str
    phonenumber: str
    password: str
    if len(sys.argv) <= 1:
        # name = input("Admin Full Name: ")
        first_name = input("Enter First Name: ")
        last_name = input("Enter Last Name: ")
        username = input("Enter username: ")
        email = input("Email Address: ")
        phonenumber = input("Enter Phonenumber: ")
        password = input("password: ")
    elif len(sys.argv) == 7:
        first_name = sys.argv[1]
        last_name = sys.argv[2]
        username = sys.argv[3]
        email = sys.argv[4]
        phonenumber = sys.argv[5]
        password = sys.argv[6]
    else:
        print(
            "\nError:\n run: poetry run create_admin_user [firstname] [lastname] [username] [email] [phonenumber] [password]"
        )
        return
    __create_admin_user(first_name, last_name, username, phonenumber, email, password)
    print(f"User with and email {email} successfully created")
