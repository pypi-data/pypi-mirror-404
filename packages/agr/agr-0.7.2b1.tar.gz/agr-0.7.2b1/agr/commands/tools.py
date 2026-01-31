"""agr tools command implementation."""

import shutil

from rich.console import Console

from agr.config import AgrConfig, find_config, find_repo_root
from agr.exceptions import AgrError
from agr.fetcher import fetch_and_install_to_tools, is_skill_installed
from agr.handle import parse_handle
from agr.tool import DEFAULT_TOOL_NAMES, TOOLS

console = Console()


def _validate_tool_names(tool_names: list[str]) -> None:
    """Validate tool names against TOOLS registry.

    Raises:
        SystemExit: If any tool name is invalid.
    """
    invalid = [name for name in tool_names if name not in TOOLS]
    if invalid:
        available = ", ".join(TOOLS.keys())
        console.print(f"[red]Error:[/red] Unknown tool(s): {', '.join(invalid)}")
        console.print(f"[dim]Available tools: {available}[/dim]")
        raise SystemExit(1)


def run_tools_list() -> None:
    """List configured tools.

    Shows which tools are configured and which are available.
    """
    # Find config (or show defaults if no agr.toml)
    config_path = find_config()

    if config_path:
        config = AgrConfig.load(config_path)
        configured = config.tools
    else:
        # No config found, show defaults
        configured = list(DEFAULT_TOOL_NAMES)
        console.print("[dim]No agr.toml found, showing defaults[/dim]")
        console.print()

    # Get available (not configured) tools
    available = [name for name in TOOLS.keys() if name not in configured]

    # Display configured tools
    console.print("[bold]Configured tools:[/bold]")
    if configured:
        for tool_name in configured:
            console.print(f"  - {tool_name}")
    else:
        console.print("  [dim](none)[/dim]")

    # Display available tools
    if available:
        console.print()
        console.print(f"[dim]Available tools:[/dim] {', '.join(available)}")


def run_tools_add(tool_names: list[str]) -> None:
    """Add tools to configuration and sync existing dependencies.

    Args:
        tool_names: Names of tools to add
    """
    _validate_tool_names(tool_names)

    # Find or create config
    config_path = find_config()
    if config_path is None:
        console.print("[red]Error:[/red] No agr.toml found.")
        console.print("[dim]Run 'agr init' first to create one.[/dim]")
        raise SystemExit(1)

    config = AgrConfig.load(config_path)

    # Add tools (skip duplicates)
    added: list[str] = []
    skipped: list[str] = []

    for name in tool_names:
        if name in config.tools:
            skipped.append(name)
        else:
            config.tools.append(name)
            added.append(name)

    # Report what happened
    for name in added:
        console.print(f"[green]Added:[/green] {name}")
    for name in skipped:
        console.print(f"[dim]Already configured:[/dim] {name}")

    # If no tools were added or no dependencies, save and exit early
    if not added or not config.dependencies:
        config.save()
        return

    # Auto-sync: install existing dependencies to new tools
    if added and config.dependencies:
        repo_root = find_repo_root()
        if repo_root is None:
            console.print(
                "[yellow]Warning:[/yellow] Not in a git repository, "
                "cannot sync dependencies."
            )
            return

        console.print()
        console.print(
            f"[dim]Syncing {len(config.dependencies)} dependencies "
            f"to new tools...[/dim]"
        )

        new_tools = [TOOLS[name] for name in added]
        resolver = config.get_source_resolver()
        sync_errors = 0

        for dep in config.dependencies:
            try:
                # Parse handle
                if dep.is_local:
                    ref = dep.path or ""
                    source_name = None
                else:
                    ref = dep.handle or ""
                    source_name = dep.source or config.default_source

                handle = parse_handle(ref)

                # Check which new tools need installation
                tools_needing_install = [
                    tool
                    for tool in new_tools
                    if not is_skill_installed(handle, repo_root, tool, source_name)
                ]

                if not tools_needing_install:
                    continue

                # Install to new tools
                fetch_and_install_to_tools(
                    handle,
                    repo_root,
                    tools_needing_install,
                    overwrite=False,
                    resolver=resolver,
                    source=source_name,
                )

                tool_list = ", ".join(t.name for t in tools_needing_install)
                console.print(
                    f"[green]Installed:[/green] {dep.identifier} ({tool_list})"
                )

            except AgrError as e:
                console.print(f"[red]Error:[/red] {dep.identifier}: {e}")
                sync_errors += 1
            except Exception as e:
                console.print(f"[red]Error:[/red] {dep.identifier}: {e}")
                sync_errors += 1

        # Save config after successful sync
        config.save()

        if sync_errors:
            console.print(
                f"[yellow]Warning:[/yellow] {sync_errors} dependency sync(s) failed"
            )
            raise SystemExit(1)


def run_tools_remove(tool_names: list[str]) -> None:
    """Remove tools from configuration and delete installed skills.

    Args:
        tool_names: Names of tools to remove
    """
    _validate_tool_names(tool_names)

    # Find config
    config_path = find_config()
    if config_path is None:
        console.print("[red]Error:[/red] No agr.toml found.")
        raise SystemExit(1)

    config = AgrConfig.load(config_path)

    # Check if removing would leave no tools
    remaining = [t for t in config.tools if t not in tool_names]
    if not remaining:
        console.print("[red]Error:[/red] Cannot remove all tools.")
        console.print("[dim]At least one tool must be configured.[/dim]")
        raise SystemExit(1)

    # Find repo root for skill cleanup
    repo_root = find_repo_root()

    # Remove tools and delete their skills
    removed: list[str] = []
    not_configured: list[str] = []

    for name in tool_names:
        if name not in config.tools:
            not_configured.append(name)
            continue

        console.print(f"[yellow]Removing:[/yellow] {name}")

        # Delete all skills from this tool's directory
        if repo_root:
            tool_config = TOOLS[name]
            skills_dir = tool_config.get_skills_dir(repo_root)
            if skills_dir.exists():
                skill_count = sum(1 for _ in skills_dir.iterdir() if _.is_dir())
                try:
                    shutil.rmtree(skills_dir)
                    console.print(
                        f"[dim]Deleted {skill_count} skills from {skills_dir.relative_to(repo_root)}/[/dim]"
                    )
                except OSError as e:
                    console.print(f"[red]Error deleting skills:[/red] {e}")
                    console.print(f"[dim]Tool '{name}' not removed from config[/dim]")
                    continue  # Skip this tool, don't remove from config

        config.tools.remove(name)
        removed.append(name)

    # Save config
    config.save()

    # Report
    for name in removed:
        console.print(f"[green]Removed:[/green] {name}")
    for name in not_configured:
        console.print(f"[dim]Not configured:[/dim] {name}")
