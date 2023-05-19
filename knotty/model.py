from datetime import datetime
from enum import Enum
from typing import List
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Table,
    UniqueConstraint,
    func,
    select,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    column_property,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    pass


class UserRole(Enum):
    regular = "regular"
    admin = "admin"
    banned = "banned"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str]
    pwhash: Mapped[str]
    registered: Mapped[datetime]
    role: Mapped[UserRole]

    namespace_members: Mapped[List["NamespaceUser"]] = relationship(
        back_populates="user"
    )
    packages: Mapped[List["Package"]] = relationship(
        secondary=lambda: package_owner_table,
        back_populates="owners",
    )


class Namespace(Base):
    __tablename__ = "namespace"

    id: Mapped[int] = mapped_column(primary_key=True)
    namespace: Mapped[str] = mapped_column(unique=True)
    description: Mapped[str]
    homepage: Mapped[str | None]
    created_date: Mapped[datetime]

    users: Mapped[List["NamespaceUser"]] = relationship(
        back_populates="namespace", cascade="all, delete-orphan", passive_deletes=True
    )
    roles: Mapped[List["NamespaceRole"]] = relationship(
        back_populates="namespace", cascade="all, delete-orphan", passive_deletes=True
    )
    packages: Mapped[List["Package"]] = relationship(back_populates="namespace")


class NamespaceUser(Base):
    __tablename__ = "namespace_users"

    user_id: Mapped[int] = mapped_column(ForeignKey(User.id), primary_key=True)
    namespace_id: Mapped[int] = mapped_column(
        ForeignKey(Namespace.id, ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    role_id: Mapped[int] = mapped_column(ForeignKey("namespace_roles.id"))
    added_date: Mapped[datetime]
    added_by_user_id: Mapped[int] = mapped_column(ForeignKey(User.id))
    updated_date: Mapped[datetime]
    updated_by_user_id: Mapped[int] = mapped_column(ForeignKey(User.id))

    user: Mapped[User] = relationship(
        back_populates="namespace_members", foreign_keys=user_id
    )
    namespace: Mapped[Namespace] = relationship(back_populates="users")
    role: Mapped["NamespaceRole"] = relationship(back_populates="users")
    added_by: Mapped[User] = relationship(foreign_keys=added_by_user_id)
    updated_by: Mapped[User] = relationship(foreign_keys=updated_by_user_id)


class NamespaceRole(Base):
    __tablename__ = "namespace_roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    namespace_id: Mapped[int] = mapped_column(
        ForeignKey(Namespace.id, ondelete="CASCADE", onupdate="CASCADE")
    )
    name: Mapped[str]
    created_date: Mapped[datetime]
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey(User.id))
    updated_date: Mapped[datetime]
    updated_by_user_id: Mapped[int] = mapped_column(ForeignKey(User.id))

    namespace: Mapped[Namespace] = relationship(back_populates="roles")
    created_by: Mapped[User] = relationship(foreign_keys=created_by_user_id)
    updated_by: Mapped[User] = relationship(foreign_keys=updated_by_user_id)
    permissions: Mapped[List["Permission"]] = relationship(
        secondary=lambda: namespace_role_permission_table,
    )
    users: Mapped[List[NamespaceUser]] = relationship(
        back_populates="role"
    )

    __table_args__ = (UniqueConstraint("namespace_id", "name"),)


namespace_role_permission_table = Table(
    "namespace_role_permissions",
    Base.metadata,
    Column(
        "role_id",
        ForeignKey(NamespaceRole.id, ondelete="CASCADE", onupdated="CASCADE"),
        primary_key=True,
    ),
    Column("permission_id", ForeignKey("permissions.id"), primary_key=True),
)


class PermissionCode(Enum):
    namespace_owner = "namespace-owner"
    namespace_admin = "namespace-admin"
    namespace_edit = "namespace-edit"


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[PermissionCode] = mapped_column(unique=True)
    description: Mapped[str]


