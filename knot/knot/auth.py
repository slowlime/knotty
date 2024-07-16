from pathlib import Path
import json

from pydantic import BaseModel, ValidationError
from pydantic.json import pydantic_encoder
from knot.app import get_app_dir


class Session(BaseModel):
    username: str
    token: str


def get_session_file_path() -> Path:
    return Path(get_app_dir()) / "session.json"


def get_session() -> Session | None:
    session_file_path = get_session_file_path()

    try:
        return Session.parse_file(session_file_path, content_type="application/json")
    except OSError:
        return None
    except ValidationError:
        return None
    except json.JSONDecodeError:
        return None


def save_session(session: Session):
    session_file_path = get_session_file_path()

    with session_file_path.open("w") as f:
        json.dump(session, f, default=pydantic_encoder)


def remove_session():
    session_file_path = get_session_file_path()
    session_file_path.unlink(True)
