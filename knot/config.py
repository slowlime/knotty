from pathlib import Path

import toml
from pydantic import BaseModel, AnyHttpUrl


class Config(BaseModel):
    url: AnyHttpUrl = "http://localhost:8000"  # type: ignore

    @staticmethod
    def from_toml(path: Path) -> "Config":
        parsed = toml.load(path)

        return Config(**parsed)
