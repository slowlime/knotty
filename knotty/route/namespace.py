from typing import Annotated
from fastapi import Depends, status

from knotty import acl, model
from knotty.auth import AuthDep
from .. import app, error, schema, storage
from ..db import SessionDep


def check_namespace_exists(session: SessionDep, namespace: str) -> int:
    namespace_id = storage.get_namespace_id(session, namespace)

    if namespace_id is None:
        raise error.not_found("Namespace")

    return namespace_id


@app.post("/namespace", status_code=status.HTTP_201_CREATED)
def create_namespace(
    session: SessionDep,
    body: schema.NamespaceCreate,
    auth: AuthDep,
    namespace_create_check: Annotated[bool | None, Depends(acl.can_add_namespace)],
):
    acl.require(namespace_create_check)

    if storage.get_namespace_exists(session, body.name):
        raise error.already_exists("Namespace")

    storage.create_namespace(session, body, auth)
    session.commit()


@app.get("/namespace/{namespace}")
def get_namespace(session: SessionDep, namespace: str) -> schema.Namespace:
    ns = storage.get_namespace(session, namespace)

    if ns is None:
        raise error.not_found("Namespace")

    return ns


@app.post(
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
            raise error.already_exists("Namespace")

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


@app.post(
    "/namespace/{namespace}/user",
    status_code=status.HTTP_201_CREATED,
)
def create_namespace_user(
    session: SessionDep,
    auth: AuthDep,
    namespace: str,
    namespace_id: Annotated[int, Depends(check_namespace_exists)],
    body: schema.NamespaceUserCreate,
    namespace_admin_check: Annotated[bool | None, Depends(acl.check_namespace_admin)],
    user_namespace_permissions: acl.NamespacePermissions,
    is_admin: Annotated[bool, Depends(acl.is_admin)],
):
    acl.require(namespace_admin_check)

    if not storage.get_user_exists(session, body.username):
        raise error.not_found("User")

    if storage.get_namespace_user_exists(session, namespace_id, body.username):
        raise error.already_exists("User")

    role_permissions = storage.get_namespace_role_permissions(
        session, namespace, body.role
    )

    if role_permissions is None:
        raise error.not_found("Role")

    if not is_admin and not acl.has_namespace_permissions(
        user_namespace_permissions, role_permissions
    ):
        raise error.no_permission()

    storage.create_namespace_user(session, namespace_id, body, added_by=auth)
    session.commit()


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


@app.post("/namespace/{namespace}/user/{username}")
def edit_namespace_user(
    session: SessionDep,
    auth: AuthDep,
    namespace: str,
    username: str,
    body: schema.NamespaceUserEdit,
    namespace_admin_check: Annotated[bool | None, Depends(acl.check_namespace_admin)],
    is_admin: Annotated[bool, Depends(acl.is_admin)],
    namespace_id: Annotated[int, Depends(check_namespace_exists)],
    user_namespace_permissions: acl.NamespacePermissions,
):
    acl.require(namespace_admin_check)

    if not storage.get_namespace_user_exists(session, namespace_id, username):
        raise error.not_found("User")

    role_permissions = storage.get_namespace_role_permissions(
        session, namespace, body.role
    )

    if role_permissions is None:
        raise error.not_found("Role")

    if not is_admin and not acl.has_namespace_permissions(
        user_namespace_permissions, role_permissions
    ):
        raise error.no_permission()

    owners = storage.get_namespace_owners(session, namespace_id)

    if (
        username in owners
        and model.PermissionCode.namespace_owner not in role_permissions
        and len(owners) <= 1
    ):
        raise error.no_owner_remains()

    storage.edit_namespace_user(session, namespace_id, username, body, updated_by=auth)
    session.commit()


@app.delete("/namespace/{namespace}/user/{username}")
def delete_namespace_user(
    session: SessionDep,
    auth: AuthDep,
    namespace: str,
    username: str,
    namespace_admin_check: Annotated[bool | None, Depends(acl.check_namespace_admin)],
    user_namespace_permissions: acl.NamespacePermissions,
    is_admin: Annotated[bool, Depends(acl.is_admin)],
    namespace_id: Annotated[int, Depends(check_namespace_exists)],
):
    if username != auth.username:
        acl.require(namespace_admin_check)

    deleted_user_permissions = storage.get_namespace_user_permissions(
        session, namespace, username
    )

    if not is_admin and not acl.has_namespace_permissions(
        user_namespace_permissions, deleted_user_permissions
    ):
        raise error.no_permission()

    owners = storage.get_namespace_owners(session, namespace_id)

    if username in owners and len(owners) <= 1:
        raise error.no_owner_remains()

    storage.delete_namespace_user(session, namespace_id, username)
    session.commit()


@app.get("/namespace/{namespace}/role", dependencies=[Depends(check_namespace_exists)])
def get_namespace_roles(
    session: SessionDep,
    namespace: str,
) -> list[schema.NamespaceRole]:
    return storage.get_namespace_roles(session, namespace)


@app.post("/namespace/{namespace}/role")
def create_namespace_role(
    session: SessionDep,
    auth: AuthDep,
    namespace_id: Annotated[int, Depends(check_namespace_exists)],
    body: schema.NamespaceRoleCreate,
    namespace_admin_check: Annotated[bool | None, Depends(acl.check_namespace_admin)],
    user_namespace_permissions: acl.NamespacePermissions,
    is_admin: Annotated[bool, Depends(acl.is_admin)],
):
    acl.require(namespace_admin_check)

    if storage.get_namespace_role_exists(session, namespace_id, body.name):
        raise error.already_exists("Role")

    if not is_admin and not acl.has_namespace_permissions(
        user_namespace_permissions, body.permissions
    ):
        raise error.no_permission()

    storage.create_namespace_role(session, namespace_id, body, added_by=auth)
    session.commit()


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


@app.post("/namespace/{namespace}/role/{role}")
def edit_namespace_role(
    session: SessionDep,
    auth: AuthDep,
    namespace: str,
    role: str,
    body: schema.NamespaceRoleEdit,
    namespace_id: Annotated[int, Depends(check_namespace_exists)],
    namespace_admin_check: Annotated[bool | None, Depends(acl.check_namespace_admin)],
    user_namespace_permissions: acl.NamespacePermissions,
    is_admin: Annotated[bool, Depends(acl.is_admin)],
):
    acl.require(namespace_admin_check)

    if not storage.get_namespace_role_exists(session, namespace_id, role):
        raise error.not_found("Role")

    if role != body.name and storage.get_namespace_role_exists(
        session, namespace_id, body.name
    ):
        raise error.already_exists("Role")

    if not is_admin and not acl.has_namespace_permissions(
        user_namespace_permissions, body.permissions
    ):
        raise error.no_permission()

    role_permissions = storage.get_namespace_role_permissions(session, namespace, role)
    assert role_permissions is not None

    if not is_admin and not acl.has_namespace_permissions(
        user_namespace_permissions, role_permissions
    ):
        raise error.no_permission()

    if (
        model.PermissionCode.namespace_owner in role_permissions
        and model.PermissionCode.namespace_owner not in body.permissions
    ):
        owners = storage.get_namespace_owners(session, namespace_id)
        affected_users = storage.get_namespace_role_users(session, namespace_id, role)
        assert affected_users is not None

        if not (set(owners) - set(affected_users)):
            raise error.no_owner_remains()

    storage.edit_namespace_role(session, namespace_id, role, body, updated_by=auth)
    session.commit()


@app.delete("/namespace/{namespace}/role/{role}")
def delete_namespace_role(
    session: SessionDep,
    namespace: str,
    role: str,
    namespace_id: Annotated[int, Depends(check_namespace_exists)],
    namespace_admin_check: Annotated[bool | None, Depends(acl.check_namespace_admin)],
    user_namespace_permissions: acl.NamespacePermissions,
    is_admin: Annotated[bool, Depends(acl.is_admin)],
):
    acl.require(namespace_admin_check)

    if not storage.get_namespace_role_exists(session, namespace_id, role):
        raise error.not_found("Role")

    role_permissions = storage.get_namespace_role_permissions(session, namespace, role)
    assert role_permissions is not None

    if not is_admin and not acl.has_namespace_permissions(
        user_namespace_permissions,
        role_permissions,
    ):
        raise error.no_permission()

    if storage.get_namespace_role_empty(session, namespace_id, role):
        raise error.role_not_empty()

    storage.delete_namespace_role(session, namespace_id, role)
    session.commit()
