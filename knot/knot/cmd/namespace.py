from typing import Annotated, Optional, assert_never

from knotty_client.api.default import (
    create_namespace_role,
    create_namespace_user,
    delete_namespace_role,
    delete_namespace_user,
    edit_namespace,
    edit_namespace_role,
    edit_namespace_user,
    get_namespace as api_get_namespace,
    create_namespace,
    delete_namespace,
    get_namespace_role,
    get_namespace_user,
)
from knotty_client.models import (
    HTTPValidationError,
    Message,
    NotFoundErrorModel,
    Namespace,
    NamespaceCreate,
    NamespaceRole,
    NamespaceUser,
    AlreadyExistsErrorModel,
    ErrorModel,
    NamespaceEdit,
    NamespaceUserCreate,
    NamespaceUserEdit,
    NamespaceRoleCreate,
    NamespaceRoleEdit,
    PermissionCode,
)
from rich import box
from rich.align import Align
from rich.columns import Columns
from rich.console import group
from rich.markdown import Markdown
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree
import typer

from knot.app import app
from knot.ctx import AuthenticatedContextObj, ContextObj
from knot.error import print_error
from knot.util import (
    assert_not_none,
    coerce_none_to_unset,
    coerce_unset_to_none,
    or_default,
)


namespace_app = typer.Typer()


def get_namespace(obj: ContextObj, namespace: str) -> Namespace:
    response = assert_not_none(api_get_namespace.sync(namespace, client=obj.client))

    match response:
        case HTTPValidationError() | NotFoundErrorModel():
            print_error(response, ctx=obj)
            raise typer.Abort()

        case Namespace():
            return response

        case _:
            assert_never(response)


@namespace_app.callback("namespace")
def namespace_cmd():
    """Namespace manipulation commands."""


@namespace_app.command("info")
def namespace_info(
    ctx: typer.Context,
    namespace: Annotated[str, typer.Argument(show_default=False)],
):
    """Fetch information about a namespace."""

    obj: ContextObj = ctx.obj
    response = get_namespace(obj, namespace)

    @group()
    def make_namespace_group(ns: Namespace):
        @group()
        def make_metadata_group(ns: Namespace):
            yield Text.assemble(
                "Namespace ",
                (ns.name, "bold"),
            )

            yield Text.assemble(
                "Created ",
                ("on", "italic"),
                " ",
                (str(ns.created_date), "bold"),
            )

            if (homepage := coerce_unset_to_none(ns.homepage)) is not None:
                yield Text.assemble(
                    "Homepage: ",
                    (homepage, "bold"),
                )

            @group()
            def make_role_group(role: NamespaceRole):
                yield Text.assemble(
                    "Created ",
                    ("by", "italic"),
                    " ",
                    (role.created_by, "bold"),
                    " ",
                    ("on", "italic"),
                    " ",
                    (str(role.created_date), "bold"),
                )

                yield Text.assemble(
                    "Updated ",
                    ("by", "italic"),
                    " ",
                    (role.updated_by, "bold"),
                    " ",
                    ("on", "italic"),
                    " ",
                    (str(role.updated_date), "bold"),
                )

                yield ""

                permission_tree = Tree("[italic]Permissions[/]")

                for permission in role.permissions:
                    permission_tree.add(str(permission))

                yield permission_tree

            yield ""

            role_columns = Columns(title="Namespace roles")

            for role in ns.roles:
                role_panel = Panel(
                    make_role_group(role),
                    title="[italic]Role[/] [bold]{name}[/]".format(
                        name=escape(role.name)
                    ),
                )

                role_columns.add_renderable(role_panel)

            yield role_columns

            @group()
            def make_user_group(user: NamespaceUser):
                yield Text.assemble(
                    "Role: ",
                    (user.role, "bold"),
                )

                yield Text.assemble(
                    "Added ",
                    ("by", "italic"),
                    " ",
                    (user.added_by, "bold"),
                    " ",
                    ("on", "italic"),
                    " ",
                    (str(user.added_date), "bold"),
                )

                yield Text.assemble(
                    "Updated ",
                    ("by", "italic"),
                    " ",
                    (user.updated_by, "bold"),
                    " ",
                    ("on", "italic"),
                    " ",
                    (str(user.updated_date), "bold"),
                )

            yield ""

            user_columns = Columns(title="Namespace members")

            for user in ns.users:
                user_panel = Panel(
                    make_user_group(user),
                    title="[italic]User[/] [bold]{name}[/]".format(
                        name=escape(user.username)
                    ),
                )
                user_columns.add_renderable(user_panel)

            yield user_columns

        info_table = Table(
            "Metadata",
            "Description",
            box=box.SIMPLE,
            padding=(0, 2),
            collapse_padding=False,
            show_edge=False,
            expand=True,
        )
        info_table.add_row(
            Align(make_metadata_group(ns), vertical="top"),
            Align(Markdown(ns.description), vertical="top"),
        )

        yield info_table

    obj.console.print(make_namespace_group(response))


