from collections.abc import Iterable
import logging
from typing import Sequence
from pydantic import validate_model
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import (
    Session,
    aliased,
    contains_eager,
    defer,
    joinedload,
    load_only,
    raiseload,
    selectinload,
    undefer,
)
from sqlalchemy.sql.base import ExecutableOption

from knotty.config import config

from . import model, schema


logger = logging.getLogger(__name__)


def get_user_model(session: Session, username: str) -> model.User | None:
    return session.scalar(select(model.User).filter_by(username=username))


def get_user_exists(session: Session, username: str) -> bool:
    return session.scalars(
        select(select(model.User).filter_by(username=username).exists())
    ).one()


def get_user(session: Session, username: str) -> schema.FullUserInfo | None:
    user = get_user_model(session, username)

    if user is None:
        return None

    return schema.FullUserInfo(
        username=user.username,
        email=user.email,  # type: ignore
        registered=user.registered,
        namespaces=get_user_namespaces(session, username),
        id=user.id,
        role=user.role,
    )


def get_user_registered(
    session: Session, username: str, email: str
) -> schema.UserRegistered:
    username_eq = model.User.username == username
    email_eq = model.User.email == email

    user = session.execute(
        select(username_eq, email_eq).where(username_eq | email_eq)
    ).one_or_none()

    if user is None:
        return schema.UserRegistered.not_registered

    match user.tuple():
        case (True, _):
            return schema.UserRegistered.username_taken

        case (_, True):
            return schema.UserRegistered.email_registered

        case _:
            return schema.UserRegistered.not_registered


def get_unknown_users(session: Session, users: set[str]) -> list[str]:
    return list(
        users
        - set(
            session.scalars(
                select(model.User.username).where(model.User.username.in_(users))
            ).all()
        )
    )


def get_user_namespaces(session: Session, username: str) -> list[str]:
    return list(
        session.scalars(
            select(model.Namespace.namespace)
            .join_from(model.User, model.User.namespace_memberships)
            .where(model.User.username == username)
            .join(model.NamespaceUser.namespace)
        ).all()
    )


def create_user(session: Session, data: schema.UserCreate):
    user = model.User(role=model.UserRole.regular, **data.dict())
    session.add(user)


def get_namespace_model(session: Session, name: str) -> model.Namespace | None:
    query = select(model.Namespace).where(model.Namespace.namespace == name)

    return session.scalar(query)


def get_namespace(session: Session, name: str) -> schema.Namespace | None:
    namespace = get_namespace_model(session, name)

    if namespace is None:
        return None

    users = get_namespace_users(session, name)
    roles = get_namespace_roles(session, name)

    return schema.Namespace(
        name=namespace.namespace,
        description=namespace.description,
        homepage=namespace.homepage,  # type: ignore
        created_date=namespace.created_date,
        users=users,
        roles=roles,
    )


def get_namespace_id(session: Session, name: str) -> int | None:
    return session.scalar(
        select(model.Namespace.id).where(model.Namespace.namespace == name)
    )


def get_namespace_exists(session: Session, name: str) -> bool:
    return get_namespace_id(session, name) is not None


def create_namespace(session: Session, data: schema.NamespaceCreate, owner: model.User):
    namespace = model.Namespace(
        name=data.name,
        description=data.description,
        homepage=data.homepage,
    )

    namespace_owner_permission = session.scalars(
        select(model.Permission).filter_by(code=model.PermissionCode.namespace_owner)
    ).one()
    owner_role = model.NamespaceRole(
        name=config.default_names.namespace_owner_role,
        created_by=owner,
        updated_by=owner,
        namespace=namespace,
    )
    owner_role.permissions.append(namespace_owner_permission)

    user = model.NamespaceUser(
        user=owner,
        namespace=namespace,
        role=owner_role,
        added_by=owner,
        updated_by=owner,
    )

    session.add_all([namespace, user])


def edit_namespace(session: Session, name: str, data: schema.NamespaceEdit):
    namespace = get_namespace_model(session, name)
    assert namespace is not None

    namespace.namespace = data.name
    namespace.description = data.description
    namespace.homepage = data.homepage


