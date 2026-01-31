"""agr sync command implementation."""

from pathlib import Path

from rich.console import Console

from agr.config import AgrConfig, find_config, find_repo_root
from agr.exceptions import AgrError
from agr.fetcher import fetch_and_install_to_tools, is_skill_installed
from agr.handle import (
    INSTALLED_NAME_SEPARATOR,
    LEGACY_SEPARATOR,
    ParsedHandle,
    parse_handle,
)
from agr.metadata import build_handle_id, read_skill_metadata, write_skill_metadata
from agr.source import DEFAULT_SOURCE_NAME
from agr.skill import SKILL_MARKER, is_valid_skill_dir, update_skill_md_name
from agr.tool import ToolConfig

console = Console()


def _migrate_legacy_directories(skills_dir: Path, tool: ToolConfig) -> None:
    """Migrate colon-based directory names to the new separator format.

    This ensures backward compatibility with skills installed before
    the Windows-compatible naming scheme was introduced.

    Only applies to flat tools (Claude), not nested tools (Cursor).

    Args:
        skills_dir: The skills directory to scan for legacy directories.
        tool: Tool configuration (migration only for non-nested tools).
    """
    # Only migrate for flat tools
    if tool.supports_nested:
        return

    if not skills_dir.exists():
        return

    for skill_dir in skills_dir.iterdir():
        if not skill_dir.is_dir():
            continue
        if LEGACY_SEPARATOR not in skill_dir.name:
            continue
        # Verify it's a skill (has SKILL.md)
        if not (skill_dir / SKILL_MARKER).exists():
            continue

        # Convert legacy separator to new separator
        new_name = skill_dir.name.replace(LEGACY_SEPARATOR, INSTALLED_NAME_SEPARATOR)
        new_path = skills_dir / new_name

        if new_path.exists():
            console.print(f"[yellow]Cannot migrate:[/yellow] {skill_dir.name}")
            console.print(f"  [dim]Target {new_name} already exists[/dim]")
            continue

        try:
            skill_dir.rename(new_path)
            console.print(f"[blue]Migrated:[/blue] {skill_dir.name} -> {new_name}")
        except OSError as e:
            console.print(f"[red]Failed to migrate:[/red] {skill_dir.name}")
            console.print(f"  [dim]{e}[/dim]")


def _migrate_flat_installed_names(
    skills_dir: Path,
    tool: ToolConfig,
    config: AgrConfig,
    repo_root: Path,
) -> None:
    """Migrate flat skill names to the plain <skill> format when safe.

    Only applies to flat tools. Uses agr.toml dependencies to resolve
    handle identities and writes metadata for accurate future matching.
    """
    # TODO(decide): consider best-effort migration for installs not in agr.toml.
    # This is ambiguous for local skills because the original path is unknown,
    # and for remotes because multiple handles can share the same skill name.
    if tool.supports_nested:
        return

    if not skills_dir.exists():
        return

    # Build handles from config dependencies
    handles_by_name: dict[str, list[tuple[ParsedHandle, str | None]]] = {}
    for dep in config.dependencies:
        ref = dep.path or dep.handle or ""
        if not ref:
            continue
        try:
            if dep.is_local:
                path = Path(ref)
                handle = ParsedHandle(is_local=True, name=path.name, local_path=path)
                source_name = None
            else:
                handle = parse_handle(ref)
                source_name = dep.source or config.default_source
        except Exception:
            continue
        handles_by_name.setdefault(handle.name, []).append((handle, source_name))

    for skill_name, handles in handles_by_name.items():
        name_dir = skills_dir / skill_name
        name_dir_is_skill = is_valid_skill_dir(name_dir)

        # If a name dir exists, try to match metadata to a handle
        matched_handle: tuple[ParsedHandle, str | None] | None = None
        if name_dir_is_skill:
            meta = read_skill_metadata(name_dir)
            if meta:
                for handle, source_name in handles:
                    handle_id = build_handle_id(handle, repo_root, source_name)
                    legacy_id = (
                        build_handle_id(handle, repo_root)
                        if source_name == DEFAULT_SOURCE_NAME
                        else None
                    )
                    if meta.get("id") in {handle_id, legacy_id}:
                        matched_handle = (handle, source_name)
                        break

        # If there is only one handle for this name, ensure name dir metadata
        if len(handles) == 1:
            handle, source_name = handles[0]
            handle_id = build_handle_id(handle, repo_root, source_name)
            if name_dir_is_skill:
                meta = read_skill_metadata(name_dir)
                if not meta or meta.get("id") != handle_id:
                    update_skill_md_name(name_dir, name_dir.name)
                    write_skill_metadata(
                        name_dir,
                        handle,
                        repo_root,
                        tool.name,
                        name_dir.name,
                        source_name,
                    )
                continue

            # No name dir: try to migrate from full flat name
            full_dir = skills_dir / handle.to_installed_name()
            if is_valid_skill_dir(full_dir):
                if not name_dir.exists():
                    try:
                        full_dir.rename(name_dir)
                        update_skill_md_name(name_dir, name_dir.name)
                        write_skill_metadata(
                            name_dir,
                            handle,
                            repo_root,
                            tool.name,
                            name_dir.name,
                            source_name,
                        )
                        console.print(
                            f"[blue]Migrated:[/blue] {full_dir.name} -> {name_dir.name}"
                        )
                    except OSError as e:
                        console.print(f"[red]Failed to migrate:[/red] {full_dir.name}")
                        console.print(f"  [dim]{e}[/dim]")
                else:
                    # Name exists but isn't a skill dir; skip rename
                    pass
            continue

        # Multiple handles with same name: avoid renaming to plain name
        if matched_handle:
            update_skill_md_name(name_dir, name_dir.name)
            write_skill_metadata(
                name_dir,
                matched_handle[0],
                repo_root,
                tool.name,
                name_dir.name,
                matched_handle[1],
            )

        # Ensure metadata on full-name dirs for all handles
        for handle, source_name in handles:
            full_dir = skills_dir / handle.to_installed_name()
            if is_valid_skill_dir(full_dir):
                update_skill_md_name(full_dir, full_dir.name)
                write_skill_metadata(
                    full_dir,
                    handle,
                    repo_root,
                    tool.name,
                    full_dir.name,
                    source_name,
                )


