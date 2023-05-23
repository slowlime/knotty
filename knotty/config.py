from datetime import timedelta
import os

from pathlib import Path

import toml

from typing import Any
from pydantic import BaseModel, SecretStr


CONFIG_PATH_ENVIRON = "KNOTTY_CONFIG"
CONFIG_PATH_DEFAULT = "./knotty.toml"


class Config(BaseModel):
    secret_key: SecretStr
    db_url: str
    connect_args: dict[str, Any] = {}
    token_expiry: timedelta = timedelta(hours=2)

    default_names: "DefaultNamesConfig"

    @staticmethod
    def load_from_toml(path: Path) -> "Config":
        Config.update_forward_refs()

        parsed = toml.load(path)

        return Config(**parsed)


class DefaultNamesConfig(BaseModel):
    namespace_owner_role = "owner"


def load_config() -> Config:
    path = os.environ.get(CONFIG_PATH_ENVIRON, CONFIG_PATH_DEFAULT)

    return Config.load_from_toml(Path(path))


config = load_config()
