from pathlib import Path
from typing import Annotated, Optional
from typing_extensions import assert_never

from knotty_client.api.default import (
    get_packages,
    get_package as api_get_package,
    create_package,
    edit_package,
    delete_package,
    create_package_tag,
    edit_package_tag,
    delete_package_tag,
    create_package_version,
    edit_package_version,
    delete_package_version,
    search_packages,
)
from knotty_client.models import (
    HTTPValidationError,
    ErrorModel,
    NotFoundErrorModel,
    Package,
    PackageCreate,
    PackageEdit,
    PackageVersion,
    PackageTag,
    AlreadyExistsErrorModel,
    Message,
    UnknownDependenciesErrorModel,
    ChecksumAlgorithm,
    PackageVersionCreate,
    PackageVersionEdit,
)
from knotty_client.types import UNSET
from rich import box
from rich.align import Align
from rich.console import group
from rich.markdown import Markdown
from rich.markup import escape
from rich.padding import Padding
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.table import Table
from rich.tree import Tree
from rich.text import Text
from rich.style import Style
import requests
import typer

from knot.app import app
from knot.ctx import AuthenticatedContextObj, ContextObj
from knot.error import print_error
from knot.manifest import Version, read_manifest
from knot.spec import PackageSpec, Tag
from knot.util import (
    assert_not_none,
    coerce_none_to_unset,
    coerce_unset_to_none,
    or_default,
)


DEFAULT_MANIFEST_PATH = Path(".") / "knot-manifest.toml"


@app.command("list")
def list_packages(
    ctx: typer.Context, query: Annotated[Optional[str], typer.Argument()] = None
):
    """List (or search) packages in the repository."""

    obj: ContextObj = ctx.obj

    if query is None:
        packages = assert_not_none(get_packages.sync(client=obj.client))
    else:
        packages = assert_not_none(search_packages.sync(client=obj.client, query=query))

    tree = Tree("Package list:")

    for package in packages:
        info = Text.assemble(
            (package.name, Style(bold=True)),
            " - ",
            package.summary,
            "\n",
        )

        info.append("by ", Style(italic=True))

        for i, owner in enumerate(package.owners):
            if i > 0:
                info.append(", ")

            info.append(owner, Style(bold=True))

        info.append(" " * 4)

        if isinstance(package.namespace, str):
            info.append("managed by ", Style(italic=True)).append(
                package.namespace, Style(bold=True)
            ).append(" " * 4)

        info.append(str(package.downloads), Style(bold=True)).append(
            " downloads", Style(italic=True)
        ).append(" " * 4)

        info.append("last updated on ", Style(italic=True)).append(
            str(package.updated_date), Style(bold=True)
        )

        if package.labels:
            info.append("\n").append("labeled ", Style(italic=True))

            for i, label in enumerate(package.labels):
                if i > 0:
                    info.append(", ")

                info.append(label, Style(bold=True))

        tree.add(Padding(info, pad=(0, 0, 1, 0)))

    obj.console.print(tree)


def get_package(pkg: str, obj: ContextObj) -> Package:
    match response := assert_not_none(api_get_package.sync(pkg, client=obj.client)):
        case HTTPValidationError() | NotFoundErrorModel():
            print_error(response, ctx=obj)
            raise typer.Abort()

        case Package():
            pass

        case _:
            assert_never(response)

    return response


