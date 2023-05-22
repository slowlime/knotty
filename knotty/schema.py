from datetime import datetime
from enum import Enum

from pydantic import BaseModel, validator

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


class PackageCreate(PackageBasic):
    namespace: str | None
    labels: set[str]
    owners: set[str]
    versions: list["PackageVersionCreate"]
    tags: list["PackageTag"]

    @validator("versions")
    def versions_must_not_repeat(
        cls, v: list["PackageVersionCreate"]
    ) -> list["PackageVersionCreate"]:
        versions = set[str]()

        for version in v:
            if version.version in versions:
                raise ValueError(
                    f"version {version.version} is specified multiple times"
                )

            versions.add(version.version)

        return v

    @validator("tags")
    def tags_must_not_repeat(cls, v: list["PackageTag"]) -> list["PackageTag"]:
        tags = set[str]()

        for tag in v:
            name = tag.name

            if name in tags:
                raise ValueError(f"tag {name} is specified multiple times")

            tags.add(name)

        return v

    @validator("tags", each_item=True)
    def tags_must_refer_to_valid_versions(
        cls,
        v: "PackageTag",
        values: dict,
    ) -> "PackageTag":
        if not any(v.version == version.version for version in values["version"]):
            raise ValueError("tag does not refer to valid version")

        return v


class PackageEdit(PackageBasic):
    namespace: str | None
    labels: set[str]
    owners: set[str]


class PackageVersionBase(BaseModel):
    version: str
    description: str
    repository: str | None
    tarball: str | None
    checksums: list["PackageChecksum"]
    dependencies: list["PackageDependency"]

    @validator("checksums")
    def checksums_dont_repeat(
        cls, v: list["PackageChecksum"]
    ) -> list["PackageChecksum"]:
        algorithms = set[model.ChecksumAlgorithm]()

        for checksum in v:
            algorithm = checksum.algorithm

            if algorithm in algorithms:
                raise ValueError(
                    f"checksum algorithm {algorithm} is specified multiple times"
                )

            algorithms.add(algorithm)

        return v

    @validator("dependencies")
    def dependencies_dont_repeat(
        cls, v: list["PackageDependency"]
    ) -> list["PackageDependency"]:
        deps = set[str]()

        for dep in v:
            pkg = dep.package

            if pkg in deps:
                raise ValueError(f"dependency {pkg} is specified multiple times")

            deps.add(pkg)

        return v


class PackageVersion(PackageVersionBase):
    downloads: int
    created_date: datetime
    created_by: str


class PackageVersionCreate(PackageVersionBase):
    pass


class PackageVersionEdit(PackageVersionBase):
    pass


class PackageChecksum(BaseModel):
    algorithm: model.ChecksumAlgorithm
    value: str

    @validator("value")
    def length_must_be_valid(cls, v, values):
        expected_len = values["algorithm"].length

        if len(v) != expected_len:
            raise ValueError(f"invalid length: expected {expected_len} bytes")

        return v


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
