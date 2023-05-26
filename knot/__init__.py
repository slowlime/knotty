#!/usr/bin/env python

from typing import Annotated, Optional

from knotty_client.api.default import get_packages
from rich.tree import Tree
from rich.text import Text
from rich.style import Style
import typer

from knot.app import app
from knot.ctx import ContextObj
from knot.util import assert_not_none


@app.command()
def list(ctx: typer.Context, query: Annotated[Optional[str], typer.Argument()] = None):
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
            info.append("managed by ", Style(italic=True)) \
                .append(package.namespace, Style(bold=True)) \
                .append("\t")

        info.append(str(package.downloads), Style(bold=True)) \
            .append(" downloads", Style(italic=True)) \
            .append("\t")

        info.append("last updated on ", Style(italic=True)) \
            .append(str(package.updated_date), Style(bold=True))

        if package.labels:
            info.append("\n") \
                .append("labeled ", Style(italic=True))

            for i, label in enumerate(package.labels):
                if i > 0:
                    info.append(", ")

                info.append(label, Style(bold=True))

        tree.add(info)

    obj.console.print(tree)


if __name__ == "__main__":
    app()