def delete_namespace(session: Session, name: str):
    namespace = get_namespace_model(session, name)
    assert namespace is not None

    session.delete(namespace)


def get_namespace_owners(session: Session, namespace_id: int) -> list[str]:
    return list(
        session.scalars(
            select(model.User.username)
            .join_from(model.Namespace, model.Namespace.users)
            .where(model.Namespace.id == namespace_id)
            .where(
                model.NamespaceUser.role_id.in_(
                    select(model.NamespaceRole.id)
                    .where(model.NamespaceRole.namespace_id == namespace_id)
                    .join(model.NamespaceRole.permissions)
                    .where(
                        model.Permission.code == model.PermissionCode.namespace_owner
                    )
                    .distinct()
                )
            )
            .join(model.NamespaceUser.user)
        ).all()
    )


def get_namespace_users(session: Session, name: str) -> list[schema.NamespaceUser]:
    username_alias = aliased(model.User)
    added_by_alias = aliased(model.User)
    updated_by_alias = aliased(model.User)

    return list(
        schema.NamespaceUser.from_orm(user)
        for user in session.execute(
            select(
                username_alias.username.label("username"),
                model.NamespaceUser.added_date,
                added_by_alias.username.label("added_by"),
                model.NamespaceUser.updated_date,
                updated_by_alias.username.label("updated_by"),
                model.NamespaceRole.name,
            )
            .join(model.NamespaceUser.namespace)
            .where(model.Namespace.namespace == name)
            .join(model.NamespaceUser.user.of_type(username_alias))
            .join(model.NamespaceUser.added_by.of_type(added_by_alias))
            .join(model.NamespaceUser.updated_by.of_type(updated_by_alias))
            .join(model.NamespaceUser.role)
        ).all()
    )


def get_namespace_roles(session: Session, name: str) -> list[schema.NamespaceRole]:
    roles = session.scalars(
        select(model.NamespaceRole)
        .join(model.NamespaceRole.namespace)
        .where(model.Namespace.namespace == name)
        .options(
            selectinload(model.NamespaceRole.created_by).load_only(
                model.User.username, raiseload=True
            ),
            selectinload(model.NamespaceRole.updated_by).load_only(
                model.User.username, raiseload=True
            ),
            selectinload(model.NamespaceRole.permissions).load_only(
                model.Permission.code, raiseload=True
            ),
            load_only(
                model.NamespaceRole.name,
                model.NamespaceRole.created_date,
                model.NamespaceRole.created_by,
                model.NamespaceRole.updated_date,
                model.NamespaceRole.updated_by,
                model.NamespaceRole.permissions,
            ),
            raiseload("*"),
        )
    ).all()

    return [
        schema.NamespaceRole(
            name=role.name,
            created_date=role.created_date,
            created_by=role.created_by.username,
            updated_date=role.updated_date,
            updated_by=role.updated_by.username,
            permissions=[permission.code for permission in role.permissions],
        )
        for role in roles
    ]


def get_namespace_packages(session: Session, name: str) -> list[schema.PackageBasic]:
    return [
        schema.PackageBasic.from_orm(package)
        for package in session.scalars(
            select(model.Package)
            .join(model.Namespace.packages)
            .where(model.Namespace.namespace == name)
            .options(
                load_only(model.Package.name, model.Package.summary),
                raiseload("*"),
            )
        ).all()
    ]


def get_namespace_user(
    session: Session, namespace: str, username: str
) -> schema.NamespaceUser | None:
    user = session.scalar(
        select(model.NamespaceUser)
        .join(model.NamespaceUser.namespace)
        .where(model.Namespace.namespace == namespace)
        .join(model.NamespaceUser.user)
        .where(model.User.username == username)
        .options(
            selectinload(model.NamespaceUser.user).load_only(model.User.username),
            selectinload(model.NamespaceUser.added_by).load_only(model.User.username),
            selectinload(model.NamespaceUser.updated_by).load_only(model.User.username),
            raiseload("*"),
        )
    )

    if user is None:
        return None

    return schema.NamespaceUser(
        username=user.user.username,
        added_date=user.added_date,
        added_by=user.added_by.username,
        updated_date=user.updated_date,
        updated_by=user.updated_by.username,
        role=str(user.role),
    )


