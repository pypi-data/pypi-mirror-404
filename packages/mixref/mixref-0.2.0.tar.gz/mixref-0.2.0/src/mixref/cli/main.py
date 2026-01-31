"""Main CLI entry point for mixref."""

import typer
from rich.console import Console

from mixref import __version__
from mixref.cli.analyze import analyze_command

app = typer.Typer(
    name="mixref",
    help="CLI Audio Analyzer for Music Producers - DnB, Techno, House",
    add_completion=False,
)
console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"mixref version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """
    mixref - Audio analysis for producers who know what they want.

    Sharp, opinionated insights for electronic music production.
    """
    pass


# Register commands
app.command(name="analyze")(analyze_command)


if __name__ == "__main__":
    app()
