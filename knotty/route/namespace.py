from typing import Annotated
from fastapi import Depends, status

from knotty import acl
from knotty.auth import AuthDep
from .. import app, error, schema, storage
from ..db import SessionDep


def check_namespace_exists(session: SessionDep, namespace: str):
    if not storage.get_namespace_exists(session, namespace):
        raise error.not_found()


@app.post("/namespace", status_code=status.HTTP_201_CREATED)
def create_namespace(
    session: SessionDep,
    body: schema.NamespaceCreate,
    auth: AuthDep,
    namespace_create_check: Annotated[bool | None, Depends(acl.can_add_namespace)],
):
    acl.require(namespace_create_check)

    if storage.get_namespace_exists(session, body.name):
        raise error.namespace_already_exists()

    storage.create_namespace(session, body, auth)
    session.commit()


@app.get("/namespace/{namespace}")
def get_namespace(session: SessionDep, namespace: str) -> schema.Namespace:
    ns = storage.get_namespace(session, namespace)

    if ns is None:
        raise error.not_found()

    return ns


@app.patch(
    "/namespace/{namespace}",
    dependencies=[Depends(check_namespace_exists)],
)
def edit_namespace(
    session: SessionDep,
    namespace: str,
    body: schema.NamespaceEdit,
    namespace_edit_check: Annotated[bool | None, Depends(acl.check_namespace_edit)],
    namespace_admin_check: Annotated[bool | None, Depends(acl.check_namespace_admin)],
):
    acl.require(namespace_edit_check)

    if body.name != namespace:
        acl.require(namespace_admin_check)

        if storage.get_namespace_exists(session, body.name):
            raise error.namespace_already_exists()

    storage.edit_namespace(session, namespace, body)
    session.commit()


@app.delete(
    "/namespace/{namespace}",
    dependencies=[Depends(check_namespace_exists)],
)
def delete_namespace(
    session: SessionDep,
    namespace: str,
    namespace_owner_check: Annotated[bool | None, Depends(acl.check_namespace_owner)],
):
    acl.require(namespace_owner_check)

    storage.delete_namespace(session, namespace)
    session.commit()


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
