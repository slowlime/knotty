from fastapi import Depends
from .. import app, error, schema, storage
from ..db import SessionDep


def check_namespace_exists(session: SessionDep, namespace: str):
    if not storage.get_namespace_exists(session, namespace):
        raise error.not_found()


@app.get("/namespace/{namespace}")
def get_namespace(session: SessionDep, namespace: str) -> schema.Namespace:
    ns = storage.get_namespace(session, namespace)

    if ns is None:
        raise error.not_found()

    return ns


@app.get(
    "/namespace/{namespace}/package", dependencies=[Depends(check_namespace_exists)]
)
def get_namespace_packages(
    session: SessionDep, namespace: str
) -> list[schema.PackageBasic]:
    return storage.get_namespace_packages(session, namespace)


@app.get("/namespace/{namespace}/user", dependencies=[Depends(check_namespace_exists)])
def get_namespace_users(
    session: SessionDep,
    namespace: str,
) -> list[schema.NamespaceUser]:
    return storage.get_namespace_users(session, namespace)


@app.get("/namespace/{namespace}/user/{username}")
def get_namespace_user(
    session: SessionDep,
    namespace: str,
    username: str,
) -> schema.NamespaceUser:
    user = storage.get_namespace_user(session, namespace, username)

    if user is None:
        raise error.not_found()

    return user


@app.get("/namespace/{namespace}/role", dependencies=[Depends(check_namespace_exists)])
def get_namespace_roles(
    session: SessionDep,
    namespace: str,
) -> list[schema.NamespaceRole]:
    return storage.get_namespace_roles(session, namespace)


@app.get("/namespace/{namespace}/role/{role}")
def get_namespace_role(
    session: SessionDep,
    namespace: str,
    role: str,
) -> schema.NamespaceRole:
    result = storage.get_namespace_role(session, namespace, role)

    if result is None:
        raise error.not_found()

    return result
