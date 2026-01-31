"""Symlink tech to klayout."""

import os
import pathlib
import shutil
import sys

import typer

from hhi import __version__

app = typer.Typer()


def remove_path_or_dir(dest: pathlib.Path):
    """Remove path or directory."""
    if dest.is_dir():
        dest.unlink()
    else:
        dest.unlink()


def make_link(src, dest, overwrite: bool = True) -> None:
    """Make a link from src to dest."""
    dest = pathlib.Path(dest)
    if dest.exists() and not overwrite:
        print(f"{dest} already exists")
        return
    if dest.exists() or dest.is_symlink():
        print(f"removing {dest} already installed")
        remove_path_or_dir(dest)
    try:
        os.symlink(src, dest, target_is_directory=True)
    except OSError:
        shutil.copytree(src, dest)
    print("link made:")
    print(f"From: {src}")
    print(f"To:   {dest}")


@app.command()
def install() -> None:
    """Install tech to klayout."""
    klayout_folder = "KLayout" if sys.platform == "win32" else ".klayout"
    cwd = pathlib.Path(__file__).resolve().parent
    home = pathlib.Path.home()
    src = cwd / "klayout"
    dest_folder = home / klayout_folder / "tech"
    dest_folder.mkdir(exist_ok=True, parents=True)
    dest = dest_folder / "hhi"
    make_link(src=src, dest=dest)


@app.command()
def version() -> None:
    """Print version."""
    print(__version__)


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1:  # No arguments provided
        sys.argv.append("--help")
    app()
