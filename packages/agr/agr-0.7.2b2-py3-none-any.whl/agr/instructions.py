"""Instruction file detection and synchronization."""

from pathlib import Path


INSTRUCTION_FILES = ("CLAUDE.md", "AGENTS.md")


def canonical_instruction_file(tool_name: str) -> str:
    """Resolve the canonical instruction file for a tool."""
    if tool_name == "claude":
        return "CLAUDE.md"
    return "AGENTS.md"


def detect_instruction_files(repo_root: Path) -> list[str]:
    """Detect instruction files present in the repo root."""
    return [name for name in INSTRUCTION_FILES if (repo_root / name).exists()]


def sync_instruction_files(
    repo_root: Path, canonical_file: str, files: list[str]
) -> list[str]:
    """Sync instruction files to match the canonical file.

    Args:
        repo_root: Repository root path.
        canonical_file: Filename to copy from.
        files: Existing instruction filenames to update.

    Returns:
        List of filenames that were updated.
    """
    canonical_path = repo_root / canonical_file
    if not canonical_path.exists():
        return []

    canonical_content = canonical_path.read_text()
    updated: list[str] = []

    for filename in files:
        if filename == canonical_file:
            continue
        target_path = repo_root / filename
        if not target_path.exists():
            continue
        if target_path.read_text() != canonical_content:
            target_path.write_text(canonical_content)
            updated.append(filename)

    return updated
