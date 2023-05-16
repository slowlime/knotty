from .. import app, model, schema, storage
from ..db import SessionDep


@app.get("/permission", response_model=schema.Permission)
def get_permissions(session: SessionDep) -> list[model.Permission]:
    return storage.get_permissions(session)
