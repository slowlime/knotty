from datetime import datetime

from typing import Annotated
from fastapi import Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from .. import app, error, schema, config, storage
from ..auth import AuthDep, JwtTokenData, auth_user, create_token, hash_password
from ..db import SessionDep


@app.get("/user/{username}")
def get_user(
    session: SessionDep, username: str, current_user: AuthDep
) -> schema.UserInfo:
    if username != current_user.username:
        raise error.no_permission()

    namespaces = storage.get_user_namespaces(session, username)

    return schema.UserInfo(
        username=current_user.username,
        email=current_user.email,
        registered=current_user.registered,
        namespaces=namespaces,
    )


@app.post("/login")
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


@app.post("/user", status_code=status.HTTP_201_CREATED)
def register(session: SessionDep, body: schema.UserRegister) -> None:
    if storage.get_user(session, body.username) is not None:
        raise error.username_taken()

    if storage.get_user_by_email(session, body.email) is not None:
        raise error.email_registered()

    pwhash = hash_password(body.password)
    registered = datetime.utcnow()

    storage.create_user(
        session, schema.UserCreate(pwhash=pwhash, registered=registered, **body.dict())
    )
    session.commit()
