from typing import Annotated, Optional

from knotty_client.api.default import get_packages, get_package
from knotty_client.models import (
    HTTPValidationError,
    NotFoundErrorModel,
    Package,
    PackageVersion,
)
from knotty_client.types import Unset
from rich import box
from rich.align import Align
from rich.console import group
from rich.markdown import Markdown
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.text import Text
from rich.style import Style
import typer

from knot.app import app
from knot.ctx import ContextObj
from knot.error import print_error
from knot.util import assert_not_none


@app.command()
def list(ctx: typer.Context, query: Annotated[Optional[str], typer.Argument()] = None):
    """List (or search) packages in the repository."""

    obj: ContextObj = ctx.obj

    if query is None:
        packages = assert_not_none(get_packages.sync(client=obj.client))
    else:
        raise NotImplementedError()

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

        info.append("\t")

        if isinstance(package.namespace, str):
            info.append("managed by ", Style(italic=True)).append(
                package.namespace, Style(bold=True)
            ).append("\t")

        info.append(str(package.downloads), Style(bold=True)).append(
            " downloads", Style(italic=True)
        ).append("\t")

        info.append("last updated on ", Style(italic=True)).append(
            str(package.updated_date), Style(bold=True)
        )

        if package.labels:
            info.append("\n").append("labeled ", Style(italic=True))

            for i, label in enumerate(package.labels):
                if i > 0:
                    info.append(", ")

                info.append(label, Style(bold=True))

        tree.add(info)

    obj.console.print(tree)


@app.command()
def info(ctx: typer.Context, pkg: str):
    """Fetch information about a package."""

    obj: ContextObj = ctx.obj

    match response := assert_not_none(get_package.sync(pkg, client=obj.client)):
        case HTTPValidationError() | NotFoundErrorModel():
            print_error(response)
            raise typer.Abort()

        case Package():
            package = response

    @group()
    def get_groups():
        yield Text.assemble(
            ("Name:", "italic"),
            " ",
            (package.name, "bold"),
        )

        yield Text.assemble(
            ("Summary:", "italic"),
            " ",
            (package.summary, "bold"),
        )

        label_text = Text().append("Labeled", "italic")

        for i, label in enumerate(package.labels):
            if i == 0:
                label_text.append(" ")
            else:
                label_text.append(", ")

            label_text.append(label, "bold")

        yield label_text

        owner_text = Text().append("Owned by", "italic")

        for i, owner in enumerate(package.owners):
            if i == 0:
                owner_text.append(" ")
            else:
                owner_text.append(", ")

            owner_text.append(owner, "bold")

        yield owner_text

        if not isinstance(package.namespace, Unset) and package.namespace is not None:
            yield Text.assemble(
                ("Managed by", "italic"),
                " ",
                (package.namespace, "bold"),
            )

        yield Text.assemble(
            ("Created by", "italic"),
            " ",
            (package.created_by, "bold"),
            " ",
            ("on", "italic"),
            " ",
            (str(package.created_date), "bold"),
        )

        yield Text.assemble(
            ("Updated by", "italic"),
            " ",
            (package.updated_by, "bold"),
            " ",
            ("on", "italic"),
            " ",
            (str(package.updated_date), "bold"),
        )

        yield Text.assemble(
            ("Downloads:", "italic"),
            " ",
            (str(package.downloads), "bold"),
        )

        if package.tags:
            tag_tree = Tree("[italic]Tags:[/]")

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
                ("Text:", "bold"),
                " ",
                ("none", "italic"),
            )

        @group()
        def get_version_group(version: PackageVersion):
            yield Text.assemble(
                ("Created by", "italic"),
                " ",
                (version.created_by, "bold"),
                " ",
                ("on", "italic"),
                " ",
                (str(version.created_date), "bold"),
            )

            yield Text.assemble(
                ("Downloads:", "italic"),
                " ",
                (str(version.downloads), "bold"),
            )

            if isinstance(version.repository, str):
                yield Text.assemble(
                    ("Repository URL:", "italic"),
                    " ",
                    version.repository,
                )

            if isinstance(version.tarball, str):
                yield Text.assemble(
                    ("Download URL:", "italic"),
                    " ",
                    version.tarball,
                )

            if version.checksums:
                checksum_tree = Tree("[italic]Checksums[/]")

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
                dependency_tree = Tree("[italic]Dependencies[/]")

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
                expand=True,
                padding=(0, 2),
                collapse_padding=False,
                box=box.SQUARE,
                show_header=False,
                title="[italic]Version[/] [bold]{version}[/]".format(
                    version=escape(version.version),
                ),
            )
            grid.add_column()
            grid.add_column()

            metadata = get_version_group(version)
            description = Markdown(version.description)
            grid.add_row(
                Align(metadata, vertical="top"), Align(description, vertical="top")
            )

            yield ""
            yield grid

    obj.console.print(get_groups())
