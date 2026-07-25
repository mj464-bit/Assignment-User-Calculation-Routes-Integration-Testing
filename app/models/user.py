import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, or_
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    """User model with authentication support."""

    __tablename__ = "users"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)

    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    calculations = relationship(
        "Calculation", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(username={self.username}, email={self.email})>"

    def verify_password(self, plain_password: str) -> bool:
        from app.auth.jwt import verify_password
        return verify_password(plain_password, self.password)

    @classmethod
    def hash_password(cls, password: str) -> str:
        from app.auth.jwt import get_password_hash
        return get_password_hash(password)

    @classmethod
    def register(cls, db, user_data: dict) -> "User":
        existing_user = (
            db.query(cls)
            .filter(or_(cls.email == user_data["email"], cls.username == user_data["username"]))
            .first()
        )
        if existing_user:
            raise ValueError("Username or email already exists")

        user = cls(
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            email=user_data["email"],
            username=user_data["username"],
            password=cls.hash_password(user_data["password"]),
        )
        db.add(user)
        db.flush()
        return user

    @classmethod
    def authenticate(cls, db, username_or_email: str, password: str):
        user = (
            db.query(cls)
            .filter(or_(cls.username == username_or_email, cls.email == username_or_email))
            .first()
        )
        if not user or not user.verify_password(password):
            return None
        return user
        