@app.command()
def info(ctx: typer.Context, pkg: Annotated[str, typer.Argument(show_default=False)]):
    """Fetch information about a package."""

    obj: ContextObj = ctx.obj

    package = get_package(pkg, obj)

    @group()
    def get_group(package: Package):
        yield Text.assemble(
            "Name: ",
            (package.name, "bold"),
        )

        yield Text.assemble(
            "Summary: ",
            (package.summary, "bold"),
        )

        if package.labels:
            label_text = Text().append("Labeled")

            for i, label in enumerate(package.labels):
                if i == 0:
                    label_text.append(" ")
                else:
                    label_text.append(", ")

                label_text.append(label, "bold")

            yield label_text

        owner_text = Text().append("Owned by")

        for i, owner in enumerate(package.owners):
            if i == 0:
                owner_text.append(" ")
            else:
                owner_text.append(", ")

            owner_text.append(owner, "bold")

        yield owner_text

        if isinstance(package.namespace, str):
            yield Text.assemble(
                "Managed by ",
                (package.namespace, "bold"),
            )

        yield Text.assemble(
            "Created ",
            ("by", "italic"),
            " ",
            (package.created_by, "bold"),
            " ",
            ("on", "italic"),
            " ",
            (str(package.created_date), "bold"),
        )

        yield Text.assemble(
            "Updated ",
            ("by", "italic"),
            " ",
            (package.updated_by, "bold"),
            " ",
            ("on", "italic"),
            " ",
            (str(package.updated_date), "bold"),
        )

        yield Text.assemble(
            "Downloads: ",
            (str(package.downloads), "bold"),
        )

        if package.tags:
            tag_tree = Tree("Tags:")

            for tag in package.tags:
                tag_tree.add(
                    Text.assemble(
                        (tag.name, "bold"),
                        ": ",
                        ("references version", "italic"),
                        " ",
                        (tag.version, "bold"),
                    )
                )

            yield tag_tree
        else:
            yield Text.assemble(
                "Tags: ",
                ("none", "italic"),
            )

        @group()
        def get_version_group(version: PackageVersion):
            yield Text.assemble(
                "Created ",
                ("by", "italic"),
                " ",
                (version.created_by, "bold"),
                " ",
                ("on", "italic"),
                " ",
                (str(version.created_date), "bold"),
            )

            yield Text.assemble(
                "Downloads: ",
                (str(version.downloads), "bold"),
            )

            if isinstance(version.repository, str):
                yield Text.assemble(
                    "Repository URL: ",
                    version.repository,
                )

            if isinstance(version.tarball, str):
                yield Text.assemble(
                    "Download URL: ",
                    version.tarball,
                )

            if version.checksums:
                checksum_tree = Tree("Checksums:")

                for checksum in version.checksums:
                    checksum_tree.add(
                        Text.assemble(
                            (str(checksum.algorithm), "bold"),
                            ": ",
                            checksum.value,
                        )
                    )

                yield checksum_tree

            if version.dependencies:
                dependency_tree = Tree("Dependencies:")

                for dep in version.dependencies:
                    dependency_tree.add(
                        Text.assemble(
                            (dep.package, "bold"),
                            ": ",
                            ("depends on version", "italic"),
                            " ",
                            (dep.spec, "bold"),
                        )
                    )

                yield dependency_tree

        for version in package.versions:
            grid = Table(
                "[italic]Version[/] [bold]{version}[/]".format(
                    version=escape(version.version),
                ),
                "Description",
                expand=True,
                padding=(0, 2),
                collapse_padding=False,
                show_edge=False,
                box=box.HORIZONTALS,
            )

            metadata = get_version_group(version)
            description = Markdown(version.description)
            grid.add_row(
                Align(metadata, vertical="top"), Align(description, vertical="top")
            )

            yield ""
            yield grid

    obj.console.print(get_group(package))


