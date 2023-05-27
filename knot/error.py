from functools import singledispatch

from knotty_client.models import HTTPValidationError
from knotty_client.types import Unset

from knot.ctx import ContextObj


@singledispatch
def print_error(err, *, ctx: ContextObj):
    ctx.console.print(str(err), style="bold red")


@print_error.register
def _(err: HTTPValidationError, *, ctx: ContextObj):
    if isinstance(err.detail, Unset):
        print_error.dispatch(object)(
            "The server has returned a validation error for the request", ctx=ctx
        )

        return

    for detail in err.detail:
        print_error.dispatch(object)(detail.msg, ctx=ctx)
