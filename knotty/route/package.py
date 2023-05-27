import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status
from knotty import acl, schema, storage, model
from knotty.auth import AuthDep
from knotty.db import SessionDep
from knotty.error import (
    AlreadyExistsException,
    HasDependentsException,
    HasReferringTagsException,
    NoPackageOwnerRemainsException,
    NoPermissionException,
    NotFoundException,
    UnauthorizedException,
    UnknownDependenciesException,
    UnknownOwnersException,
    exception_responses,
)


router = APIRouter()
logger = logging.getLogger(__name__)


def can_edit_owners(
    session: SessionDep,
    auth: AuthDep,
    current_package: schema.PackageBrief,
    is_admin: bool,
) -> bool:
    if auth.username in current_package.owners:
        return True

    if current_package.namespace is None:
        return False

    user_namespace_permissions = acl.get_namespace_user_permissions(
        session,
        auth,
        current_package.namespace,
    )

    if not is_admin and not acl.has_namespace_permission(
        set(user_namespace_permissions),
        model.PermissionCode.namespace_admin,
    ):
        return False

    return True


def get_package_id(session: SessionDep, package: str) -> int:
    package_id = storage.get_package_id(session, package)

    if package_id is None:
        raise NoPermissionException("Package")

    return package_id


@router.get("/package")
def get_packages(session: SessionDep) -> list[schema.PackageBrief]:
    return storage.get_packages(session)


@router.post(
    "/package",
    status_code=status.HTTP_201_CREATED,
    responses=exception_responses(
        UnauthorizedException,
        NoPermissionException,
        NotFoundException,
        AlreadyExistsException,
        UnknownOwnersException,
        UnknownDependenciesException,
    ),
)
def create_package(
    session: SessionDep,
    auth: AuthDep,
    body: schema.PackageCreate,
    can_create_package_check: Annotated[bool, Depends(acl.can_create_package)],
    is_admin: Annotated[bool, Depends(acl.is_admin)],
) -> schema.Message:
    acl.require(can_create_package_check)

    if body.namespace is not None:
        if not storage.get_namespace_exists(session, body.namespace):
            raise NotFoundException("Namespace")

        user_namespace_permissions = acl.get_namespace_user_permissions(
            session, auth, body.namespace
        )

        if not is_admin and not acl.has_namespace_permission(
            set(user_namespace_permissions),
            model.PermissionCode.package_create,
        ):
            raise NoPermissionException()

    if storage.get_package_exists(session, body.name):
        raise AlreadyExistsException("Package")

    if auth.username not in body.owners:
        body.owners.add(auth.username)

    unknown_owners = storage.get_unknown_users(session, body.owners)

    if unknown_owners:
        raise UnknownOwnersException(unknown_owners)

    unknown_deps = storage.get_unknown_packages(
        session,
        set(dep.package for version in body.versions for dep in version.dependencies),
    )

    if unknown_deps:
        raise UnknownDependenciesException(unknown_deps)

    storage.create_package(session, body, created_by=auth)
    session.commit()

    return schema.Message(message="Package created")


@router.get("/package/{package}", responses=exception_responses(NotFoundException))
def get_package(session: SessionDep, package: str) -> schema.Package:
    p = storage.get_package(session, package)

    if p is None:
        raise NotFoundException("Package")

    return p


