from .. import app, error, model, schema, storage
from ..db import SessionDep


def namespace_user_model_to_schema(user: model.NamespaceUser) -> schema.NamespaceUser:
    return schema.NamespaceUser(
        username=user.user.username,
        added_date=user.added_date,
        added_by=user.added_by.username,
        updated_date=user.updated_date,
        updated_by=user.updated_by.username,
        role=user.role.name,
    )


def namespace_role_model_to_schema(role: model.NamespaceRole) -> schema.NamespaceRole:
    return schema.NamespaceRole(
        name=role.name,
        created_date=role.created_date,
        created_by=role.created_by.username,
        updated_date=role.updated_date,
        updated_by=role.updated_by.username,
        permissions=[permission.permission.code for permission in role.permissions],
    )


@app.get("/namespace/{namespace}")
def get_namespace(session: SessionDep, namespace: str) -> schema.Namespace:
    ns = storage.get_namespace(session, namespace)

    if ns is None:
        raise error.not_found()

    users = [namespace_user_model_to_schema(user) for user in ns.users]
    roles = [namespace_role_model_to_schema(role) for role in ns.roles]

    return schema.Namespace(
        name=namespace,
        description=ns.description,
        homepage=ns.homepage,
        created_date=ns.created_date,
        users=users,
        roles=roles,
    )


@app.get("/namespace/{namespace}/package")
def get_namespace_packages(
    session: SessionDep, namespace: str
) -> list[schema.PackageBasic]:
    packages = storage.get_namespace_packages(session, namespace)

    if packages is None:
        raise error.not_found()

    return [
        schema.PackageBasic(
            name=package.name,
            summary=package.summary,
        )
        for package in packages
    ]


@app.get("/namespace/{namespace}/user")
def get_namespace_users(
    session: SessionDep,
    namespace: str,
) -> list[schema.NamespaceUser]:
    ns = storage.get_namespace(session, namespace)

    if ns is None:
        raise error.not_found()

    return [namespace_user_model_to_schema(user) for user in ns.users]


@app.get("/namespace/{namespace}/user/{username}")
def get_namespace_user(
    session: SessionDep,
    namespace: str,
    username: str,
) -> schema.NamespaceUser:
    user = storage.get_namespace_user(session, namespace, username)

    if user is None:
        raise error.not_found()

    return namespace_user_model_to_schema(user)


@app.get("/namespace/{namespace}/role")
def get_namespace_roles(
    session: SessionDep,
    namespace: str,
) -> list[schema.NamespaceRole]:
    ns = storage.get_namespace(session, namespace)

    if ns is None:
        raise error.not_found()

    return [namespace_role_model_to_schema(role) for role in ns.roles]


@app.get("/namespace/{namespace}/role/{role}")
def get_namespace_role(
    session: SessionDep,
    namespace: str,
    role: str,
) -> schema.NamespaceRole:
    role_model = storage.get_namespace_role(session, namespace, role)

    if role_model is None:
        raise error.not_found()

    return namespace_role_model_to_schema(role_model)
