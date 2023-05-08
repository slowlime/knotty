from datetime import datetime, timedelta
from typing import Annotated
from fastapi import Depends, HTTPException, status

from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

from . import model, config
from .db import SessionDep
from .error import unauthorized
from .storage import get_user

JWT_ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["argon2"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


class JwtTokenData(BaseModel):
    sub: str

    @staticmethod
    def for_username(username: str) -> "JwtTokenData":
        return JwtTokenData(sub=f"username:{username}")


class ExpireableJwtTokenData(JwtTokenData):
    exp: datetime


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def auth_user(session: Session, username: str, password: str) -> model.User | None:
    user = get_user(session, username)

    if user is None:
        return None

    if not verify_password(password, user.pwhash):
        return None

    return user


def create_token(data: JwtTokenData, expires_in: timedelta) -> str:
    expiration = datetime.utcnow() + expires_in
    data = ExpireableJwtTokenData(exp=expiration, **data.dict())
    encoded = jwt.encode(data.dict(), config.secret_key, algorithm=JWT_ALGORITHM)

    return encoded


def get_current_user(
    session: SessionDep, token: Annotated[str, Depends(oauth2_scheme)]
) -> model.User:
    try:
        payload = jwt.decode(token, config.secret_key, algorithms=[JWT_ALGORITHM])
        username: str | None = payload.get("sub")

        if username is None:
            raise unauthorized()
    except JWTError:
        raise unauthorized()

    user = get_user(session, username)

    if user is None:
        raise unauthorized()

    return user


AuthDep = Annotated[model.User, Depends(get_current_user)]
