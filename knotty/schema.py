from datetime import datetime
from enum import Enum
from typing import Annotated

import semver
from pydantic import (
    AnyHttpUrl,
    AnyUrl,
    BaseModel,
    ConstrainedStr,
    EmailStr,
    Field,
    validator,
)

from knotty import model

USERNAME_REGEX = r"^[a-zA-Z][a-zA-Z0-9-]*$"
NAMESPACE_NAME_REGEX = r"^[a-zA-Z][a-zA-Z0-9-]*$"
NAMESPACE_ROLE_REGEX = r"^[a-zA-Z][a-zA-Z0-9-]*$"
PACKAGE_REGEX = r"^[a-z][a-z0-9-]*$"
PACKAGE_LABEL_REGEX = r"^[a-z][a-z0-9-]*$"
PACKAGE_TAG_REGEX = r"^[a-z][a-z0-9-]*$"

Username = Annotated[str, Field(min_length=1, max_length=32, regex=USERNAME_REGEX)]
Email = Annotated[EmailStr, Field(max_length=64)]
NamespaceName = Annotated[
    str, Field(min_length=1, max_length=32, regex=NAMESPACE_NAME_REGEX)
]
NamespaceRoleName = Annotated[
    str, Field(min_length=1, max_length=32, regex=NAMESPACE_ROLE_REGEX)
]
PackageName = Annotated[str, Field(min_length=1, max_length=32, regex=PACKAGE_REGEX)]
PackageLabel = Annotated[
    str, Field(min_length=1, max_length=32, regex=PACKAGE_LABEL_REGEX)
]
PackageDependencySpec = Annotated[str, Field(min_length=1, max_length=40)]
PackageTagName = Annotated[
    str, Field(min_length=1, max_length=32, regex=PACKAGE_TAG_REGEX)
]


class ChecksumValue(ConstrainedStr):
    to_lower = True
    regex = r"^[a-f0-9]+$"


class Version(semver.version.Version):
    @classmethod
    def _parse(cls, version):
        return cls.parse(version)

    @classmethod
    def __get_validators__(cls):
        yield cls._parse

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(examples=["1.0.2", "2.15.3-alpha", "21.3.15-beta+12345"])


class WithId(BaseModel):
    id: int


class UserRegistered(Enum):
    not_registered = 0
    username_taken = 1
    email_registered = 2


class UserInfo(BaseModel):
    username: Username
    email: Email
    registered: datetime
    namespaces: list[str]


class FullUserInfo(UserInfo, WithId):
    role: model.UserRole


class AuthToken(BaseModel):
    token_type: str = "bearer"
    access_token: str


class UserRegister(BaseModel):
    username: Username
    email: Email
    password: Annotated[str, Field(max_length=1024)]


class UserCreate(BaseModel):
    username: str
    email: str
    pwhash: str
    registered: datetime


class NamespaceBase(BaseModel):
    name: NamespaceName
    description: Annotated[str, Field(max_length=131072)]
    homepage: Annotated[AnyHttpUrl, Field(max_length=2048)] | None


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
    name: NamespaceRoleName
    permissions: list[model.PermissionCode]


class NamespaceRole(NamespaceRoleBase):
    created_date: datetime
    created_by: str
    updated_date: datetime
    updated_by: str


class NamespaceRoleCreate(NamespaceRoleBase):
    pass


class NamespaceRoleEdit(NamespaceRoleBase):
    pass


class PackageBasic(BaseModel):
    name: PackageName
    summary: Annotated[str, Field(max_length=256)]


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
    labels: set[PackageLabel]
    owners: set[str]
    versions: list["PackageVersionCreate"]
    tags: list["PackageTag"]

    @validator("versions")
    def versions_must_not_repeat(
        cls, v: list["PackageVersionCreate"]
    ) -> list["PackageVersionCreate"]:
        versions = set[Version]()

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
    labels: set[PackageLabel]
    owners: set[str]


class PackageVersionBase(BaseModel):
    version: Version
    description: Annotated[str, Field(max_length=131072)]
    repository: Annotated[AnyUrl, Field(max_length=2048)] | None
    tarball: Annotated[AnyUrl, Field(max_length=2048)] | None
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
    value: ChecksumValue

    @validator("value")
    def length_must_be_valid(cls, v, values):
        expected_len = values["algorithm"].length

        if len(v) != expected_len:
            raise ValueError(f"invalid length: expected {expected_len} bytes")

        return v


class PackageDependency(BaseModel):
    package: str
    spec: PackageDependencySpec


class PackageTag(BaseModel):
    name: PackageTagName
    version: str


class Permission(BaseModel):
    code: str
    description: str

    class Config:
        orm_mode = True
