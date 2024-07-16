from datetime import timedelta
from functools import cache
import logging
import os

from pathlib import Path
from fastapi import Depends

import toml

from typing import Annotated, Any
from pydantic import BaseModel, SecretStr


CONFIG_PATH_ENVIRON = "KNOTTY_CONFIG"
CONFIG_PATH_DEFAULT = "./knotty.toml"


class Config(BaseModel):
    secret_key: SecretStr
    db_url: str
    connect_args: dict[str, Any] = {}
    use_static_pool: bool = False
    token_expiry: timedelta = timedelta(hours=2)

    default_names: "DefaultNamesConfig"
    logging: dict[str, Any] = {}

    @staticmethod
    def load_from_toml(path: Path) -> "Config":
        parsed = toml.load(path)

        return Config(**parsed)

    def __hash__(self):
        return hash(id(self))

    def __eq__(self, other):
        return id(self) == id(other)


class DefaultNamesConfig(BaseModel):
    namespace_owner_role = "owner"


def load_config() -> Config:
    path = os.environ.get(CONFIG_PATH_ENVIRON, CONFIG_PATH_DEFAULT)

    return Config.load_from_toml(Path(path))


@cache
def get_config() -> Config:
    logging.debug("loading a config")
    return load_config()


Config.update_forward_refs()
ConfigDep = Annotated[Config, Depends(get_config)]
