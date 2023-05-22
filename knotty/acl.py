from typing import Annotated, Literal
from fastapi import Depends
from sqlalchemy.orm import Session

from knotty import model, storage
from knotty.db import SessionDep
from knotty.error import no_permission
from knotty.auth import AuthDep


def is_admin(auth: AuthDep) -> bool:
    return auth.role == model.UserRole.admin


def check_user_role(
    auth: AuthDep, is_admin: Annotated[bool, Depends(is_admin)]
) -> bool | None:
    if is_admin:
        return True

    if auth.role == model.UserRole.banned:
        return False


def can_view_user(
    auth: AuthDep,
    user_role_check: Annotated[bool | None, Depends(check_user_role)],
    username: str,
) -> bool:
    if auth.username == username:
        return True

    if user_role_check:
        return True

    return False


def can_edit_user(
    is_admin: Annotated[bool, Depends(is_admin)],
) -> bool:
    return is_admin


def get_namespace_user_permissions(
    session: Session, auth: AuthDep, namespace: str
) -> list[model.PermissionCode]:
    return storage.get_namespace_user_permissions(session, namespace, auth.username)


NamespacePermissions = Annotated[
    list[model.PermissionCode], Depends(get_namespace_user_permissions)
]


def has_namespace_permission(
    user_permissions: set[model.PermissionCode],
    permission: model.PermissionCode,
) -> bool:
    Code = model.PermissionCode

    match permission:
        case Code.namespace_owner:
            return Code.namespace_owner in user_permissions

        case Code.namespace_admin:
            return (
                has_namespace_permission(user_permissions, Code.namespace_owner)
                or Code.namespace_admin in user_permissions
            )

        case _:
            return (
                has_namespace_permission(user_permissions, Code.namespace_admin)
                or permission in user_permissions
            )


def has_namespace_permissions(
    user_permissions: list[model.PermissionCode],
    needed_permissions: list[model.PermissionCode],
) -> bool:
    user_perms = set(user_permissions)

    return all(
        has_namespace_permission(user_perms, permission)
        for permission in needed_permissions
    )


def can_add_namespace(
    user_role_check: Annotated[bool | None, Depends(check_user_role)],
) -> bool:
    return bool(user_role_check)


def check_namespace_owner(
    user_role_check: Annotated[bool | None, Depends(check_user_role)],
    namespace_permissions: NamespacePermissions,
) -> bool | None:
    if user_role_check:
        return True

    if model.PermissionCode.namespace_owner in namespace_permissions:
        return True


def check_namespace_admin(
    namespace_owner_check: Annotated[bool | None, Depends(check_namespace_owner)],
    namespace_permissions: NamespacePermissions,
) -> bool | None:
    if namespace_owner_check:
        return True

    if model.PermissionCode.namespace_admin in namespace_permissions:
        return True


def check_namespace_edit(
    namespace_admin_check: Annotated[bool | None, Depends(check_namespace_admin)],
    namespace_permissions: NamespacePermissions,
) -> bool | None:
    if namespace_admin_check:
        return True

    if model.PermissionCode.namespace_edit in namespace_permissions:
        return True


def can_create_package(
    user_role_check: Annotated[bool | None, Depends(check_user_role)],
) -> bool:
    return bool(user_role_check)


def is_package_owner(
    session: SessionDep,
    auth: AuthDep,
    package: str,
) -> bool:
    return storage.get_package_owner_exists(session, package, auth.username)


def can_edit_package(
    session: SessionDep,
    auth: AuthDep,
    user_role_check: Annotated[bool | None, Depends(check_user_role)],
    is_owner: Annotated[bool, Depends(is_package_owner)],
    package: str,
) -> bool:
    if user_role_check is not None:
        return user_role_check

    if is_owner:
        return True

    namespace = storage.get_package_namespace(session, package)

    if namespace is None:
        return False

    user_namespace_permissions = get_namespace_user_permissions(
        session, auth, namespace
    )

    return has_namespace_permission(
        set(user_namespace_permissions), model.PermissionCode.package_edit
    )


def can_delete_package(
    session: SessionDep,
    auth: AuthDep,
    user_role_check: Annotated[bool | None, Depends(check_user_role)],
    is_owner: Annotated[bool, Depends(is_package_owner)],
    package: str,
) -> bool:
    if user_role_check is not None:
        return user_role_check

    if is_owner:
        return True

    namespace = storage.get_package_namespace(session, package)

    if namespace is None:
        return False

    user_namespace_permissions = get_namespace_user_permissions(
        session, auth, namespace
    )

    return has_namespace_permission(
        set(user_namespace_permissions), model.PermissionCode.namespace_admin
    )


def require(check: bool | None, allow_by_default: bool = False):
    if check is None:
        check = allow_by_default

    if not check:
        raise no_permission()