@namespace_app.command("create")
def namespace_create(
    ctx: typer.Context,
    namespace: Annotated[str, typer.Argument(show_default=False)],
    description: Annotated[
        str, typer.Option("--description", "-d", show_default=False)
    ],
    homepage: Annotated[Optional[str], typer.Option("--homepage", "-h")] = None,
    no_homepage: Annotated[bool, typer.Option("--no-homepage")] = False,
):
    """Create a new namespace."""

    if homepage is not None and no_homepage:
        raise typer.BadParameter(
            "--homepage and --no-homepage are mutually exclusive.",
            ctx=ctx,
            param_hint="--no-homepage",
        )

    obj: AuthenticatedContextObj = ctx.obj.to_authenticated()

    request = NamespaceCreate(
        name=namespace, description=description, homepage=coerce_none_to_unset(homepage)
    )
    response = assert_not_none(
        create_namespace.sync(client=obj.client, json_body=request)
    )

    match response:
        case AlreadyExistsErrorModel() | ErrorModel() | HTTPValidationError():
            print_error(response, ctx=obj)
            raise typer.Abort()

        case Message():
            pass

        case _:
            assert_never(response)

    obj.console.print(
        "[bold green]Success![/] {message}".format(
            message=escape(response.message),
        )
    )


@namespace_app.command("edit")
def namespace_edit(
    ctx: typer.Context,
    namespace: Annotated[str, typer.Argument(show_default=False)],
    description: Annotated[
        Optional[str],
        typer.Option(
            "-d", "--description", show_default="Current description"  # type: ignore
        ),
    ] = None,
    name: Annotated[
        Optional[str],
        typer.Option("-n", "--name", show_default="Current name"),  # type: ignore
    ] = None,
    no_homepage: Annotated[bool, typer.Option("--no-homepage")] = False,
    homepage: Annotated[
        Optional[str],
        typer.Option(
            "-h", "--homepage", show_default="Current homepage"  # type: ignore
        ),
    ] = None,
):
    """Edit namespace metadata."""

    if homepage is not None and no_homepage:
        raise typer.BadParameter(
            "--homepage and --no-homepage are mutually exclusive.",
            ctx=ctx,
            param_hint="--no-homepage",
        )

    obj: AuthenticatedContextObj = ctx.obj.to_authenticated()
    ns = get_namespace(obj, namespace)

    request = NamespaceEdit(
        name=or_default(name, namespace),
        description=or_default(description, ns.description),
        homepage=coerce_none_to_unset(
            or_default(homepage, coerce_unset_to_none(ns.homepage))
            if not no_homepage
            else None
        ),
    )
    response = assert_not_none(
        edit_namespace.sync(namespace, client=obj.client, json_body=request)
    )

    match response:
        case AlreadyExistsErrorModel() | ErrorModel() | HTTPValidationError() | NotFoundErrorModel():
            print_error(response, ctx=obj)
            raise typer.Abort()

        case Message():
            pass

        case _:
            assert_never(response)

    obj.console.print(
        "[bold green]Success![/] {message}".format(
            message=escape(response.message),
        )
    )


@namespace_app.command("delete")
def namespace_delete(
    ctx: typer.Context,
    namespace: Annotated[str, typer.Argument(show_default=False)],
    yes: Annotated[bool, typer.Option("--yes", "-y")] = False,
):
    """Delete a namespace."""

    obj: AuthenticatedContextObj = ctx.obj.to_authenticated()

    if not yes:
        typer.confirm("Are you sure you want to delete the namespace?", abort=True)

    response = assert_not_none(delete_namespace.sync(namespace, client=obj.client))

    match response:
        case ErrorModel() | HTTPValidationError() | NotFoundErrorModel():
            print_error(response, ctx=obj)
            raise typer.Abort()

        case Message():
            pass

        case _:
            assert_never(response)

    obj.console.print(
        "[bold green]Success![/] {message}".format(
            message=escape(response.message),
        )
    )


