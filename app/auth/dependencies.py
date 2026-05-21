from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.auth.model import AuthUser
from app.auth.schemas import TokenData
from app.auth import service as auth_service
from app.config import settings
from app.database import get_db

# auto_error=False: token is optional at the transport level so we can
# return a sandbox user when DISABLE_SECURITY=true without Swagger failing.
_oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)

# Transient SQLAlchemy instance used as a sentinel in sandbox mode.
_SANDBOX_USER = AuthUser(username="sandbox", hashed_password="", is_active=True)
_SANDBOX_USER.id = 0


async def get_current_user(
    token: str | None = Depends(_oauth2),
    db: Session = Depends(get_db),
) -> AuthUser:
    if settings.disable_security:
        return _SANDBOX_USER

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.jwt_algorithm]
        )
        username: str | None = payload.get("sub")
        if username is None:
            raise exc
    except JWTError:
        raise exc

    user = auth_service.get_user(db, username)
    if user is None or not user.is_active:
        raise exc
    return user