def get_namespace_user_model(
    session: Session, namespace_id: int, username: str
) -> model.NamespaceUser | None:
    return session.scalar(
        select(model.NamespaceUser)
        .filter_by(namespace_id=namespace_id)
        .join(model.NamespaceUser.user)
        .where(model.User.username == username)
    )


def get_namespace_user_exists(
    session: Session, namespace_id: int, username: str
) -> bool:
    return session.scalars(
        select(
            select(model.NamespaceUser)
            .filter_by(namespace_id=namespace_id)
            .join(model.NamespaceUser.user)
            .where(model.User.username == username)
            .exists()
        )
    ).one()


def get_namespace_user_permissions(
    session: Session, namespace: str, username: str
) -> list[model.PermissionCode]:
    query = (
        select(model.Permission.code)
        .join_from(model.User, model.User.namespace_memberships)
        .where(model.User.username == username)
        .join(model.NamespaceUser.namespace)
        .where(model.Namespace.namespace == namespace)
        .join(model.NamespaceUser.role)
        .join(model.NamespaceRole.permissions)
    )

    return list(session.scalars(query).all())


def create_namespace_user(
    session: Session,
    namespace_id: int,
    data: schema.NamespaceUserCreate,
    added_by: model.User,
):
    user = get_user_model(session, data.username)
    assert user is not None

    role = get_namespace_role_model(session, namespace_id, data.role)
    assert role is not None

    ns_user = model.NamespaceUser(
        user=user,
        namespace_id=namespace_id,
        role=role,
        added_by=added_by,
        updated_by=added_by,
    )
    session.add(ns_user)


def edit_namespace_user(
    session: Session,
    namespace_id: int,
    username: str,
    data: schema.NamespaceUserEdit,
    updated_by: model.User,
):
    user = get_user_model(session, username)
    assert user is not None

    role = get_namespace_role_model(session, namespace_id, data.role)
    assert role is not None

    ns_user = get_namespace_user_model(session, namespace_id, username)
    assert ns_user is not None

    ns_user.role = role
    ns_user.updated_by = updated_by


def delete_namespace_user(
    session: Session,
    namespace_id: int,
    username: str,
):
    ns_user = get_namespace_user_model(session, namespace_id, username)
    assert ns_user is not None

    session.delete(ns_user)


def get_namespace_role(
    session: Session,
    namespace: str,
    role: str,
) -> schema.NamespaceRole | None:
    created_by_alias = aliased(model.User)
    updated_by_alias = aliased(model.User)

    role_model = session.scalar(
        select(model.NamespaceRole)
        .where(model.NamespaceRole.name == role)
        .join(model.NamespaceRole.namespace)
        .where(model.Namespace.namespace == namespace)
        .join(model.NamespaceRole.created_by.of_type(created_by_alias))
        .join(model.NamespaceRole.updated_by.of_type(updated_by_alias))
        .options(
            contains_eager(
                model.NamespaceRole.created_by.of_type(created_by_alias)
            ).load_only(model.User.username, raiseload=True),
            contains_eager(
                model.NamespaceRole.updated_by.of_type(updated_by_alias)
            ).load_only(model.User.username, raiseload=True),
            undefer(model.NamespaceRole.permissions).load_only(
                model.Permission.code, raiseload=True
            ),
        )
    )

    if role_model is None:
        return None

    return schema.NamespaceRole(
        name=role_model.name,
        created_date=role_model.created_date,
        created_by=role_model.created_by.username,
        updated_date=role_model.updated_date,
        updated_by=role_model.updated_by.username,
        permissions=[permission.code for permission in role_model.permissions],
    )


def get_namespace_role_model(
    session: Session, namespace_id: int, role: str
) -> model.NamespaceRole | None:
    return session.scalar(
        select(model.NamespaceRole).filter_by(namespace_id=namespace_id, name=role)
    )


def get_namespace_role_exists(session: Session, name: str | int, role: str) -> bool:
    query = select(model.NamespaceRole).join_from(
        model.Namespace, model.Namespace.roles
    )

    match name:
        case str(name):
            query = query.where(model.Namespace.namespace == name)

        case int(namespace_id):
            query = query.where(model.Namespace.id == namespace_id)

    return session.scalars(
        select(query.where(model.NamespaceRole.name == role).exists())
    ).one()