user_app = typer.Typer()


@user_app.callback("user")
def user_cmd():
    """Namespace member manipulation commands."""


@user_app.command("add")
def user_add(
    ctx: typer.Context,
    namespace: Annotated[str, typer.Argument(show_default=False)],
    username: Annotated[str, typer.Argument(show_default=False)],
    role: Annotated[str, typer.Option("-r", "--role", show_default=False)],
):
    """Add a user to a namespace."""

    obj: AuthenticatedContextObj = ctx.obj.to_authenticated()

    request = NamespaceUserCreate(username, role)
    response = assert_not_none(
        create_namespace_user.sync(
            namespace,
            client=obj.client,
            json_body=request,
        )
    )

    match response:
        case AlreadyExistsErrorModel() | ErrorModel() | HTTPValidationError() | NotFoundErrorModel():
            print_error(response, ctx=obj)
            raise typer.Abort()

        case Message():
            pass

        case _:
            assert_never(response)

    obj.console.print(
        "[bold green]Success![/] {message}".format(
            message=escape(response.message),
        )
    )


@user_app.command("edit")
def user_edit(
    ctx: typer.Context,
    namespace: Annotated[str, typer.Argument(show_default=False)],
    username: Annotated[str, typer.Argument(show_default=False)],
    role: Annotated[
        Optional[str],
        typer.Option("-r", "--role", show_default="Current role"),  # type: ignore
    ] = None,
    yes: Annotated[bool, typer.Option("--yes", "-y")] = False,
):
    """Edit namespace member metadata."""

    obj: AuthenticatedContextObj = ctx.obj.to_authenticated()

    user_response = assert_not_none(
        get_namespace_user.sync(
            namespace,
            username,
            client=obj.client,
        )
    )

    match user_response:
        case HTTPValidationError() | NotFoundErrorModel():
            print_error(user_response, ctx=obj)
            raise typer.Abort()

        case NamespaceUser():
            user = user_response

        case _:
            assert_never(user_response)

    if username == obj.session.username and not yes:
        typer.confirm(
            "You are going to update your metadata in the namespace. "
            + "Are you sure you want to continue?",
            abort=True,
        )

    request = NamespaceUserEdit(role=or_default(role, user.role))
    response = assert_not_none(
        edit_namespace_user.sync(
            namespace,
            username,
            client=obj.client,
            json_body=request,
        )
    )

    match response:
        case ErrorModel() | HTTPValidationError() | NotFoundErrorModel():
            print_error(response, ctx=obj)
            raise typer.Abort()

        case Message():
            pass

        case _:
            assert_never(response)

    obj.console.print(
        "[bold green]Success![/] {message}".format(
            message=escape(response.message),
        )
    )


@user_app.command("delete")
def user_delete(
    ctx: typer.Context,
    namespace: Annotated[str, typer.Argument(show_default=False)],
    username: Annotated[str, typer.Argument(show_default=False)],
    yes: Annotated[bool, typer.Option("--yes", "-y")] = False,
):
    """Remove a user from a namespace."""

    obj: AuthenticatedContextObj = ctx.obj.to_authenticated()

    if not yes:
        if username == obj.session.username:
            typer.confirm(
                "You are about to remove yourself from this namespace. "
                + "You will lose access to any resources managed by it. "
                + "Are you sure you want to continue?",
                abort=True,
            )
        else:
            typer.confirm(
                "Are you sure you want to remove the user from the namespace?",
                abort=True,
            )

    response = assert_not_none(
        delete_namespace_user.sync(
            namespace,
            username,
            client=obj.client,
        )
    )

    match response:
        case ErrorModel() | HTTPValidationError() | NotFoundErrorModel():
            print_error(response, ctx=obj)
            raise typer.Abort()

        case Message():
            pass

        case _:
            assert_never(response)

    obj.console.print(
        "[bold green]Success![/] {message}".format(
            message=escape(response.message),
        )
    )


role_app = typer.Typer()


@role_app.callback("role")
def role_cmd():
    """Namespace role manipulation commands."""