@app.command()
def download(
    ctx: typer.Context,
    pkg: Annotated[
        str,
        typer.Argument(
            help="Package specification (pkg-name, pkg-name:1.0.0, pkg-name:tag)",
            show_default=False,
        ),
    ],
    out_path: Annotated[
        Path,
        typer.Argument(
            show_default=False,
            file_okay=True,
            dir_okay=False,
            writable=True,
        ),
    ],
    yes: Annotated[bool, typer.Option("--yes", "-y")] = False,
):
    """Download a package."""

    spec = PackageSpec.from_str(pkg)
    obj: ContextObj = ctx.obj

    if not yes and out_path.exists():
        typer.confirm(
            "File already exists. Are you sure you want to overwrite it?", abort=True
        )

    package = get_package(spec.package, obj)

    if not package.versions:
        print_error("Package defines no versions.", ctx=obj)
        raise typer.Abort()

    match spec.version:
        case None:
            version = max(package.versions, key=lambda x: Version.parse(x.version))

        case Tag() as tag_spec:
            for tag in package.tags:
                if tag.name == tag_spec:
                    break
            else:
                print_error("Tag does not exist.", ctx=obj)
                raise typer.Abort()

            for version in package.versions:
                if str(version.version) == tag.version:
                    break
            else:
                print_error(
                    f"Package references non-existent version {tag.version}", ctx=obj
                )
                raise typer.Abort()

        case Version() as version_spec:
            for version in package.versions:
                if Version.parse(version.version) == version_spec:
                    break
            else:
                print_error("Version does not exist.", ctx=obj)
                raise typer.Abort()

        case _:
            assert_never(spec.version)

    url = version.tarball

    if not isinstance(url, str):
        print_error(
            f"Version {version.version} does not link to downloadable tarball", ctx=obj
        )
        raise typer.Abort()

    obj.console.print(
        f"Downloading version [italic]{escape(version.version)}[/]: {escape(url)}..."
    )

    with Progress(
        TextColumn("[bold blue]Downloading..."),
        BarColumn(bar_width=None),
        TaskProgressColumn(),
        DownloadColumn(binary_units=True),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=obj.console,
    ) as progress:
        r = requests.get(
            url,
            stream=True,
            headers={
                "User-Agent": "knot",
            },
        )
        r.raise_for_status()

        with out_path.open("wb") as f:
            content_length = r.headers.get("content-length")
            total = None

            if content_length is not None:
                try:
                    total = int(content_length, base=10)
                except ValueError:
                    pass

            task = progress.add_task("Downloading...", total=total)

            for chunk in r.iter_content(1024):
                f.write(chunk)
                progress.advance(task, len(chunk))

    obj.console.print(
        "[bold green]Success![/] Downloaded to [italic]{path}[/]".format(
            path=escape(str(out_path)),
        )
    )


pkg_app = typer.Typer()


@pkg_app.callback("pkg")
def pkg_cmd():
    """Package manipulation commands."""


@pkg_app.command("create")
def pkg_create(
    ctx: typer.Context,
    pkg: Annotated[str, typer.Argument(show_default=False)],
    description: Annotated[str, typer.Option("--description", "-d")],
    labels: Annotated[list[str], typer.Option("--label", "-l")] = [],
    owners: Annotated[list[str], typer.Option("--owner", "-o")] = [],
    namespace: Optional[str] = None,
):
    """Create a new package."""

    obj: AuthenticatedContextObj = ctx.obj.to_authenticated()

    model = PackageCreate(
        name=pkg,
        summary=description,
        versions=[],
        tags=[],
        namespace=namespace if namespace is not None else UNSET,
        labels=labels,
        owners=owners,
    )

    response = assert_not_none(create_package.sync(client=obj.client, json_body=model))
    match response:
        case UnknownDependenciesErrorModel() | NotFoundErrorModel() | AlreadyExistsErrorModel() | ErrorModel() | HTTPValidationError():
            print_error(response, ctx=obj)
            raise typer.Abort()

        case Message():
            obj.console.print(
                "[bold green]Success![/] {message}".format(
                    message=escape(response.message),
                )
            )

            return

    assert_never(response)