def create_namespace_role(
    session: Session,
    namespace_id: int,
    data: schema.NamespaceRoleCreate,
    created_by: model.User,
):
    permissions = session.scalars(
        select(model.Permission).where(model.Permission.code.in_(data.permissions))
    ).all()

    role = model.NamespaceRole(
        namespace_id=namespace_id,
        name=data.name,
        created_by=created_by,
        updated_by=created_by,
        permissions=permissions,
    )

    session.add(role)


def edit_namespace_role(
    session: Session,
    namespace_id: int,
    role: str,
    data: schema.NamespaceRoleEdit,
    updated_by: model.User,
):
    permissions = session.scalars(
        select(model.Permission).where(model.Permission.code.in_(data.permissions))
    ).all()

    role_model = get_namespace_role_model(session, namespace_id, role)
    assert role_model is not None

    role_model.name = data.name
    role_model.updated_by = updated_by

    role_model.permissions.clear()
    role_model.permissions.extend(permissions)


def delete_namespace_role(
    session: Session,
    namespace_id: int,
    role: str,
):
    role_model = get_namespace_role_model(session, namespace_id, role)
    assert role_model is not None

    session.delete(role_model)


def get_namespace_role_permissions(
    session: Session,
    name: str,
    role: str,
) -> list[model.PermissionCode] | None:
    if not get_namespace_role_exists(session, name, role):
        return None

    return list(
        session.scalars(
            select(model.Permission.code)
            .join_from(model.Namespace, model.Namespace.roles)
            .where(model.Namespace.namespace == name)
            .where(model.NamespaceRole.name == role)
            .join(model.NamespaceRole.permissions)
        ).all()
    )


def get_namespace_role_users(
    session: Session,
    namespace_id: int,
    role: str,
) -> list[str] | None:
    if not get_namespace_role_exists(session, namespace_id, role):
        return None

    return list(
        session.scalars(
            select(model.User.username)
            .join_from(model.NamespaceRole, model.NamespaceRole.users)
            .where(model.NamespaceRole.name == role)
            .where(model.NamespaceRole.namespace_id == namespace_id)
            .join(model.NamespaceUser.user)
        ).all()
    )


def get_namespace_role_empty(
    session: Session,
    namespace_id: int,
    role: str,
) -> bool:
    return session.scalars(
        select(
            ~select(model.NamespaceUser)
            .join(model.NamespaceUser.role)
            .where(model.NamespaceUser.namespace_id == namespace_id)
            .where(model.NamespaceRole.name == role)
            .exists()
        )
    ).one()


def to_package_brief(package: model.Package) -> schema.PackageBrief:
    return schema.PackageBrief(
        name=package.name,
        summary=package.summary,
        labels=[label.name for label in package.labels],
        namespace=package.namespace.namespace
        if package.namespace is not None
        else None,
        owners=[owner.username for owner in package.owners],
        updated_date=package.updated_date,
        downloads=package.downloads,
    )


def get_packages(session: Session) -> list[schema.PackageBrief]:
    packages = session.scalars(
        select(model.Package).options(
            selectinload(model.Package.labels),
            selectinload(model.Package.owners).load_only(
                model.User.username, raiseload=True
            ),
            selectinload(model.Package.namespace).load_only(model.Namespace.namespace),
            undefer(model.Package.downloads),
        )
    ).all()

    return [to_package_brief(package) for package in packages]


def to_package_version(version: model.PackageVersion) -> schema.PackageVersion:
    return schema.PackageVersion(
        version=version.version,  # type: ignore
        downloads=version.downloads,
        created_date=version.created_date,
        created_by=version.created_by.username,
        description=version.description,
        repository=version.repository,  # type: ignore
        tarball=version.tarball,  # type: ignore
        checksums=[
            schema.PackageChecksum(
                algorithm=checksum.algorithm,
                value=checksum.value.hex(),  # type: ignore
            )
            for checksum in version.checksums
        ],
        dependencies=[
            schema.PackageDependency(
                package=dep.dep_package.name,
                spec=dep.spec,
            )
            for dep in version.dependencies
        ],
    )


