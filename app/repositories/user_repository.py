from app.repositories.base import BaseRepository
from app.models.user import User
from app.core.security import hash_password
from typing import Optional


class UserRepository(BaseRepository):
    def create_user(self, username: str, password: str, student_id: Optional[str] = None, email: Optional[str] = None):
        user = User(
            username=username,
            password_hash=hash_password(password),
            student_id=student_id,
            email=email,
        )
        self.db.add(user)
        self.db.flush()
        self.db.commit()
        return user

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()
