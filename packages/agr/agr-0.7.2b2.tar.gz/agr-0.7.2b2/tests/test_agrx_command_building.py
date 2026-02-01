"""Tests for agrx command construction."""

from agr.tool import CLAUDE, CODEX, COPILOT, CURSOR
from agrx.main import _build_skill_command


def test_build_skill_command_non_interactive_codex_exec():
    """Codex non-interactive uses exec subcommand with positional prompt."""
    cmd = _build_skill_command(CODEX, "$skill prompt", non_interactive=True)
    assert cmd == ["codex", "exec", "$skill prompt"]


def test_build_skill_command_interactive_claude_positional():
    """Claude interactive uses positional prompt."""
    cmd = _build_skill_command(CLAUDE, "/skill prompt", non_interactive=False)
    assert cmd == ["claude", "/skill prompt"]


def test_build_skill_command_interactive_copilot_flag():
    """Copilot interactive uses -i prompt flag."""
    cmd = _build_skill_command(COPILOT, "/skill prompt", non_interactive=False)
    assert cmd == ["copilot", "-i", "/skill prompt"]


def test_build_skill_command_non_interactive_cursor_flag():
    """Cursor non-interactive uses -p prompt flag."""
    cmd = _build_skill_command(CURSOR, "/skill prompt", non_interactive=True)
    assert cmd == ["agent", "-p", "/skill prompt"]
