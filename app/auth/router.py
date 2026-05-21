from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth.schemas import Token
from app.auth import service as auth_service
from app.config import settings
from app.database import get_db

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/token",
    response_model=Token,
    summary="Obtain a JWT access token",
    description=(
        "Exchange credentials for a short-lived JWT bearer token.\n\n"
        "Pass the returned `access_token` as `Authorization: Bearer <token>` "
        "on every subsequent request.\n\n"
        "> When `DISABLE_SECURITY=true` any credentials are accepted and "
        "a sandbox token is returned — **never enable this in production**."
    ),
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    if settings.disable_security:
        token = auth_service.create_access_token({"sub": form_data.username or "sandbox"})
        return Token(access_token=token)

    user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_service.create_access_token({"sub": user.username})
    return Token(access_token=token)
