"""agr add command implementation."""

from rich.console import Console

from agr.config import AgrConfig, Dependency, find_config, find_repo_root
from agr.exceptions import AgrError, InvalidHandleError
from agr.fetcher import fetch_and_install_to_tools
from agr.handle import parse_handle

console = Console()


def run_add(
    refs: list[str], overwrite: bool = False, source: str | None = None
) -> None:
    """Run the add command.

    Args:
        refs: List of handles or paths to add
        overwrite: Whether to overwrite existing skills
    """
    # Find repo root
    repo_root = find_repo_root()
    if repo_root is None:
        console.print("[red]Error:[/red] Not in a git repository")
        raise SystemExit(1)

    # Find or create config
    config_path = find_config()
    if config_path is None:
        config_path = repo_root / "agr.toml"
        config = AgrConfig()
    else:
        config = AgrConfig.load(config_path)

    # Get configured tools
    tools = config.get_tools()
    resolver = config.get_source_resolver()

    # Track results for summary
    results: list[tuple[str, bool, str]] = []  # (ref, success, message)

    for ref in refs:
        try:
            # Parse handle
            handle = parse_handle(ref)

            if source and handle.is_local:
                raise AgrError("Local skills cannot specify a source")

            # Validate explicit source if provided
            if source:
                resolver.get(source)

            # Install the skill to all configured tools (downloads once)
            installed_paths_dict = fetch_and_install_to_tools(
                handle,
                repo_root,
                tools,
                overwrite,
                resolver=resolver,
                source=source,
            )
            installed_paths = [
                f"{name}: {path}" for name, path in installed_paths_dict.items()
            ]

            # Add to config
            if handle.is_local:
                config.add_dependency(
                    Dependency(
                        type="skill",
                        path=ref,
                    )
                )
            else:
                config.add_dependency(
                    Dependency(
                        type="skill",
                        handle=handle.to_toml_handle(),
                        source=source,
                    )
                )

            results.append((ref, True, ", ".join(installed_paths)))

        except InvalidHandleError as e:
            results.append((ref, False, str(e)))
        except FileExistsError as e:
            results.append((ref, False, str(e)))
        except AgrError as e:
            results.append((ref, False, str(e)))
        except Exception as e:
            results.append((ref, False, f"Unexpected error: {e}"))

    # Save config if any successes
    successes = [r for r in results if r[1]]
    if successes:
        config.save(config_path)

    # Print results
    for ref, success, message in results:
        if success:
            console.print(f"[green]Added:[/green] {ref}")
            console.print(f"  [dim]Installed to {message}[/dim]")
        else:
            console.print(f"[red]Failed:[/red] {ref}")
            console.print(f"  [dim]{message}[/dim]")

    # Summary
    if len(refs) > 1:
        console.print()
        console.print(
            f"[bold]Summary:[/bold] {len(successes)}/{len(refs)} skills added"
        )

    # Exit with error if any failures
    failures = [r for r in results if not r[1]]
    if failures:
        raise SystemExit(1)
