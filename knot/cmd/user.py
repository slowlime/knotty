from typing import Annotated, Optional
from typing_extensions import assert_never
from knotty_client.api.default import (
    login as api_login,
    register as api_register,
    get_user,
)
from knotty_client.models import (
    AuthToken,
    BodyLoginLoginPost,
    ErrorModel,
    HTTPValidationError,
    Message,
    UserRegister,
    NotFoundErrorModel,
    UserInfo,
)
from rich.console import group
from rich.markup import escape
from rich.text import Text
import typer

from knot.app import app
from knot.auth import Session, remove_session, save_session
from knot.ctx import AuthenticatedContextObj, ContextObj
from knot.error import print_error
from knot.util import assert_not_none


def request_token(obj: ContextObj, username: str, password: str):
    model = BodyLoginLoginPost(
        username=username, password=password, grant_type="password"
    )
    response = assert_not_none(api_login.sync(client=obj.client, form_data=model))

    match response:
        case ErrorModel() | HTTPValidationError():
            print_error(response, ctx=obj)
            raise typer.Abort()

        case AuthToken():
            pass

        case _:
            assert_never(response)

    session = Session(username=username, token=response.access_token)
    save_session(session)


@app.command()
def login(ctx: typer.Context):
    """Sign in to the repository."""

    obj: ContextObj = ctx.obj

    username = typer.prompt("Enter username")
    password = typer.prompt("Enter password", hide_input=True)

    request_token(obj, username, password)
    obj.console.print(
        "[bold green]Success![/] Authorized as [b]{username}[/]".format(
            username=escape(username),
        )
    )


@app.command()
def logout(ctx: typer.Context):
    """Log out of the current session."""

    obj: AuthenticatedContextObj = ctx.obj.to_authenticated()

    remove_session()
    obj.console.print(
        "[bold green]Success![/] Logged out of [b]{username}[/]".format(
            username=escape(obj.session.username),
        )
    )


@app.command()
def register(ctx: typer.Context):
    """Register a new account."""

    obj: ContextObj = ctx.obj

    username = typer.prompt("Enter username")
    email = typer.prompt("Enter email")
    password = typer.prompt(
        "Enter password", hide_input=True, confirmation_prompt="Repeat password"
    )

    model = UserRegister(username=username, email=email, password=password)
    response = assert_not_none(api_register.sync(client=obj.client, json_body=model))

    match response:
        case ErrorModel() | HTTPValidationError():
            print_error(response, ctx=obj)
            raise typer.Abort()

        case Message():
            pass

        case _:
            assert_never(response)

    obj.console.print(
        "[bold green]Registration successful![/] {message}".format(
            message=escape(response.message),
        )
    )

    request_token(obj, username, password)
    obj.console.print(
        "[bold green]Success![/] Authorized as [b]{username}[/]".format(
            username=escape(username),
        )
    )


@app.command()
def account(
    ctx: typer.Context,
    username: Annotated[
        Optional[str], typer.Argument(show_default="Current user")
    ] = None,
):
    """Show information about a user."""

    obj: AuthenticatedContextObj = ctx.obj.to_authenticated()

    if username is None:
        username = obj.session.username

    response = assert_not_none(get_user.sync(username=username, client=obj.client))

    match response:
        case ErrorModel() | HTTPValidationError() | NotFoundErrorModel():
            print_error(response, ctx=obj)
            raise typer.Abort()

        case UserInfo():
            pass

        case _:
            assert_never(response)

    @group()
    def get_group(user: UserInfo):
        yield Text.assemble(
            "Username: ",
            (user.username, "bold"),
        )

        yield Text.assemble(
            "Email: ",
            (user.email, "bold"),
        )

        yield Text.assemble(
            "Registered ",
            ("on", "italic"),
            " ",
            (str(user.registered), "bold"),
        )

        if user.namespaces:
            namespace_text = Text.assemble("Member of namespaces:")

            for i, namespace in enumerate(user.namespaces):
                if i == 0:
                    namespace_text.append(" ")
                else:
                    namespace_text.append(", ")

                namespace_text.append(namespace, "bold")

            yield namespace_text

    obj.console.print(get_group(response))
