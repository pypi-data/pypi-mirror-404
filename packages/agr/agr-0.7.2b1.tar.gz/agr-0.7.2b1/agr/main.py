"""CLI entry point for agr."""

from typing import Annotated, Optional

import typer

from agr import __version__
from agr.commands.add import run_add
from agr.commands.init import run_init
from agr.commands.list import run_list
from agr.commands.remove import run_remove
from agr.commands.sync import run_sync
from agr.commands.tools import run_tools_add, run_tools_list, run_tools_remove

app = typer.Typer(
    name="agr",
    help="Agent Resources - Install and manage agent skills.",
    no_args_is_help=True,
    add_completion=False,
)

# Tools sub-app
tools_app = typer.Typer(
    name="tools",
    help="Manage configured tools.",
    no_args_is_help=False,  # Default to list
)
app.add_typer(tools_app, name="tools")


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        print(f"agr {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            "-v",
            help="Show version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
) -> None:
    """Agent Resources - Install and manage agent skills."""
    pass


# Tools subcommand group
@tools_app.callback(invoke_without_command=True)
def tools_default(ctx: typer.Context) -> None:
    """List configured tools (default behavior)."""
    if ctx.invoked_subcommand is None:
        run_tools_list()


@tools_app.command("list")
def tools_list() -> None:
    """List configured tools."""
    run_tools_list()


@tools_app.command("add")
def tools_add(
    names: Annotated[
        list[str],
        typer.Argument(help="Tool names to add."),
    ],
) -> None:
    """Add tools and sync existing dependencies to them."""
    run_tools_add(names)


@tools_app.command("remove")
def tools_remove(
    names: Annotated[
        list[str],
        typer.Argument(help="Tool names to remove."),
    ],
) -> None:
    """Remove tools and delete their installed skills."""
    run_tools_remove(names)


@app.command()
def init(
    skill_name: Annotated[
        Optional[str],
        typer.Argument(
            help="Name for a new skill scaffold. If omitted, creates agr.toml.",
        ),
    ] = None,
) -> None:
    """Initialize agr.toml or create a skill scaffold.

    Without arguments: Creates agr.toml in current directory.
    With skill name: Creates a skill scaffold directory.

    Examples:
        agr init           # Create agr.toml
        agr init my-skill  # Create my-skill/SKILL.md scaffold
    """
    run_init(skill_name)


@app.command()
def add(
    refs: Annotated[
        list[str],
        typer.Argument(
            help="Skill handles (user/skill) or local paths (./path) to add.",
        ),
    ],
    overwrite: Annotated[
        bool,
        typer.Option(
            "--overwrite",
            "-o",
            help="Overwrite existing skills.",
        ),
    ] = False,
    source: Annotated[
        Optional[str],
        typer.Option(
            "--source",
            "-s",
            help="Source name to use for this install.",
        ),
    ] = None,
) -> None:
    """Add skills from GitHub or local paths.

    Examples:
        agr add kasperjunge/commit
        agr add maragudk/skills/collaboration
        agr add ./my-skill
        agr add kasperjunge/commit kasperjunge/pr  # Multiple
    """
    run_add(refs, overwrite, source)


@app.command()
def remove(
    refs: Annotated[
        list[str],
        typer.Argument(
            help="Skill handles or paths to remove.",
        ),
    ],
) -> None:
    """Remove skills from the project.

    Examples:
        agr remove kasperjunge/commit
        agr remove ./my-skill
    """
    run_remove(refs)


@app.command()
def sync() -> None:
    """Install all skills from agr.toml.

    Installs any dependencies that aren't already installed.
    """
    run_sync()


@app.command(name="list")
def list_cmd() -> None:
    """List all skills and their status.

    Shows all dependencies from agr.toml and whether they're installed.
    """
    run_list()


if __name__ == "__main__":
    app()
