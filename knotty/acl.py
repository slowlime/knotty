from typing import Annotated, Literal
from fastapi import Depends
from sqlalchemy.orm import Session

from knotty import model, storage
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


def get_namespace_permissions(
    session: Session, auth: AuthDep, namespace: str
) -> list[model.PermissionCode]:
    return storage.get_namespace_permissions(session, namespace, auth.username)


NamespacePermissions = Annotated[
    list[model.PermissionCode], Depends(get_namespace_permissions)
]


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


def require(check: bool | None, allow_by_default: bool = False):
    if check is None:
        check = allow_by_default

    if not check:
        raise no_permission()
