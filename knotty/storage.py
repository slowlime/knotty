from sqlalchemy import select
from sqlalchemy.orm import (
    Session,
    aliased,
    contains_eager,
    load_only,
    raiseload,
    selectinload,
    undefer,
)

from knotty import config

from . import model, schema


def get_user_model(session: Session, username: str) -> model.User | None:
    query = select(model.User).where(model.User.username == username)

    return session.scalar(query)


def get_user(session: Session, username: str) -> schema.FullUserInfo | None:
    user = get_user_model(session, username)

    if user is None:
        return None

    return schema.FullUserInfo(
        username=user.username,
        email=user.email,
        registered=user.registered,
        namespaces=get_user_namespaces(session, username),
        role=user.role,
    )


def get_user_registered(
    session: Session, username: str, email: str
) -> schema.UserRegistered:
    user = session.scalar(
        select(model.User.username, model.User.email).where(
            (model.User.username == username) | (model.User.email == email)
        )
    )

    match user:
        case (True, _):
            return schema.UserRegistered.username_taken

        case (_, True):
            return schema.UserRegistered.email_registered

        case _:
            return schema.UserRegistered.not_registered


def get_user_namespaces(session: Session, username: str) -> list[str]:
    return list(
        session.scalars(
            select(model.Namespace.namespace)
            .join_from(model.User, model.User.namespace_members)
            .where(model.User.username == username)
            .join(model.NamespaceUser.namespace)
        ).all()
    )


def create_user(session: Session, data: schema.UserCreate):
    user = model.User(**data.dict())
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
        homepage=namespace.homepage,
        created_date=namespace.created_date,
        users=users,
        roles=roles,
    )


def get_namespace_exists(session: Session, name: str) -> bool:
    return session.execute(
        select(
            select(model.Namespace).where(model.Namespace.namespace == name).exists()
        )
    ).scalar_one()


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
            permissions=[str(permission.code) for permission in role.permissions],
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
        permissions=[str(permission.code) for permission in role_model.permissions],
    )


def create_namespace(session: Session, data: schema.NamespaceCreate, owner: model.User):
    namespace = model.Namespace(
        name=data.name,
        description=data.description,
        homepage=data.homepage,
    )

    namespace_owner_permission = session.scalars(
        select(model.Permission)
        .filter_by(code=model.PermissionCode.namespace_owner)
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
            raiseload("*"),
        )
    )

    if package is None:
        return None

    return schema.Package(
        created_date=package.created_date,
        created_by=package.created_by.username,
        updated_by=package.updated_by.username,
        versions=[
            schema.PackageVersion(
                version=version.version,
                downloads=version.downloads,
                created_date=version.created_date,
                created_by=version.created_by.username,
                description=version.description,
                repository=version.repository,
                tarball=version.tarball,
                checksums=[
                    schema.PackageChecksum(
                        algorithm=checksum.algorithm,
                        value=checksum.value.hex(),
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
            for version in package.versions
        ],
        tags=[
            schema.PackageTag(
                name=tag.name,
                version=tag.version.version,
            )
            for tag in package.tags
        ],
        **to_package_brief(package).dict(),
    )


def get_permissions(session: Session) -> list[model.Permission]:
    query = select(model.Permission)

    return list(session.scalars(query).all())


def get_namespace_permissions(
    session: Session, namespace: str, username: str
) -> list[model.PermissionCode]:
    query = (
        select(model.Permission.code)
        .join_from(model.User, model.User.namespace_members)
        .where(model.User.username == username)
        .join(model.NamespaceUser.namespace)
        .where(model.Namespace.namespace == namespace)
        .join(model.NamespaceUser.role)
        .join(model.NamespaceRole.permissions)
    )

    return list(session.scalars(query).all())
