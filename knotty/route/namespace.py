from typing import Annotated
from fastapi import APIRouter, Depends, status

from knotty import acl, model, schema, storage
from knotty.auth import AuthDep
from knotty.config import ConfigDep
from knotty.db import SessionDep
from knotty.error import (
    AlreadyExistsException,
    NoNamespaceOwnerRemainsException,
    NoPermissionException,
    NotFoundException,
    RoleNotEmptyException,
    exception_responses,
)


router = APIRouter()


def check_namespace_exists(session: SessionDep, namespace: str) -> int:
    namespace_id = storage.get_namespace_id(session, namespace)

    if namespace_id is None:
        raise NotFoundException("Namespace")

    return namespace_id


@router.post(
    "/namespace",
    status_code=status.HTTP_201_CREATED,
    responses=exception_responses(AlreadyExistsException),
)
def create_namespace(
    config: ConfigDep,
    session: SessionDep,
    body: schema.NamespaceCreate,
    auth: AuthDep,
    namespace_create_check: Annotated[bool | None, Depends(acl.can_add_namespace)],
) -> schema.Message:
    acl.require(namespace_create_check)

    if storage.get_namespace_exists(session, body.name):
        raise AlreadyExistsException("Namespace")

    storage.create_namespace(session, body, auth, config)
    session.commit()

    return schema.Message(message="Namespace created")


@router.get("/namespace/{namespace}", responses=exception_responses(NotFoundException))
def get_namespace(session: SessionDep, namespace: str) -> schema.Namespace:
    ns = storage.get_namespace(session, namespace)

    if ns is None:
        raise NotFoundException("Namespace")

    return ns


@router.post(
    "/namespace/{namespace}",
    dependencies=[Depends(check_namespace_exists)],
    responses=exception_responses(
        NotFoundException, NoPermissionException, AlreadyExistsException
    ),
)
def edit_namespace(
    session: SessionDep,
    namespace: str,
    body: schema.NamespaceEdit,
    namespace_edit_check: Annotated[bool | None, Depends(acl.check_namespace_edit)],
    namespace_admin_check: Annotated[bool | None, Depends(acl.check_namespace_admin)],
) -> schema.Message:
    acl.require(namespace_edit_check)

    if body.name != namespace:
        acl.require(namespace_admin_check)

        if storage.get_namespace_exists(session, body.name):
            raise AlreadyExistsException("Namespace")

    storage.edit_namespace(session, namespace, body)
    session.commit()

    return schema.Message(message="Namespace updated")


@router.delete(
    "/namespace/{namespace}",
    dependencies=[Depends(check_namespace_exists)],
    responses=exception_responses(NotFoundException, NoPermissionException),
)
def delete_namespace(
    session: SessionDep,
    namespace: str,
    namespace_owner_check: Annotated[bool | None, Depends(acl.check_namespace_owner)],
) -> schema.Message:
    acl.require(namespace_owner_check)

    storage.delete_namespace(session, namespace)
    session.commit()

    return schema.Message(message="Namespace deleted")


@router.get(
    "/namespace/{namespace}/package",
    dependencies=[Depends(check_namespace_exists)],
    responses=exception_responses(NotFoundException),
)
def get_namespace_packages(
    session: SessionDep, namespace: str
) -> list[schema.PackageBasic]:
    return storage.get_namespace_packages(session, namespace)


@router.get(
    "/namespace/{namespace}/user",
    dependencies=[Depends(check_namespace_exists)],
    responses=exception_responses(NotFoundException),
)
def get_namespace_users(
    session: SessionDep,
    namespace: str,
) -> list[schema.NamespaceUser]:
    return storage.get_namespace_users(session, namespace)