def get_package_ids(session: Session, packages: list[str]) -> dict[str, int]:
    return {
        package.name: package.id
        for package in session.execute(
            select(model.Package.id, model.Package.name).where(
                model.Package.name.in_(packages)
            )
        ).all()
    }


def get_package(session: Session, name: str) -> schema.Package | None:
    package = session.scalar(
        select(model.Package)
        .where(model.Package.name == name)
        .options(
            selectinload(model.Package.labels),
            selectinload(model.Package.owners).load_only(model.User.username),
            selectinload(model.Package.namespace).load_only(model.Namespace.namespace),
            undefer(model.Package.downloads),
            selectinload(model.Package.created_by).load_only(model.User.username),
            selectinload(model.Package.updated_by).load_only(model.User.username),
            selectinload(model.Package.versions)
            .joinedload(model.PackageVersion.created_by)
            .load_only(model.User.username),
            selectinload(model.Package.versions).selectinload(
                model.PackageVersion.checksums
            ),
            selectinload(model.Package.versions)
            .selectinload(model.PackageVersion.dependencies)
            .joinedload(model.PackageVersionDependency.dep_package)
            .load_only(model.Package.name),
            selectinload(model.Package.tags)
            .joinedload(model.PackageTag.package)
            .load_only(model.Package.name),
            selectinload(model.Package.tags)
            .joinedload(model.PackageTag.version)
            .load_only(model.PackageVersion.version),
            raiseload("*"),
        )
    )

    if package is None:
        return None

    return schema.Package(
        created_date=package.created_date,
        created_by=package.created_by.username,
        updated_by=package.updated_by.username,
        versions=[to_package_version(version) for version in package.versions],
        tags=[
            schema.PackageTag(
                name=tag.name,
                version=tag.version.version,
            )
            for tag in package.tags
        ],
        **to_package_brief(package).dict(),
    )


def get_package_exists(session: Session, package: str) -> bool:
    return session.scalars(
        select(select(model.Package).filter_by(name=package).exists())
    ).one()


def get_package_model(session: Session, package: str) -> model.Package | None:
    return session.scalar(select(model.Package).filter_by(name=package))


def get_package_brief(session: Session, package: str) -> schema.PackageBrief | None:
    pkg_model = get_package_model(session, package)

    if pkg_model is None:
        return None

    return to_package_brief(pkg_model)


def make_package_version_checksum_model(
    data: schema.PackageChecksum,
) -> model.PackageVersionChecksum:
    return model.PackageVersionChecksum(
        algorithm=data.algorithm,
        value=bytes.fromhex(data.value),
    )


def make_package_version_dependency_model(
    dependencies: dict[str, int],
    data: schema.PackageDependency,
) -> model.PackageVersionDependency:
    return model.PackageVersionDependency(
        dep_package_id=dependencies[data.package],
        spec=data.spec,
    )


def make_package_version_model(
    dependencies: dict[str, int],
    data: schema.PackageVersionCreate,
    created_by: model.User,
) -> model.PackageVersion:
    return model.PackageVersion(
        version=str(data.version),
        created_by=created_by,
        description=data.description,
        repository=data.repository,
        tarball=data.tarball,
        checksums=[
            make_package_version_checksum_model(checksum) for checksum in data.checksums
        ],
        dependencies=[
            make_package_version_dependency_model(dependencies, dep)
            for dep in data.dependencies
        ],
    )


def create_package(
    session: Session, data: schema.PackageCreate, created_by: model.User
):
    package = model.Package(
        name=data.name,
        summary=data.summary,
        created_by=created_by,
        updated_by=created_by,
    )

    if data.namespace is not None:
        namespace = get_namespace_model(session, data.namespace)
        assert namespace is not None

        package.namespace = namespace

    labels = get_or_create_labels(session, data.labels)
    package.labels.extend(labels)

    owners = session.scalars(
        select(model.User)
        .options(defer("*"))
        .where(model.User.username.in_(data.owners))
    ).all()
    package.owners.extend(owners)

    dependencies = get_package_ids(
        session,
        [dep.package for version in data.versions for dep in version.dependencies],
    )
    versions = {}

    for version_data in data.versions:
        version = make_package_version_model(dependencies, version_data, created_by)
        package.versions.append(version)
        versions[version.version] = version

    for tag in data.tags:
        package.tags.append(
            model.PackageTag(
                name=tag.name,
                version=versions[tag.version],
            )
        )

    session.add(package)