@pkg_app.command("edit")
def pkg_edit(
    ctx: typer.Context,
    pkg: Annotated[str, typer.Argument(show_default=False)],
    name: Annotated[
        Optional[str],
        typer.Option("--name", show_default="Current name"),  # type: ignore
    ] = None,
    description: Annotated[
        Optional[str],
        typer.Option(
            "--description", "-d", show_default="Current description"  # type: ignore
        ),
    ] = None,
    namespace: Annotated[
        Optional[str],
        typer.Option(
            "--namespace",
            "-n",
            show_default="Current namespace",  # type: ignore
        ),
    ] = None,
    no_namespace: Annotated[bool, typer.Option("--no-namespace")] = False,
    labels: Annotated[
        Optional[list[str]],
        typer.Option("--label", "-l", show_default="Current labels"),  # type: ignore
    ] = None,
    no_labels: Annotated[bool, typer.Option("--no-labels")] = False,
    owners: Annotated[
        Optional[list[str]],
        typer.Option("--owner", "-o", show_default="Current owners"),  # type: ignore
    ] = None,
    yes: Annotated[bool, typer.Option("--yes", "-y")] = False,
):
    """Edit an already existing package."""

    if no_namespace and namespace is not None:
        raise typer.BadParameter(
            "--namespace and --no-namespace are mutually exclusive.",
            ctx=ctx,
            param_hint="--no-namespace",
        )

    if no_labels and labels:
        raise typer.BadParameter(
            "--label and --no-labels are mutually exclusive.",
            ctx=ctx,
            param_hint="--no-labels",
        )

    obj: AuthenticatedContextObj = ctx.obj.to_authenticated()
    current_package = get_package(pkg, obj)

    if not owners:
        owners = None

    if not labels and not no_labels:
        labels = None

    if (
        not yes
        and owners is not None
        and obj.session.username in current_package.owners
        and obj.session.username not in owners
    ):
        # 'tis a potential footgun
        typer.confirm(
            "You have not specified your username in the owner list. "
            + "Continuing will relinquish your ownership of the package. "
            + "Are you sure you want to continue?",
            abort=True,
        )

    request = PackageEdit(
        name=or_default(name, current_package.name),
        summary=or_default(description, current_package.summary),
        labels=or_default(labels, current_package.labels),
        owners=or_default(owners, current_package.owners),
        namespace=coerce_none_to_unset(
            or_default(namespace, coerce_unset_to_none(current_package.namespace))
            if not no_namespace
            else None
        ),
    )

    response = assert_not_none(
        edit_package.sync(pkg, client=obj.client, json_body=request)
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


@pkg_app.command("delete")
def pkg_delete(
    ctx: typer.Context,
    pkg: Annotated[str, typer.Argument(show_default=False)],
    yes: Annotated[bool, typer.Option("--yes", "-y")] = False,
):
    """Delete a package."""

    obj: AuthenticatedContextObj = ctx.obj.to_authenticated()

    if not yes:
        typer.confirm("Are you sure you want to remove the package?", abort=True)

    match response := assert_not_none(delete_package.sync(pkg, client=obj.client)):
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


tag_app = typer.Typer()


@tag_app.callback("tag")
def tag_cmd():
    """Manage package tags."""


@tag_app.command("create")
def tag_create(
    ctx: typer.Context,
    pkg: Annotated[str, typer.Argument(show_default=False)],
    tag: Annotated[str, typer.Argument(show_default=False)],
    version: Annotated[str, typer.Argument(show_default=False)],
):
    """Create a new package tag pointing to the provided version."""

    obj: AuthenticatedContextObj = ctx.obj.to_authenticated()

    request = PackageTag(name=tag, version=version)
    response = assert_not_none(
        create_package_tag.sync(pkg, client=obj.client, json_body=request)
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


@tag_app.command("edit")
def tag_edit(
    ctx: typer.Context,
    pkg: Annotated[str, typer.Argument(show_default=False)],
    tag: Annotated[str, typer.Argument(show_default=False)],
    version: Annotated[str, typer.Argument(show_default=False)],
    name: Annotated[
        Optional[str],
        typer.Option("--name", show_default="Current tag name"),  # type: ignore
    ] = None,
):
    """Update a package tag to point to the provided version."""

    obj: AuthenticatedContextObj = ctx.obj.to_authenticated()

    request = PackageTag(name=or_default(name, tag), version=version)
    response = assert_not_none(
        edit_package_tag.sync(pkg, tag, client=obj.client, json_body=request),
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
        "[bold green]Success![/] {message}".format(message=escape(response.message))
    )


@tag_app.command("delete")
def tag_delete(
    ctx: typer.Context,
    pkg: Annotated[str, typer.Argument(show_default=False)],
    tag: Annotated[str, typer.Argument(show_default=False)],
    yes: Annotated[bool, typer.Option("--yes", "-y")] = False,
):
    """Delete a package tag."""

    obj: AuthenticatedContextObj = ctx.obj.to_authenticated()

    if not yes:
        typer.confirm("Are you sure you want to delete the package tag?", abort=True)

    response = assert_not_none(delete_package_tag.sync(pkg, tag, client=obj.client))

    match response:
        case ErrorModel() | HTTPValidationError() | NotFoundErrorModel():
            print_error(response, ctx=obj)
            raise typer.Abort()

        case Message():
            pass

        case _:
            assert_never(response)

    obj.console.print(
        "[bold green]Success![/] {message}".format(message=escape(response.message))
    )


@app.command()
def publish(
    ctx: typer.Context,
    pkg: Annotated[str, typer.Argument(show_default=False)],
    manifest_path: Annotated[
        Path, typer.Option("--manifest", "-m")
    ] = DEFAULT_MANIFEST_PATH,
    replace: Annotated[Optional[str], typer.Option("--replace")] = None,
    yes: Annotated[bool, typer.Option("--yes", "-y")] = False,
):
    """Publish a package manifest as a new version."""

    obj: AuthenticatedContextObj = ctx.obj.to_authenticated()
    manifest = read_manifest(manifest_path)

    request = {
        "version": str(manifest.version),
        "description": manifest.description,
        "checksums": [
            {
                "algorithm": ChecksumAlgorithm(checksum.algorithm.lower()),
                "value": checksum.value,
            }
            for checksum in manifest.checksums
        ],
        "dependencies": [
            {
                "package": dep.package,
                "spec": dep.spec,
            }
            for dep in manifest.dependencies
        ],
        "repository": coerce_none_to_unset(manifest.repository),
        "tarball": coerce_none_to_unset(manifest.tarball),
    }

    response = None
    manually_confirmed = False

    if replace is None:
        response = assert_not_none(
            create_package_version.sync(
                pkg,
                client=obj.client,
                json_body=PackageVersionCreate.from_dict(request),
            )
        )

        match response:
            case AlreadyExistsErrorModel() if response.what == "Version" and (
                yes
                or (
                    manually_confirmed := typer.confirm(
                        "This version of the package already exists. "
                        + "Are you sure you want to replace it?"
                    )
                )
            ):
                pass

            case AlreadyExistsErrorModel() | ErrorModel() | HTTPValidationError() | NotFoundErrorModel() | UnknownDependenciesErrorModel():
                print_error(response, ctx=obj)
                raise typer.Abort()

            case Message():
                pass

            case _:
                assert_never(response)

        if isinstance(response, AlreadyExistsErrorModel):
            obj.console.print(
                "[bold red]Version already exists, replacing...[/] "
                + (
                    "(forced by [italic]--yes[/])"
                    if not manually_confirmed
                    else "(forced by user)"
                )
            )
            replace = str(manifest.version)
    elif not yes:
        typer.confirm("Are you sure you want to replace the version?", abort=True)

    if replace:
        response = assert_not_none(
            edit_package_version.sync(
                package=pkg,
                version=replace,
                client=obj.client,
                json_body=PackageVersionEdit.from_dict(request),
            )
        )

        match response:
            case AlreadyExistsErrorModel() | ErrorModel() | HTTPValidationError() | NotFoundErrorModel() | UnknownDependenciesErrorModel():
                print_error(response, ctx=obj)
                raise typer.Abort()

            case Message():
                pass

            case _:
                assert_never(response)

    assert isinstance(response, Message)
    obj.console.print(
        "[bold green]Success![/] {message}".format(
            message=escape(response.message),
        )
    )


@app.command()
def unpublish(
    ctx: typer.Context,
    pkg: Annotated[str, typer.Argument(show_default=False)],
    version: Annotated[str, typer.Argument(show_default=False)],
    yes: Annotated[bool, typer.Option("--yes", "-y")] = False,
):
    """Remove a package version."""

    obj: AuthenticatedContextObj = ctx.obj.to_authenticated()

    if not yes:
        typer.confirm("Are you sure you want to remove the version?", abort=True)

    response = assert_not_none(
        delete_package_version.sync(pkg, version, client=obj.client),
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


app.add_typer(pkg_app)
app.add_typer(tag_app)