package_label_table = Table(
    "package_labels",
    Base.metadata,
    Column(
        "package_id",
        ForeignKey("packages.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    ),
    Column("label_id", ForeignKey("labels.id"), primary_key=True),
)

package_owner_table = Table(
    "package_owners",
    Base.metadata,
    Column(
        "package_id",
        Integer,
        ForeignKey("packages.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    ),
    Column("owner_id", ForeignKey(User.id), primary_key=True),
)


class Package(Base):
    __tablename__ = "packages"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    namespace_id: Mapped[int | None] = mapped_column(
        ForeignKey(Namespace.id, ondelete="SET NULL", onupdate="SET NULL")
    )
    summary: Mapped[str]
    created_date: Mapped[datetime]
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey(User.id))
    updated_date: Mapped[datetime]
    updated_by_user_id: Mapped[int] = mapped_column(ForeignKey(User.id))

    namespace: Mapped[Namespace | None] = relationship(back_populates="packages")
    created_by: Mapped[User] = relationship(foreign_keys=created_by_user_id)
    updated_by: Mapped[User] = relationship(foreign_keys=updated_by_user_id)
    labels: Mapped[List["Label"]] = relationship(
        back_populates="packages",
        cascade="all, delete-orphan",
        passive_deletes=True,
        secondary=package_label_table,
    )
    owners: Mapped[List[User]] = relationship(
        secondary=package_owner_table,
        back_populates="packages",
    )
    versions: Mapped[List["PackageVersion"]] = relationship(
        back_populates="package",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    dependents: Mapped[List["PackageVersionDependency"]] = relationship(
        back_populates="dep_package",
    )
    tags: Mapped[List["PackageTag"]] = relationship(
        back_populates="package",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # defined below
    downloads: Mapped[int]


class PackageVersion(Base):
    __tablename__ = "package_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    package_id: Mapped[int] = mapped_column(
        ForeignKey(Package.id, ondelete="CASCADE", onupdate="CASCADE")
    )
    version: Mapped[str]
    downloads: Mapped[int]
    created_date: Mapped[datetime]
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey(User.id))
    description: Mapped[str]
    repository: Mapped[str | None]
    tarball: Mapped[str | None]

    package: Mapped[Package] = relationship(back_populates="versions")
    created_by: Mapped[User] = relationship(foreign_keys=created_by_user_id)
    checksums: Mapped[List["PackageVersionChecksum"]] = relationship(
        back_populates="version",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    dependencies: Mapped[List["PackageVersionDependency"]] = relationship(
        back_populates="version",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    tagged_as: Mapped[List["PackageTag"]] = relationship(back_populates="version")

    __table_args__ = (UniqueConstraint("package_id", "version"),)


Package.downloads = column_property(
    select(func.sum(PackageVersion.downloads))
    .where(PackageVersion.package_id == Package.id)
    .scalar_subquery()
)


class PackageVersionChecksum(Base):
    __tablename__ = "package_version_checksums"

    version_id: Mapped[int] = mapped_column(
        ForeignKey(PackageVersion.id, ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    algorithm: Mapped[str] = mapped_column(primary_key=True)
    value: Mapped[bytes]

    version: Mapped[PackageVersion] = relationship(back_populates="checksums")


class PackageVersionDependency(Base):
    __tablename__ = "package_version_dependencies"

    version_id: Mapped[int] = mapped_column(
        ForeignKey(PackageVersion.id, ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    dep_package_id: Mapped[int] = mapped_column(
        ForeignKey(Package.id), primary_key=True
    )
    spec: Mapped[str]

    version: Mapped[PackageVersion] = relationship(back_populates="dependencies")
    dep_package: Mapped[Package] = relationship(back_populates="dependents")


class PackageTag(Base):
    __tablename__ = "package_tags"

    package_id: Mapped[int] = mapped_column(
        ForeignKey(Package.id, ondelete="CASCADE", onupdate="CASCADE"), primary_key=True
    )
    name: Mapped[str] = mapped_column(primary_key=True)
    version_id: Mapped[int] = mapped_column(ForeignKey(PackageVersion.id))

    package: Mapped[Package] = relationship(back_populates="tags")
    version: Mapped[PackageVersion] = relationship(back_populates="tagged_as")


class Label(Base):
    __tablename__ = "labels"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)

    packages: Mapped[List[Package]] = relationship(back_populates="labels")
