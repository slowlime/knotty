import logging.config

from fastapi import APIRouter, FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from knotty import schema
from knotty.config import Config, get_config
from knotty.error import KnottyException
import knotty.route.namespace
import knotty.route.package
import knotty.route.permission
import knotty.route.user


TITLE = "knotty"
VERSION = "0.0.1"

router = APIRouter()


@router.get("/", response_model=schema.KnottyInfo)
def get_version() -> dict[str, str]:
    return {
        "version": VERSION,
    }


def make_app(config: Config) -> FastAPI:
    logging.config.dictConfig(config.logging)

    app = FastAPI(title=TITLE, version=VERSION)
    app.include_router(router)
    app.include_router(knotty.route.namespace.router)
    app.include_router(knotty.route.package.router)
    app.include_router(knotty.route.permission.router)
    app.include_router(knotty.route.user.router)

    for route in app.routes:
        if isinstance(route, APIRoute):
            route.operation_id = route.name

    @app.exception_handler(KnottyException)
    def knotty_exception_handler(request, exc: KnottyException):
        return JSONResponse(
            jsonable_encoder(exc.data), status_code=exc.status_code, headers=exc.headers
        )

    return app


def make_default_app():
    return make_app(get_config())
