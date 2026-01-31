"""CLI entry point for agrx - temporary skill runner."""

import shutil
import signal
import subprocess
import sys
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

from agr.config import AgrConfig, find_config, find_repo_root
from agr.exceptions import (
    AgrError,
    InvalidHandleError,
    RepoNotFoundError,
    SkillNotFoundError,
)
from agr.fetcher import downloaded_repo, install_skill_from_repo
from agr.handle import ParsedHandle, parse_handle
from agr.skill import find_skill_in_repo
from agr.tool import DEFAULT_TOOL_NAMES, TOOLS, ToolConfig, get_tool

app = typer.Typer(
    name="agrx",
    help="Run a skill temporarily without adding to agr.toml.",
    no_args_is_help=True,
    add_completion=False,
)

console = Console()

AGRX_PREFIX = "_agrx_"  # Prefix for temporary resources


def _get_default_tool() -> str:
    """Get default tool from agr.toml or fall back to default."""
    config_path = find_config()
    if config_path:
        config = AgrConfig.load(config_path)
        if config.tools:
            return config.tools[0]
    return DEFAULT_TOOL_NAMES[0]


def _check_tool_cli(tool_config: ToolConfig) -> None:
    """Check if tool's CLI is installed.

    Args:
        tool_config: ToolConfig for the tool to check

    Raises:
        typer.Exit: If CLI is not found
    """
    cli_cmd = tool_config.cli_command
    if not cli_cmd:
        console.print(
            f"[red]Error:[/red] {tool_config.name} has no CLI command configured"
        )
        raise typer.Exit(1)
    if shutil.which(cli_cmd) is None:
        console.print(f"[red]Error:[/red] {cli_cmd} CLI not found.")
        if tool_config.install_hint:
            console.print(f"[dim]{tool_config.install_hint}[/dim]")
        raise typer.Exit(1)


def _cleanup_skill(skill_path: Path) -> None:
    """Clean up a temporary skill."""
    if skill_path.exists():
        try:
            shutil.rmtree(skill_path)
        except Exception:
            pass  # Best effort cleanup


def _build_skill_command(
    tool_config: ToolConfig,
    skill_prompt: str,
    *,
    non_interactive: bool,
) -> list[str]:
    """Build the command to run a skill with the selected tool."""
    if non_interactive and tool_config.cli_exec_command:
        cmd = list(tool_config.cli_exec_command)
    else:
        assert tool_config.cli_command is not None
        cmd = [tool_config.cli_command]
    if not non_interactive and tool_config.cli_interactive_prompt_flag:
        cmd.extend([tool_config.cli_interactive_prompt_flag, skill_prompt])
    elif not non_interactive and tool_config.cli_interactive_prompt_positional:
        cmd.append(skill_prompt)
    elif tool_config.cli_prompt_flag:
        cmd.extend([tool_config.cli_prompt_flag, skill_prompt])
    else:
        cmd.append(skill_prompt)
    return cmd


