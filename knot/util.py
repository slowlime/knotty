from typing import TypeVar
from click import Command

from knotty_client.types import UNSET, Unset
import typer
from typer.core import TyperGroup


T = TypeVar("T")

def assert_not_none(v: T | None) -> T:
    assert v is not None

    return v


def or_default(v: T | None, default: T) -> T:
    if v is None:
        return default

    return v


def coerce_unset_to_none(v: T | Unset) -> T | None:
    if isinstance(v, Unset):
        return None

    return v


def coerce_none_to_unset(v: T | None) -> T | Unset:
    if v is None:
        return UNSET

    return v
