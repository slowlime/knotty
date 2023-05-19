from .. import app, error, schema, storage
from ..db import SessionDep


@app.get("/package")
def get_packages(session: SessionDep) -> list[schema.PackageBrief]:
    return storage.get_packages(session)


@app.get("/package/{package}")
def get_package(session: SessionDep, package: str) -> schema.Package:
    p = storage.get_package(session, package)

    if p is None:
        raise error.not_found()

    return p
