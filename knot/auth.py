from pathlib import Path
import typer
from pydantic import BaseModel, ValidationError

from knot.app import APP_NAME


class Session(BaseModel):
    username: str
    token: str


def get_session() -> Session | None:
    session_file_path = Path(typer.get_app_dir(APP_NAME)) / "session.json"

    try:
        return Session.parse_file(session_file_path, content_type="application/json")
    except OSError or ValidationError:
        return None
