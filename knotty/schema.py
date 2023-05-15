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


class Namespace(BaseModel):
    name: str
    description: str
    homepage: str | None
    created_date: datetime
    users: list["NamespaceUser"]
    roles: list["NamespaceRole"]


class NamespaceUser(BaseModel):
    username: str
    added_date: datetime
    added_by: str
    updated_date: datetime
    updated_by: str
    role: str


class NamespaceRole(BaseModel):
    name: str
    created_date: datetime
    created_by: str
    updated_date: datetime
    updated_by: str
    permissions: list[str]


class PackageBasic(BaseModel):
    name: str
    summary: str


class PackageBrief(PackageBasic):
    labels: list[str]
    namespace: str | None
    owners: list[str]
    updated_date: datetime
    downloads: int
