from sqlalchemy import select
from sqlalchemy.orm import Session

from . import model, schema


def get_user(session: Session, username: str) -> model.User | None:
    query = select(model.User).where(model.User.username == username)

    return session.scalars(query).one_or_none()


def get_user_by_email(session: Session, email: str) -> model.User | None:
    query = select(model.User).where(model.User.email == email)

    return session.scalars(query).one_or_none()


def get_user_namespaces(session: Session, username: str) -> list[str]:
    query = (
        select(model.Namespace.namespace)
        .join(model.Namespace.users)
        .join(model.NamespaceUser.user)
        .where(model.User.username == username)
    )

    return list(session.scalars(query).all())


def create_user(session: Session, data: schema.UserCreate):
    user = model.User(**data.dict())
    session.add(user)


def get_namespace(session: Session, name: str) -> model.Namespace | None:
    query = select(model.Namespace).where(model.Namespace.namespace == name)

    return session.scalars(query).one_or_none()


def get_namespace_packages(session: Session, name: str) -> list[model.Package] | None:
    namespace_exists = select(
        select(model.Namespace).where(model.Namespace.namespace == name).exists()
    )

    if not session.scalar(namespace_exists):
        return None

    query = (
        select(model.Package)
        .join(model.Package.namespace)
        .where(model.Namespace.namespace == name)
    )

    return list(session.scalars(query).all())


def get_namespace_user(
    session: Session, namespace: str, username: str
) -> model.NamespaceUser | None:
    query = (
        select(model.NamespaceUser)
        .join(model.NamespaceUser.namespace)
        .where(model.Namespace.namespace == namespace)
        .join(model.NamespaceUser.user)
        .where(model.User.username == username)
    )

    return session.scalars(query).one_or_none()


def get_namespace_role(
    session: Session,
    namespace: str,
    role: str,
) -> model.NamespaceRole | None:
    query = (
        select(model.NamespaceRole)
        .where(model.NamespaceRole.name == role)
        .join(model.NamespaceRole.namespace)
        .where(model.Namespace.namespace == namespace)
    )

    return session.scalars(query).one_or_none()


def get_packages(session: Session) -> list[model.Package]:
    query = select(model.Package)

    return list(session.scalars(query).all())


def get_package(session: Session, name: str) -> model.Package | None:
    query = select(model.Package).where(model.Package.name == name)

    return session.scalars(query).one_or_none()


def get_permissions(session: Session) -> list[model.Permission]:
    query = select(model.Permission)

    return list(session.scalars(query).all())
