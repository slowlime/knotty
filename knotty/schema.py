from datetime import datetime
from enum import Enum

from pydantic import BaseModel

from knotty import model

# TODO: username/namespace/package name constraints


class WithId(BaseModel):
    id: int


class UserRegistered(Enum):
    not_registered = 0
    username_taken = 1
    email_registered = 2


class UserInfo(BaseModel):
    username: str
    email: str
    registered: datetime
    namespaces: list[str]


class FullUserInfo(UserInfo, WithId):
    role: model.UserRole


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


class NamespaceBase(BaseModel):
    name: str
    description: str
    homepage: str | None


class NamespaceCreate(NamespaceBase):
    pass


class NamespaceEdit(NamespaceBase):
    pass


class Namespace(NamespaceBase):
    created_date: datetime
    users: list["NamespaceUser"]
    roles: list["NamespaceRole"]


class NamespaceUserBase(BaseModel):
    username: str
    role: str


class NamespaceUser(NamespaceUserBase):
    added_date: datetime
    added_by: str
    updated_date: datetime
    updated_by: str


class NamespaceUserCreate(NamespaceUserBase):
    pass


class NamespaceUserEdit(BaseModel):
    role: str


class NamespaceRoleBase(BaseModel):
    name: str
    permissions: list[model.PermissionCode]


class NamespaceRole(NamespaceRoleBase):
    name: str
    created_date: datetime
    created_by: str
    updated_date: datetime
    updated_by: str


class NamespaceRoleCreate(NamespaceRoleBase):
    pass


class NamespaceRoleEdit(NamespaceRoleBase):
    pass


class PackageBasic(BaseModel):
    name: str
    summary: str


class PackageBrief(PackageBasic):
    labels: list[str]
    namespace: str | None
    owners: list[str]
    updated_date: datetime
    downloads: int


class Package(PackageBrief):
    created_date: datetime
    created_by: str
    updated_by: str
    versions: list["PackageVersion"]
    tags: list["PackageTag"]


class PackageVersion(BaseModel):
    version: str
    downloads: int
    created_date: datetime
    created_by: str
    description: str
    repository: str | None
    tarball: str | None
    checksums: list["PackageChecksum"]
    dependencies: list["PackageDependency"]


class PackageChecksum(BaseModel):
    algorithm: str
    value: str


class PackageDependency(BaseModel):
    package: str
    spec: str


class PackageTag(BaseModel):
    name: str
    version: str


class Permission(BaseModel):
    code: str
    description: str

    class Config:
        orm_mode = True
