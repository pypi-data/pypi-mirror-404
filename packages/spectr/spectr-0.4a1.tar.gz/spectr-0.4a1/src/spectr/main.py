import os
import sys
from importlib.metadata import version
from pathlib import Path
from typing import Annotated

import toml
import typer
from qass.tools.analyzer.buffer_metadata_cache import (
    Buffer,
    BufferMetadataCache,
)
from rich.console import Console

from spectr.app import Spectr
from spectr.config import Config

app = typer.Typer()


def version_callback(value: bool):
    if value:
        print(f"{version('spectr')}")
        raise typer.Exit()


def get_db_url(config: Config, path: Path) -> str:
    if config.metadata_cache.persist_cache:
        return f"sqlite:///{path.resolve() / '.metadata.db'}"
    return "sqlite:///:memory:"


@app.command()
def main(
    path: Annotated[
        Path | None, typer.Option(help="Root Path for file synchronization")
    ] = None,
    glob_pattern: Annotated[
        str,
        typer.Option(
            help="Pattern forwarded to Path.glob for initial file candidate retrieval"
        ),
    ] = "*p*c?b*",
    regex_pattern: Annotated[
        str,
        typer.Option(
            help="Pattern used to further validate file candidates before they are loaded"
        ),
    ] = "^.*[p][0-9]*[c][0-9]{1}[b][0-9]{2}",
    version: Annotated[  # noqa
        bool | None,
        typer.Option("--version", callback=version_callback, is_eager=True),
    ] = None,
    persist: Annotated[
        bool | None,
        typer.Option(
            help=(
                "Persist the cache in a locally created '.metadata.db' file.\n"
                "Overwrites 'persist_cache' in the config file."
            )
        ),
    ] = None,
) -> None:
    path = path or Path.cwd()
    assert path.exists()

    # TODO: This whole handling section here needs refactoring
    err_console = Console(stderr=True)
    match sys.platform:
        case "linux":
            config_base_path = Path.home() / ".config"
        case "win32":
            config_base_path = os.getenv("%LOCALAPPDATA%")
            err_console.print("Unable to retrieve config base path for windows")
        case "darwin":
            config_base_path = Path.home() / ".config"
        case _:
            err_console.print("Unknown operating system")
            raise typer.Exit()

    try:
        config_path = config_base_path / "spectr" / "config.toml"
        if not config_path.parent.exists():
            config_path.parent.mkdir(parents=True)
        if not config_path.exists():
            config_path.open("w").write(toml.dumps(Config().model_dump()))
    except PermissionError:
        err_console.print(
            "Insufficient permission for config folder.\nUsing default config"
        )
    except Exception:
        err_console.print("Error during config file creation.\nUsing default config")

    try:
        config_content = toml.load(config_path) if config_path.exists() else {}
    except Exception:
        config_content = {}

    config = Config(**config_content)
    if persist is not None:
        config.metadata_cache.persist_cache = persist

    cache = BufferMetadataCache(db_url=get_db_url(config, path), Buffer_cls=Buffer)
    cache.synchronize_directory(
        path.resolve(), glob_pattern=glob_pattern, regex_pattern=regex_pattern
    )

    app = Spectr(cache, config)
    app.run()
