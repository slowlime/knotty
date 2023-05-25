from datetime import datetime, timedelta
from logging import getLogger
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

from . import model, storage
from .config import Config, ConfigDep
from .db import SessionDep
from .error import unauthorized

JWT_ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["argon2"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
logger = getLogger(__name__)


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
    user = storage.get_user_model(session, username)

    if user is None:
        return None

    if not verify_password(password, user.pwhash):
        return None

    return user


def create_token(data: JwtTokenData, expires_in: timedelta, config: Config) -> str:
    expiration = datetime.utcnow() + expires_in
    data = ExpireableJwtTokenData(exp=expiration, **data.dict())
    encoded = jwt.encode(
        data.dict(), config.secret_key.get_secret_value(), algorithm=JWT_ALGORITHM
    )

    return encoded


def get_current_user(
    session: SessionDep, token: Annotated[str, Depends(oauth2_scheme)],
    config: ConfigDep,
) -> model.User:
    try:
        payload = jwt.decode(
            token, config.secret_key.get_secret_value(), algorithms=[JWT_ALGORITHM]
        )
        sub: str | None = payload.get("sub")

        if sub is None:
            logger.error("Received a valid JWT without sub field! Payload: %s", payload)

            raise unauthorized()

        username = sub[len("username:"):]
    except JWTError:
        logger.info("Received an invalid JWT", exc_info=True)

        raise unauthorized()

    user = storage.get_user_model(session, username)

    if user is None:
        logger.error("Received a valid JWT for invalid user %s!", sub)

        raise unauthorized()

    logger.debug("Username %s has been authenticated", user.username)

    return user


AuthDep = Annotated[model.User, Depends(get_current_user)]