@router.post(
    "/namespace/{namespace}/user",
    status_code=status.HTTP_201_CREATED,
    responses=exception_responses(
        NotFoundException, NoPermissionException, AlreadyExistsException
    ),
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
) -> schema.Message:
    acl.require(namespace_admin_check)

    if not storage.get_user_exists(session, body.username):
        raise NotFoundException("User")

    if storage.get_namespace_user_exists(session, namespace_id, body.username):
        raise AlreadyExistsException("User")

    role_permissions = storage.get_namespace_role_permissions(
        session, namespace, body.role
    )

    if role_permissions is None:
        raise NotFoundException("Role")

    if not is_admin and not acl.has_namespace_permissions(
        user_namespace_permissions, role_permissions
    ):
        raise NoPermissionException()

    storage.create_namespace_user(session, namespace_id, body, added_by=auth)
    session.commit()

    return schema.Message(message="User added to namespace")


@router.get(
    "/namespace/{namespace}/user/{username}",
    dependencies=[Depends(check_namespace_exists)],
    responses=exception_responses(NotFoundException),
)
def get_namespace_user(
    session: SessionDep,
    namespace: str,
    username: str,
) -> schema.NamespaceUser:
    user = storage.get_namespace_user(session, namespace, username)

    if user is None:
        raise NotFoundException("User")

    return user


@router.post(
    "/namespace/{namespace}/user/{username}",
    responses=exception_responses(
        NotFoundException, NoPermissionException, NoNamespaceOwnerRemainsException
    ),
)
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
) -> schema.Message:
    acl.require(namespace_admin_check)

    if not storage.get_namespace_user_exists(session, namespace_id, username):
        raise NotFoundException("User")

    role_permissions = storage.get_namespace_role_permissions(
        session, namespace, body.role
    )

    if role_permissions is None:
        raise NotFoundException("Role")

    if not is_admin and not acl.has_namespace_permissions(
        user_namespace_permissions, role_permissions
    ):
        raise NoPermissionException()

    owners = storage.get_namespace_owners(session, namespace_id)

    if (
        username in owners
        and model.PermissionCode.namespace_owner not in role_permissions
        and len(owners) <= 1
    ):
        raise NoNamespaceOwnerRemainsException()

    storage.edit_namespace_user(session, namespace_id, username, body, updated_by=auth)
    session.commit()

    return schema.Message(message="Namespace user updated")


@router.delete(
    "/namespace/{namespace}/user/{username}",
    responses=exception_responses(
        NotFoundException, NoPermissionException, NoNamespaceOwnerRemainsException
    ),
)
def delete_namespace_user(
    session: SessionDep,
    auth: AuthDep,
    namespace: str,
    username: str,
    namespace_admin_check: Annotated[bool | None, Depends(acl.check_namespace_admin)],
    user_namespace_permissions: acl.NamespacePermissions,
    is_admin: Annotated[bool, Depends(acl.is_admin)],
    namespace_id: Annotated[int, Depends(check_namespace_exists)],
) -> schema.Message:
    if username != auth.username:
        acl.require(namespace_admin_check)

    deleted_user_permissions = storage.get_namespace_user_permissions(
        session, namespace, username
    )

    if not is_admin and not acl.has_namespace_permissions(
        user_namespace_permissions, deleted_user_permissions
    ):
        raise NoPermissionException()

    owners = storage.get_namespace_owners(session, namespace_id)

    if username in owners and len(owners) <= 1:
        raise NoNamespaceOwnerRemainsException()

    storage.delete_namespace_user(session, namespace_id, username)
    session.commit()

    return schema.Message(message="User removed from namespace")


@router.get(
    "/namespace/{namespace}/role",
    dependencies=[Depends(check_namespace_exists)],
    responses=exception_responses(NotFoundException),
)
def get_namespace_roles(
    session: SessionDep,
    namespace: str,
) -> list[schema.NamespaceRole]:
    return storage.get_namespace_roles(session, namespace)


