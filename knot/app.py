from pathlib import Path
import typer


APP_NAME = "knot"

app = typer.Typer(name=APP_NAME)


def get_app_dir() -> Path:
    path = Path(typer.get_app_dir(APP_NAME))

    if path.is_dir():
        return path

    if not path.exists():
        path.mkdir(parents=True)

        return path

    raise OSError(f"The configuration path {path} is not a directory")