@app.command()
def main(
    handle: Annotated[
        str,
        typer.Argument(
            help="Skill handle to run (e.g., kasperjunge/commit).",
        ),
    ],
    tool: Annotated[
        Optional[str],
        typer.Option(
            "--tool",
            "-t",
            help="Tool CLI to use (claude, cursor, codex, copilot).",
        ),
    ] = None,
    interactive: Annotated[
        bool,
        typer.Option(
            "--interactive",
            "-i",
            help="Start interactive session after running the skill.",
        ),
    ] = False,
    prompt: Annotated[
        Optional[str],
        typer.Option(
            "--prompt",
            "-p",
            help="Prompt to pass to the skill.",
        ),
    ] = None,
    source: Annotated[
        Optional[str],
        typer.Option(
            "--source",
            "-s",
            help="Source name to use for this run.",
        ),
    ] = None,
    global_install: Annotated[
        bool,
        typer.Option(
            "--global",
            "-g",
            help="Install to global skills directory instead of project-local.",
        ),
    ] = False,
) -> None:
    """Run a skill temporarily without adding to agr.toml.

    Downloads and installs the skill to a temporary location, runs it with the
    selected tool's CLI, and cleans up afterwards.

    Examples:
        agrx kasperjunge/commit
        agrx maragudk/skills/collaboration -i
        agrx kasperjunge/commit -p "Review my changes"
        agrx kasperjunge/commit --tool cursor
        agrx kasperjunge/commit --tool codex
    """
    # Determine which tool to use
    tool_name = tool or _get_default_tool()

    # Validate tool name
    if tool_name not in TOOLS:
        available = ", ".join(TOOLS.keys())
        console.print(f"[red]Error:[/red] Unknown tool '{tool_name}'")
        console.print(f"[dim]Available tools: {available}[/dim]")
        raise typer.Exit(1)

    tool_config = get_tool(tool_name)

    # Find repo root (or use global dir)
    repo_root: Path | None = None
    if global_install:
        skills_dir = tool_config.get_global_skills_dir()
    else:
        repo_root = find_repo_root()
        if repo_root is None:
            console.print("[red]Error:[/red] Not in a git repository")
            console.print(
                f"[dim]Use --global to install to {tool_config.get_global_skills_dir()}[/dim]"
            )
            raise typer.Exit(1)
        skills_dir = tool_config.get_skills_dir(repo_root)

    try:
        # Parse handle
        parsed = parse_handle(handle)

        if parsed.is_local:
            console.print("[red]Error:[/red] agrx only works with remote handles")
            console.print("[dim]Use 'agr add' for local skills[/dim]")
            raise typer.Exit(1)

        config_path = find_config()
        config = AgrConfig.load(config_path) if config_path else AgrConfig()
        resolver = config.get_source_resolver()
        if source:
            resolver.get(source)

        # Check tool CLI is available
        _check_tool_cli(tool_config)

        console.print(f"[dim]Downloading {handle}...[/dim]")

        # Create prefixed name for temporary skill
        prefixed_name = f"{AGRX_PREFIX}{parsed.name}"

        # Download and install
        owner, repo_name = parsed.get_github_repo()
        installed_path = None
        for source_config in resolver.ordered(source):
            try:
                with downloaded_repo(source_config, owner, repo_name) as repo_dir:
                    if find_skill_in_repo(repo_dir, parsed.name) is None:
                        continue
                    # Create a modified handle for the prefixed installation
                    temp_handle = ParsedHandle(
                        username=parsed.username,
                        repo=parsed.repo,
                        name=prefixed_name,
                    )

                    installed_path = install_skill_from_repo(
                        repo_dir,
                        parsed.name,
                        temp_handle,
                        skills_dir,
                        tool_config,
                        repo_root,
                        overwrite=True,
                        install_source=source_config.name,
                    )
                    break
            except RepoNotFoundError:
                if source is not None:
                    raise
                continue

        if installed_path is None:
            raise SkillNotFoundError(
                f"Skill '{parsed.name}' not found in sources: "
                f"{', '.join(s.name for s in resolver.ordered(source))}"
            )

        # For consistency, update temp_skill_path to match
        temp_skill_path = installed_path

        # Set up cleanup handlers
        cleanup_done = False

        def cleanup_handler(signum, frame):
            nonlocal cleanup_done
            if not cleanup_done:
                cleanup_done = True
                _cleanup_skill(temp_skill_path)
            sys.exit(1)

        original_sigint = signal.signal(signal.SIGINT, cleanup_handler)
        original_sigterm = signal.signal(signal.SIGTERM, cleanup_handler)

        try:
            console.print(
                f"[dim]Running skill '{parsed.name}' with {tool_name}...[/dim]"
            )

            # Build the skill prompt from the actual installed location
            if tool_config.supports_nested:
                relative_skill = temp_skill_path.relative_to(skills_dir)
                skill_prompt = (
                    f"{tool_config.skill_prompt_prefix}{relative_skill.as_posix()}"
                )
            else:
                skill_prompt = (
                    f"{tool_config.skill_prompt_prefix}{temp_skill_path.name}"
                )
            if prompt:
                skill_prompt += f" {prompt}"

            # Run the appropriate CLI
            if interactive:
                # Run the skill in interactive mode
                cmd = _build_skill_command(
                    tool_config,
                    skill_prompt,
                    non_interactive=False,
                )
                if tool_config.cli_force_flag:
                    cmd.append(tool_config.cli_force_flag)
                subprocess.run(cmd, check=False)
            else:
                # Just run the skill
                cmd = _build_skill_command(
                    tool_config,
                    skill_prompt,
                    non_interactive=True,
                )
                if tool_config.suppress_stderr_non_interactive:
                    result = subprocess.run(
                        cmd,
                        check=False,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                    if result.returncode != 0 and result.stderr:
                        sys.stderr.write(result.stderr)
                else:
                    subprocess.run(cmd, check=False)

        finally:
            # Restore signal handlers
            signal.signal(signal.SIGINT, original_sigint)
            signal.signal(signal.SIGTERM, original_sigterm)

            # Clean up
            if not cleanup_done:
                cleanup_done = True
                _cleanup_skill(temp_skill_path)

    except InvalidHandleError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except AgrError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