@router.post(
    "/namespace/{namespace}/role",
    status_code=status.HTTP_201_CREATED,
    responses=exception_responses(
        NotFoundException, NoPermissionException, AlreadyExistsException
    ),
)
def create_namespace_role(
    session: SessionDep,
    auth: AuthDep,
    namespace_id: Annotated[int, Depends(check_namespace_exists)],
    body: schema.NamespaceRoleCreate,
    namespace_admin_check: Annotated[bool | None, Depends(acl.check_namespace_admin)],
    user_namespace_permissions: acl.NamespacePermissions,
    is_admin: Annotated[bool, Depends(acl.is_admin)],
) -> schema.Message:
    acl.require(namespace_admin_check)

    if storage.get_namespace_role_exists(session, namespace_id, body.name):
        raise AlreadyExistsException("Role")

    if not is_admin and not acl.has_namespace_permissions(
        user_namespace_permissions, body.permissions
    ):
        raise NoPermissionException()

    storage.create_namespace_role(session, namespace_id, body, created_by=auth)
    session.commit()

    return schema.Message(message="Namespace role added")


@router.get(
    "/namespace/{namespace}/role/{role}",
    dependencies=[Depends(check_namespace_exists)],
    responses=exception_responses(NotFoundException),
)
def get_namespace_role(
    session: SessionDep,
    namespace: str,
    role: str,
) -> schema.NamespaceRole:
    result = storage.get_namespace_role(session, namespace, role)

    if result is None:
        raise NotFoundException("Role")

    return result


@router.post(
    "/namespace/{namespace}/role/{role}",
    responses=exception_responses(
        NotFoundException,
        NoPermissionException,
        AlreadyExistsException,
        NoNamespaceOwnerRemainsException,
    ),
)
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
) -> schema.Message:
    acl.require(namespace_admin_check)

    if not storage.get_namespace_role_exists(session, namespace_id, role):
        raise NotFoundException("Role")

    if role != body.name and storage.get_namespace_role_exists(
        session, namespace_id, body.name
    ):
        raise AlreadyExistsException("Role")

    if not is_admin and not acl.has_namespace_permissions(
        user_namespace_permissions, body.permissions
    ):
        raise NoPermissionException()

    role_permissions = storage.get_namespace_role_permissions(session, namespace, role)
    assert role_permissions is not None

    if not is_admin and not acl.has_namespace_permissions(
        user_namespace_permissions, role_permissions
    ):
        raise NoPermissionException()

    if (
        model.PermissionCode.namespace_owner in role_permissions
        and model.PermissionCode.namespace_owner not in body.permissions
    ):
        owners = storage.get_namespace_owners(session, namespace_id)
        affected_users = storage.get_namespace_role_users(session, namespace_id, role)
        assert affected_users is not None

        if not (set(owners) - set(affected_users)):
            raise NoNamespaceOwnerRemainsException()

    storage.edit_namespace_role(session, namespace_id, role, body, updated_by=auth)
    session.commit()

    return schema.Message(message="Namespace role updated")


@router.delete(
    "/namespace/{namespace}/role/{role}",
    responses=exception_responses(
        NotFoundException, NoPermissionException, RoleNotEmptyException
    ),
)
def delete_namespace_role(
    session: SessionDep,
    namespace: str,
    role: str,
    namespace_id: Annotated[int, Depends(check_namespace_exists)],
    namespace_admin_check: Annotated[bool | None, Depends(acl.check_namespace_admin)],
    user_namespace_permissions: acl.NamespacePermissions,
    is_admin: Annotated[bool, Depends(acl.is_admin)],
) -> schema.Message:
    acl.require(namespace_admin_check)

    if not storage.get_namespace_role_exists(session, namespace_id, role):
        raise NotFoundException("Role")

    role_permissions = storage.get_namespace_role_permissions(session, namespace, role)
    assert role_permissions is not None

    if not is_admin and not acl.has_namespace_permissions(
        user_namespace_permissions,
        role_permissions,
    ):
        raise NoPermissionException()

    if storage.get_namespace_role_empty(session, namespace_id, role):
        raise RoleNotEmptyException()

    storage.delete_namespace_role(session, namespace_id, role)
    session.commit()

    return schema.Message(message="Namespace role deleted")
