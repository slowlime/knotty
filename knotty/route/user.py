from datetime import datetime

from typing import Annotated
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from knotty.config import config
from .. import acl, error, schema, storage
from ..auth import JwtTokenData, auth_user, create_token, hash_password
from ..db import SessionDep


router = APIRouter()


@router.get("/user/{username}")
def get_user(
    session: SessionDep,
    username: str,
    is_admin: Annotated[bool, Depends(acl.is_admin)],
    user_view: Annotated[bool, Depends(acl.can_view_user)],
) -> schema.UserInfo:
    user = storage.get_user(session, username)

    if not user:
        if is_admin:
            raise error.not_found()
        else:
            raise error.no_permission()

    acl.require(user_view)

    namespaces = storage.get_user_namespaces(session, username)

    return schema.UserInfo(
        username=user.username,
        email=user.email,
        registered=user.registered,
        namespaces=namespaces,
    )


@router.post("/login")
def login(
    session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> schema.AuthToken:
    user = auth_user(session, form_data.username, form_data.password)

    if user is None:
        raise error.invalid_credentials()

    token = create_token(
        JwtTokenData.for_username(form_data.username), config.token_expiry
    )

    return schema.AuthToken(access_token=token)


@router.post("/user", status_code=status.HTTP_201_CREATED)
def register(session: SessionDep, body: schema.UserRegister) -> None:
    match storage.get_user_registered(session, body.username, body.email):
        case schema.UserRegistered.username_taken:
            raise error.username_taken()

        case schema.UserRegistered.email_registered:
            raise error.email_registered()

        case schema.UserRegistered.not_registered:
            pass

    pwhash = hash_password(body.password)
    registered = datetime.utcnow()

    storage.create_user(
        session, schema.UserCreate(pwhash=pwhash, registered=registered, **body.dict())
    )
    session.commit()
