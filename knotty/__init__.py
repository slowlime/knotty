import logging.config

from fastapi import FastAPI

from knotty.config import Config, get_config
import knotty.route.namespace
import knotty.route.package
import knotty.route.permission
import knotty.route.user


def make_app(config: Config) -> FastAPI:
    logging.config.dictConfig(config.logging)

    app = FastAPI()
    app.include_router(knotty.route.namespace.router)
    app.include_router(knotty.route.package.router)
    app.include_router(knotty.route.permission.router)
    app.include_router(knotty.route.user.router)

    app.get("/")(lambda: {"version": "knotty v0.0.1"})

    return app


def make_default_app():
    return make_app(get_config())