@router.post(
    "/package/{package}",
    responses=exception_responses(
        UnauthorizedException,
        NotFoundException,
        NoPermissionException,
        AlreadyExistsException,
        UnknownOwnersException,
        NoPackageOwnerRemainsException,
    ),
)
def edit_package(
    session: SessionDep,
    auth: AuthDep,
    package: str,
    body: schema.PackageEdit,
    can_edit_check: Annotated[bool, Depends(acl.can_edit_package)],
    is_admin: Annotated[bool, Depends(acl.is_admin)],
) -> schema.Message:
    current_package = storage.get_package_brief(session, package)

    if current_package is None:
        raise NotFoundException("Package")

    acl.require(can_edit_check)

    if body.namespace != current_package.namespace:
        # check if we can remove the package from the current namespace
        if current_package.namespace is not None:
            user_namespace_permissions = acl.get_namespace_user_permissions(
                session, auth, current_package.namespace
            )

            if not is_admin and not acl.has_namespace_permission(
                set(user_namespace_permissions),
                model.PermissionCode.namespace_admin,
            ):
                raise NoPermissionException()

        # check if we can add the package to the requested namespace
        if body.namespace is not None:
            user_namespace_permissions = acl.get_namespace_user_permissions(
                session, auth, body.namespace
            )

            if not is_admin and not acl.has_namespace_permission(
                set(user_namespace_permissions),
                model.PermissionCode.package_create,
            ):
                raise NoPermissionException()

    if current_package.name != body.name and storage.get_package_exists(
        session, body.name
    ):
        raise AlreadyExistsException("Package")

    if current_package.owners != body.owners:
        if not can_edit_owners(session, auth, current_package, is_admin):
            raise NoPermissionException()

    unknown_owners = storage.get_unknown_users(session, body.owners)

    if unknown_owners:
        raise UnknownOwnersException(unknown_owners)

    if not body.owners:
        raise NoPackageOwnerRemainsException()

    storage.edit_package(session, package, body, updated_by=auth)
    session.commit()

    return schema.Message(message="Package updated")


@router.delete(
    "/package/{package}",
    dependencies=[Depends(get_package_id)],
    responses=exception_responses(
        NotFoundException,
        UnauthorizedException,
        NoPermissionException,
        HasDependentsException,
    ),
)
def delete_package(
    session: SessionDep,
    package: str,
    can_delete_package: Annotated[bool, Depends(acl.can_delete_package)],
) -> schema.Message:
    acl.require(can_delete_package)

    if storage.get_package_has_dependents(session, package):
        raise HasDependentsException()

    storage.delete_package(session, package)
    session.commit()

    return schema.Message(message="Package deleted")


@router.get(
    "/package/{package}/version", responses=exception_responses(NotFoundException)
)
def get_package_versions(
    session: SessionDep,
    package_id: Annotated[int, Depends(get_package_id)],
) -> list[schema.PackageVersion]:
    return storage.get_package_versions(session, package_id)


@router.post(
    "/package/{package}/version",
    status_code=status.HTTP_201_CREATED,
    responses=exception_responses(
        NotFoundException,
        UnauthorizedException,
        NoPermissionException,
        AlreadyExistsException,
        UnknownDependenciesException,
    ),
)
def create_package_version(
    session: SessionDep,
    auth: AuthDep,
    package_id: Annotated[int, Depends(get_package_id)],
    body: schema.PackageVersionCreate,
    can_edit_check: Annotated[bool, Depends(acl.can_edit_package)],
) -> schema.Message:
    acl.require(can_edit_check)

    if storage.get_package_version_exists(session, package_id, str(body.version)):
        raise AlreadyExistsException("Version")

    unknown_deps = storage.get_unknown_packages(
        session,
        set(dep.package for dep in body.dependencies),
    )

    if unknown_deps:
        raise UnknownDependenciesException(unknown_deps)

    storage.create_package_version(session, package_id, body, created_by=auth)
    session.commit()

    return schema.Message(message="Package version added")


@router.get(
    "/package/{package}/version/{version}",
    responses=exception_responses(NotFoundException),
)
def get_package_version(
    session: SessionDep,
    package_id: Annotated[int, Depends(get_package_id)],
    version: str,
) -> schema.PackageVersion:
    result = storage.get_package_version(session, package_id, version)

    if result is None:
        raise NotFoundException("Version")

    return result


@router.post(
    "/package/{package}/version/{version}",
    responses=exception_responses(
        NotFoundException,
        UnauthorizedException,
        NoPermissionException,
        AlreadyExistsException,
        UnknownDependenciesException,
    ),
)
def edit_package_version(
    session: SessionDep,
    auth: AuthDep,
    package_id: Annotated[int, Depends(get_package_id)],
    version: str,
    body: schema.PackageVersionEdit,
    can_edit_check: Annotated[bool, Depends(acl.can_edit_package)],
) -> schema.Message:
    current_version = storage.get_package_version(session, package_id, version)

    if current_version is None:
        raise NotFoundException("Version")

    acl.require(can_edit_check)

    if current_version.version != body.version:
        if storage.get_package_version_exists(session, package_id, str(body.version)):
            raise AlreadyExistsException("Version")

    unknown_deps = storage.get_unknown_packages(
        session,
        set(dep.package for dep in body.dependencies),
    )

    if unknown_deps:
        raise UnknownDependenciesException(unknown_deps)

    storage.edit_package_version(session, package_id, version, body, updated_by=auth)
    session.commit()

    return schema.Message(message="Package version updated")


