from ..db.schema import UserInDB
from ..db.setup import session_context
from ..models.db import User, UserIn
from ..models.exceptions import NotFoundException


class UserDBService:
    """Basic CRUD interface for managing users in the database"""

    def get_all_users(self) -> list[User]:
        with session_context() as ses:
            users = ses.query(UserInDB).all()

        return [User.from_orm(user) for user in users]

    def create_user(self, user: UserIn) -> User:
        new_user = UserInDB(**user.dict())
        with session_context() as ses:
            ses.add(new_user)
            ses.commit()
            ses.refresh(new_user)

        return User.from_orm(new_user)

    def get_user(self, user_id: str | int) -> User | None:
        """Returns a user if they exist"""

        if isinstance(user_id, int):
            user_id = str(user_id)

        with session_context() as ses:
            existing_user = ses.query(UserInDB).filter_by(id=user_id).first()

        return User.from_orm(existing_user) if existing_user else None

    def update_user(self, user: UserIn) -> User:
        with session_context() as ses:
            existing_user = ses.query(UserInDB).filter_by(id=user.id).first()
            if not existing_user:
                raise NotFoundException(UserInDB, f"user_id={user.id}")

            existing_user.update(**user.dict(exclude_unset=True))
            ses.add(existing_user)
            ses.commit()
            ses.refresh(existing_user)

        return User.from_orm(existing_user)

    def delete_user(self, user_id: str) -> None:
        with session_context() as ses:
            existing_user = ses.query(UserInDB).filter_by(id=user_id).first()
            if not existing_user:
                return

            ses.delete(existing_user)
            ses.commit()
