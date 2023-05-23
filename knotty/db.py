from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .config import config

sql_engine = create_engine(config.db_url, connect_args=config.connect_args, echo=True)
DbSession = sessionmaker(autocommit=False, autoflush=False, bind=sql_engine)


def get_db():
    with DbSession() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