def edit_package(
    session: Session, package: str, data: schema.PackageEdit, updated_by: model.User
):
    pkg_model = get_package_model(session, package)
    assert pkg_model is not None

    pkg_model.name = data.name
    pkg_model.summary = data.summary
    pkg_model.updated_by = updated_by

    if data.namespace is not None:
        namespace = get_namespace_model(session, data.namespace)
    else:
        namespace = None

    pkg_model.namespace = namespace

    labels = get_or_create_labels(session, data.labels)
    pkg_model.labels.clear()
    pkg_model.labels.extend(labels)

    owners = session.scalars(
        select(model.User)
        .options(defer("*"))
        .where(model.User.username.in_(data.owners))
    ).all()
    pkg_model.owners.clear()
    pkg_model.owners.extend(owners)

    session.flush()
    purge_garbage_labels(session)


def delete_package(session: Session, package: str):
    pkg_model = get_package_model(session, package)
    assert pkg_model is not None

    session.delete(pkg_model)


def get_unknown_packages(session: Session, packages: set[str]) -> list[str]:
    return list(
        packages
        - set(
            session.scalars(
                select(model.Package.name).where(model.Package.name.in_(packages))
            ).all()
        )
    )


def get_package_owner_exists(session: Session, package: str, username: str) -> bool:
    return session.scalars(
        select(
            select(model.User)
            .filter_by(username=username)
            .join(model.User.packages)
            .where(model.Package.name == package)
            .exists()
        )
    ).one()


def get_package_namespace(session: Session, package: str) -> str | None:
    return session.scalar(
        select(model.Namespace.namespace)
        .join_from(model.Package, model.Package.namespace)
        .where(model.Package.name == package)
    )


def get_package_has_dependents(session: Session, package: str) -> bool:
    package_alias = aliased(model.Package)
    dependent_package_alias = aliased(model.Package)

    return session.scalars(
        select(
            select(dependent_package_alias.name)
            .join_from(
                package_alias, model.Package.dependents.of_type(dependent_package_alias)
            )
            .where(package_alias.name == package)
            .exists()
        )
    ).one()


def get_package_id(session: Session, package: str) -> int | None:
    return session.scalar(select(model.Package.id).filter_by(name=package))


def get_package_version_options() -> list[ExecutableOption]:
    return [
        joinedload(model.PackageVersion.created_by).load_only(model.User.username),
        selectinload(model.PackageVersion.checksums),
        selectinload(model.PackageVersion.dependencies)
        .joinedload(model.PackageVersionDependency.dep_package)
        .load_only(model.Package.name),
        raiseload("*"),
    ]


def get_package_versions(
    session: Session, package_id: int
) -> list[schema.PackageVersion]:
    versions = session.scalars(
        select(model.PackageVersion)
        .filter_by(package_id=package_id)
        .options(*get_package_version_options())
    ).all()

    return [to_package_version(version) for version in versions]


def get_package_version(
    session: Session, package_id: int, version: str
) -> schema.PackageVersion | None:
    version_model = session.scalar(
        select(model.PackageVersion)
        .filter_by(package_id=package_id, version=version)
        .options(*get_package_version_options())
    )

    if version_model is None:
        return None

    return to_package_version(version_model)


def get_package_version_model(
    session: Session, package_id: int, version: str
) -> model.PackageVersion | None:
    return session.scalar(
        select(model.PackageVersion).filter_by(package_id=package_id, version=version)
    )


def create_package_version(
    session: Session,
    package_id: int,
    data: schema.PackageVersionCreate,
    created_by: model.User,
):
    package = session.get(model.Package, package_id)
    assert package is not None

    dependencies = get_package_ids(session, [dep.package for dep in data.dependencies])
    version = make_package_version_model(dependencies, data, created_by)
    package.versions.append(version)