def run_sync() -> None:
    """Run the sync command.

    Installs all dependencies from agr.toml that aren't already installed.
    Also migrates any legacy colon-based directory names to the new
    Windows-compatible double-hyphen format (for flat tools only).
    """
    # Find repo root
    repo_root = find_repo_root()
    if repo_root is None:
        console.print("[red]Error:[/red] Not in a git repository")
        raise SystemExit(1)

    # Find config
    config_path = find_config()
    if config_path is None:
        console.print("[yellow]No agr.toml found.[/yellow] Nothing to sync.")
        return

    config = AgrConfig.load(config_path)

    # Get configured tools
    tools = config.get_tools()

    # Migrate legacy colon-based directories for flat tools
    for tool in tools:
        skills_dir = tool.get_skills_dir(repo_root)
        _migrate_legacy_directories(skills_dir, tool)
        _migrate_flat_installed_names(skills_dir, tool, config, repo_root)

    if not config.dependencies:
        console.print("[yellow]No dependencies in agr.toml.[/yellow] Nothing to sync.")
        return

    resolver = config.get_source_resolver()

    # Track results per dependency (not per tool)
    results: list[tuple[str, str, str | None]] = []  # (identifier, status, error)

    for dep in config.dependencies:
        identifier = dep.identifier

        try:
            # Parse handle
            if dep.is_local:
                ref = dep.path or ""
            else:
                ref = dep.handle or ""

            handle = parse_handle(ref)
            if dep.is_local:
                source_name = None
            else:
                source_name = dep.source or config.default_source

            # Check if already installed in all tools
            all_installed = all(
                is_skill_installed(handle, repo_root, tool, source_name)
                for tool in tools
            )

            if all_installed:
                results.append((identifier, "up-to-date", None))
                continue

            # Get tools that need installation
            tools_needing_install = [
                tool
                for tool in tools
                if not is_skill_installed(handle, repo_root, tool, source_name)
            ]

            # Install to all tools that need it (downloads once)
            fetch_and_install_to_tools(
                handle,
                repo_root,
                tools_needing_install,
                overwrite=False,
                resolver=resolver,
                source=source_name,
            )

            results.append((identifier, "installed", None))

        except FileExistsError as e:
            results.append((identifier, "error", str(e)))
        except AgrError as e:
            results.append((identifier, "error", str(e)))
        except Exception as e:
            results.append((identifier, "error", f"Unexpected: {e}"))

    # Print results
    installed = 0
    up_to_date = 0
    errors = 0

    for identifier, status, error in results:
        if status == "installed":
            console.print(f"[green]Installed:[/green] {identifier}")
            installed += 1
        elif status == "up-to-date":
            console.print(f"[dim]Up to date:[/dim] {identifier}")
            up_to_date += 1
        else:
            console.print(f"[red]Error:[/red] {identifier}")
            if error:
                console.print(f"  [dim]{error}[/dim]")
            errors += 1

    # Summary
    console.print()
    parts = []
    if installed:
        parts.append(f"{installed} installed")
    if up_to_date:
        parts.append(f"{up_to_date} up to date")
    if errors:
        parts.append(f"{errors} failed")

    console.print(f"[bold]Summary:[/bold] {', '.join(parts)}")

    if errors:
        raise SystemExit(1)
