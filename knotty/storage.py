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
