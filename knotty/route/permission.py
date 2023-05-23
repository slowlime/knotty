from fastapi import APIRouter
from .. import model, schema, storage
from ..db import SessionDep


router = APIRouter()


@router.get("/permission", response_model=list[schema.Permission])
def get_permissions(session: SessionDep) -> list[model.Permission]:
    return storage.get_permissions(session)