@router.delete(
    "/package/{package}/version/{version}",
    responses=exception_responses(
        NotFoundException,
        UnauthorizedException,
        NoPermissionException,
        HasReferringTagsException,
    ),
)
def delete_package_version(
    session: SessionDep,
    package_id: Annotated[int, Depends(get_package_id)],
    version: str,
    can_edit_check: Annotated[bool, Depends(acl.can_edit_package)],
) -> schema.Message:
    if not storage.get_package_version_exists(session, package_id, version):
        raise NotFoundException("Version")

    acl.require(can_edit_check)

    if storage.get_package_version_is_tagged(session, package_id, version):
        raise HasReferringTagsException()

    storage.delete_package_version(session, package_id, version)
    session.commit()

    return schema.Message(message="Package version deleted")


@router.get("/package/{package}/tag", responses=exception_responses(NotFoundException))
def get_package_tags(
    session: SessionDep,
    package_id: Annotated[int, Depends(get_package_id)],
) -> list[schema.PackageTag]:
    return storage.get_package_tags(session, package_id)


@router.post(
    "/package/{package}/tag",
    status_code=status.HTTP_201_CREATED,
    responses=exception_responses(
        NotFoundException,
        UnauthorizedException,
        NoPermissionException,
        AlreadyExistsException,
    ),
)
def create_package_tag(
    session: SessionDep,
    package_id: Annotated[int, Depends(get_package_id)],
    body: schema.PackageTag,
    can_edit_check: Annotated[bool, Depends(acl.can_edit_package)],
) -> schema.Message:
    acl.require(can_edit_check)

    if storage.get_package_tag_exists(session, package_id, body.name):
        raise AlreadyExistsException("Tag")

    if not storage.get_package_version_exists(session, package_id, body.version):
        raise NotFoundException("Version")

    storage.create_package_tag(session, package_id, body)
    session.commit()

    return schema.Message(message="Package tag created")


@router.get(
    "/package/{package}/tag/{tag}", responses=exception_responses(NotFoundException)
)
def get_package_tag(
    session: SessionDep,
    package_id: Annotated[int, Depends(get_package_id)],
    tag: str,
) -> schema.PackageTag:
    result = storage.get_package_tag(session, package_id, tag)

    if result is None:
        raise NotFoundException("Tag")

    return result


@router.post(
    "/package/{package}/tag/{tag}",
    responses=exception_responses(
        NotFoundException,
        UnauthorizedException,
        NoPermissionException,
        AlreadyExistsException,
    ),
)
def edit_package_tag(
    session: SessionDep,
    package_id: Annotated[int, Depends(get_package_id)],
    tag: str,
    body: schema.PackageTag,
    can_edit_check: Annotated[bool, Depends(acl.can_edit_package)],
) -> schema.Message:
    current_tag = storage.get_package_tag(session, package_id, tag)

    if current_tag is None:
        raise NotFoundException("Tag")

    acl.require(can_edit_check)

    if current_tag.name != body.name:
        if storage.get_package_tag_exists(session, package_id, body.name):
            raise AlreadyExistsException("Tag")

    if not storage.get_package_version_exists(session, package_id, body.version):
        raise NotFoundException("Version")

    storage.edit_package_tag(session, package_id, tag, body)
    session.commit()

    return schema.Message(message="Package tag updated")


@router.delete(
    "/package/{package}/tag/{tag}",
    responses=exception_responses(
        UnauthorizedException, NoPermissionException, NotFoundException
    ),
)
def delete_package_tag(
    session: SessionDep,
    package_id: Annotated[int, Depends(get_package_id)],
    tag: str,
    can_edit_check: Annotated[bool, Depends(acl.can_edit_package)],
) -> schema.Message:
    if not storage.get_package_tag_exists(session, package_id, tag):
        raise NotFoundException("Tag")

    acl.require(can_edit_check)

    storage.delete_package_tag(session, package_id, tag)
    session.commit()

    return schema.Message(message="Package tag deleted")