@role_app.command("create")
def role_create(
    ctx: typer.Context,
    namespace: Annotated[str, typer.Argument(show_default=False)],
    role: Annotated[str, typer.Argument(show_default=False)],
    permissions: Annotated[
        list[PermissionCode], typer.Option("--permission", "-p")
    ] = [],
    no_permissions: Annotated[bool, typer.Option("--no-permissions")] = False,
):
    """Create a namespace role."""

    if permissions and no_permissions:
        raise typer.BadParameter(
            "--permissions and --no-permissions are mutually exclusive.",
            ctx=ctx,
            param_hint="--no-permissions",
        )

    obj: AuthenticatedContextObj = ctx.obj.to_authenticated()

    request = NamespaceRoleCreate(name=role, permissions=permissions)
    response = assert_not_none(
        create_namespace_role.sync(
            namespace=namespace,
            client=obj.client,
            json_body=request,
        )
    )

    match response:
        case AlreadyExistsErrorModel() | ErrorModel() | HTTPValidationError() | NotFoundErrorModel():
            print_error(response, ctx=obj)
            raise typer.Abort()

        case Message():
            pass

        case _:
            assert_never(response)

    obj.console.print(
        "[bold green]Success![/] {message}".format(
            message=escape(response.message),
        )
    )


@role_app.command("edit")
def role_edit(
    ctx: typer.Context,
    namespace: Annotated[str, typer.Argument(show_default=False)],
    role: Annotated[str, typer.Argument(show_default=False)],
    name: Annotated[
        Optional[str],
        typer.Option("-n", "--name", show_default="Current name"),  # type: ignore
    ] = None,
    permissions: Annotated[
        Optional[list[PermissionCode]],
        typer.Option(
            "--permission",
            "-p",
            show_default="Current permissions",  # type: ignore
        ),
    ] = None,
    no_permissions: Annotated[bool, typer.Option("--no-permissions")] = False,
):
    """Edit namespace role metadata."""

    if permissions and no_permissions:
        raise typer.BadParameter(
            "--permission and --no-permissions are mutually exclusive.",
            ctx=ctx,
            param_hint="--no-permissions",
        )

    obj: AuthenticatedContextObj = ctx.obj.to_authenticated()

    role_response = assert_not_none(
        get_namespace_role.sync(
            namespace,
            role,
            client=obj.client,
        )
    )

    match role_response:
        case HTTPValidationError() | NotFoundErrorModel():
            print_error(role_response, ctx=obj)
            raise typer.Abort()

        case NamespaceRole():
            current_role = role_response

        case _:
            assert_never(role_response)

    if no_permissions:
        permissions = None

    request = NamespaceRoleEdit(
        name=or_default(name, current_role.name),
        permissions=or_default(permissions, current_role.permissions),
    )
    response = assert_not_none(
        edit_namespace_role.sync(
            namespace,
            role,
            client=obj.client,
            json_body=request,
        )
    )

    match response:
        case AlreadyExistsErrorModel() | ErrorModel() | HTTPValidationError() | NotFoundErrorModel():
            print_error(response, ctx=obj)
            raise typer.Abort()

        case Message():
            pass

        case _:
            assert_never(response)

    obj.console.print(
        "[bold green]Success![/] {message}".format(
            message=escape(response.message),
        )
    )


@role_app.command("delete")
def role_delete(
    ctx: typer.Context,
    namespace: Annotated[str, typer.Argument(show_default=False)],
    role: Annotated[str, typer.Argument(show_default=False)],
    yes: Annotated[bool, typer.Option("--yes", "-y")] = False,
):
    """Delete a namespace role."""

    obj: AuthenticatedContextObj = ctx.obj.to_authenticated()

    if not yes:
        typer.confirm(
            "Are you sure you want to remove the role from the namespace?", abort=True
        )

    response = assert_not_none(
        delete_namespace_role.sync(
            namespace,
            role,
            client=obj.client,
        )
    )

    match response:
        case ErrorModel() | HTTPValidationError() | NotFoundErrorModel():
            print_error(response, ctx=obj)
            raise typer.Abort()

        case Message():
            pass

        case _:
            assert_never(response)

    obj.console.print(
        "[bold green]Success![/] {message}".format(
            message=escape(response.message),
        )
    )


namespace_app.add_typer(user_app)
namespace_app.add_typer(role_app)

app.add_typer(namespace_app)
