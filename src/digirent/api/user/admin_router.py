from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm.session import Session
import digirent.api.dependencies as dependencies
from digirent.database.models import User
from digirent.database.enums import UserRole
from .schema import UserSchema


router = APIRouter()


@router.get(
    "/",
    response_model=List[UserSchema],
    dependencies=[Depends(dependencies.get_current_admin_user)],
)
def fetch_all_users(
    role: Optional[UserRole] = None,
    session: Session = Depends(dependencies.get_database_session),
):
    # TODO pagination
    query = session.query(User)
    if type is not None:
        query = query.filter(User.role == role)
    return session.query(User).all()
