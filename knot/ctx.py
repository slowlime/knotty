from dataclasses import dataclass
from pathlib import Path

from typing import Optional
from knotty_client import Client, AuthenticatedClient
from rich.console import Console
import typer

from knot.app import app, get_app_dir
from knot.auth import get_session, Session
from knot.config import Config

CLIENT_SETTINGS = {
    "timeout": 15,
    "verify_ssl": False,
    "follow_redirects": False,
    "raise_on_unexpected_status": True,
}


@dataclass
class BaseContextObj:
    console: Console

    def to_authenticated(self) -> "AuthenticatedContextObj":
        raise NotImplementedError()


@dataclass
class AuthenticatedContextObj(BaseContextObj):
    session: Session
    client: AuthenticatedClient

    def to_authenticated(self) -> "AuthenticatedContextObj":
        return self


@dataclass
class UnauthenticatedContextObj(BaseContextObj):
    session: None
    client: Client

    def to_authenticated(self) -> AuthenticatedContextObj:
        # breaking the circular imports
        from knot.error import print_error

        print_error(
            "This operation requires authorization. Use `knot login` to log in.",
            ctx=self,
        )
        raise typer.Abort()


ContextObj = AuthenticatedContextObj | UnauthenticatedContextObj


@app.callback()
def get_client(
    ctx: typer.Context,
    config_path: Optional[Path] = None,
    url: Optional[str] = None,
):
    config_user_provided = config_path is not None

    if config_path is None:
        config_path = get_app_dir() / "config.toml"

    try:
        config = Config.from_toml(config_path)
    except FileNotFoundError:
        if config_user_provided:
            raise

        config = Config()

    if url is None:
        url = config.url

    session = get_session()

    if session is not None:
        client = AuthenticatedClient(url, token=session.token, **CLIENT_SETTINGS)
        maker = lambda base: AuthenticatedContextObj(
            session=session, client=client, **base.__dict__
        )
    else:
        client = Client(url, **CLIENT_SETTINGS)
        maker = lambda base: UnauthenticatedContextObj(
            session=session, client=client, **base.__dict__
        )

    base = BaseContextObj(console=Console())
    ctx.obj = maker(base)