def edit_package_version(
    session: Session,
    package_id: int,
    version: str,
    data: schema.PackageVersionEdit,
    updated_by: model.User,
):
    package = session.get(model.Package, package_id)
    assert package is not None

    version_model = get_package_version_model(session, package_id, version)
    assert version_model is not None

    version_model.version = str(data.version)
    version_model.description = data.description
    version_model.repository = data.repository
    version_model.tarball = data.tarball

    version_model.checksums.clear()
    version_model.checksums.extend(
        make_package_version_checksum_model(checksum) for checksum in data.checksums
    )

    dependencies = get_package_ids(session, [dep.package for dep in data.dependencies])
    version_model.dependencies.clear()
    version_model.dependencies.extend(
        make_package_version_dependency_model(dependencies, dep)
        for dep in data.dependencies
    )

    package.updated_by = updated_by


def delete_package_version(session: Session, package_id: int, version: str):
    package_version = get_package_version_model(session, package_id, version)
    assert package_version is not None

    session.delete(package_version)


def get_package_version_exists(session: Session, package_id: int, version: str) -> bool:
    return session.scalars(
        select(
            select(model.PackageVersion)
            .filter_by(package_id=package_id, version=version)
            .exists()
        )
    ).one()


def get_package_version_is_tagged(
    session: Session, package_id: int, version: str
) -> bool:
    return session.scalars(
        select(
            select(model.PackageTag)
            .select_from(model.PackageVersion)
            .filter_by(package_id=package_id, version=version)
            .join(model.PackageVersion.tagged_as)
            .exists()
        )
    ).one()


def get_package_tags(session: Session, package_id: int) -> list[schema.PackageTag]:
    return [
        schema.PackageTag(
            name=tag.name,
            version=tag.version,
        )
        for tag in session.scalars(
            select(model.PackageTag.name, model.PackageVersion.version)
            .where(model.PackageTag.package_id == package_id)
            .join(model.PackageTag.version)
        ).all()
    ]


def get_package_tag_model(
    session: Session, package_id: int, tag: str
) -> model.PackageTag | None:
    return session.scalar(
        select(model.PackageTag).filter_by(package_id=package_id, name=tag)
    )


def get_package_tag_exists(session: Session, package_id: int, tag: str) -> bool:
    return session.scalars(
        select(
            select(model.PackageTag).filter_by(package_id=package_id, name=tag).exists()
        )
    ).one()


def get_package_tag(
    session: Session, package_id: int, tag: str
) -> schema.PackageTag | None:
    result = session.scalar(
        select(model.PackageTag.name, model.PackageVersion.version)
        .select_from(model.PackageTag)
        .filter_by(package_id=package_id, name=tag)
        .join(model.PackageTag.version)
    )

    if result is None:
        return None

    return schema.PackageTag(
        name=result.name,
        version=result.version,
    )


def create_package_tag(session: Session, package_id: int, data: schema.PackageTag):
    package = session.get(model.Package, package_id)
    assert package is not None

    version = get_package_version_model(session, package_id, data.version)
    assert version is not None

    package.tags.append(
        model.PackageTag(
            name=data.name,
            version=version,
        )
    )


def edit_package_tag(
    session: Session, package_id: int, tag: str, data: schema.PackageTag
):
    tag_model = get_package_tag_model(session, package_id, tag)
    assert tag_model is not None

    version = get_package_version_model(session, package_id, data.version)
    assert version is not None

    tag_model.name = data.name
    tag_model.version = version


def delete_package_tag(session: Session, package_id: int, tag: str):
    tag_model = get_package_tag_model(session, package_id, tag)
    assert tag_model is not None

    session.delete(tag_model)


def get_permissions(session: Session) -> list[model.Permission]:
    query = select(model.Permission)

    return list(session.scalars(query).all())


def get_or_create_labels(
    session: Session, labels: Iterable[str]
) -> Sequence[model.Label]:
    return session.scalars(
        insert(model.Label)
        .on_conflict_do_nothing(index_elements=[model.Label.name])
        .returning(model.Label),
        [{"name": label} for label in labels],
    ).all()


def purge_garbage_labels(session: Session):
    session.execute(
        delete(model.Label).where(
            model.Label.id.in_(
                select(model.Label.id)
                .join(model.Label.packages, isouter=True)
                .where(model.Package.id == None)
            )
        )
    )
