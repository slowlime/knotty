from functools import cache
import logging
from typing import Annotated

from fastapi import Depends
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker
from knotty import storage

from knotty.config import ConfigDep


logger = logging.getLogger(__name__)


@cache
def make_db(*, config: ConfigDep) -> sessionmaker[Session]:
    sql_engine = create_engine(
        config.db_url,
        connect_args=config.connect_args,
        poolclass=StaticPool if config.use_static_pool else None,
    )
    DbSession = sessionmaker(autocommit=False, autoflush=False, bind=sql_engine)

    return DbSession


@cache
def init_db(
    *, DbSession: Annotated[sessionmaker[Session], Depends(make_db)]
) -> sessionmaker[Session]:
    with DbSession() as session:
        storage.insert_permissions(session)
        session.commit()

    return DbSession


def get_db(DbSession: Annotated[sessionmaker[Session], Depends(init_db)]):
    with DbSession() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
