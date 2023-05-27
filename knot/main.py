# re-export
from knot.app import app  # pyright: ignore

# we need these imports for side-effects only
import knot.cmd.package  # pyright: ignore
import knot.cmd.user  # pyright: ignore
