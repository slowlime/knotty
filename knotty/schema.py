from datetime import datetime

from pydantic import BaseModel


class UserInfo(BaseModel):
    username: str
    email: str
    registered: datetime
    namespaces: list[str]


class AuthToken(BaseModel):
    token_type: str = "bearer"
    access_token: str


class UserRegister(BaseModel):
    username: str
    email: str
    password: str


class UserCreate(BaseModel):
    username: str
    email: str
    pwhash: str
    registered: datetime
