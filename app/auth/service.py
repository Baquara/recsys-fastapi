from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.auth.model import AuthUser
from app.config import settings

_pwd = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)


def hash_password(plain: str) -> str:
    return _pwd.hash(plain)


def get_user(db: Session, username: str) -> AuthUser | None:
    return db.query(AuthUser).filter(AuthUser.username == username).first()


def create_user(db: Session, username: str, password: str) -> AuthUser:
    user = AuthUser(username=username, hashed_password=hash_password(password))
    db.add(user)
    db.flush()
    return user


def authenticate_user(db: Session, username: str, password: str) -> AuthUser | None:
    user = get_user(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    payload = data.copy()
    expire = datetime.now(tz=timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload["exp"] = expire
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
