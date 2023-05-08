from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from . import config

sql_engine = create_engine(config.db_url, connect_args=config.connect_args)
DbSession = sessionmaker(autocommit=False, autoflush=False, bind=sql_engine)


def get_db() -> Generator[Session, None, None]:
    with DbSession() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
