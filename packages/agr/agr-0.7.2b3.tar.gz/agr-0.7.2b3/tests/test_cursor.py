"""Tests for Cursor support with nested directory structures."""

from pathlib import Path

import pytest

from agr.config import AgrConfig
from agr.fetcher import (
    fetch_and_install,
    get_installed_skills,
    install_local_skill,
    is_skill_installed,
    uninstall_skill,
)
from agr.handle import ParsedHandle
from agr.skill import SKILL_MARKER
from agr.tool import CLAUDE, CURSOR, get_tool


class TestToolConfig:
    """Tests for tool configuration."""

    def test_claude_is_flat(self):
        """Claude uses flat directory structure."""
        assert not CLAUDE.supports_nested

    def test_cursor_is_nested(self):
        """Cursor uses nested directory structure."""
        assert CURSOR.supports_nested

    def test_get_tool_claude(self):
        """Get Claude tool config by name."""
        tool = get_tool("claude")
        assert tool == CLAUDE

    def test_get_tool_cursor(self):
        """Get Cursor tool config by name."""
        tool = get_tool("cursor")
        assert tool == CURSOR

    def test_get_tool_unknown_raises(self):
        """Getting unknown tool raises."""
        from agr.exceptions import AgrError

        with pytest.raises(AgrError, match="Unknown tool"):
            get_tool("unknown")


class TestNestedPaths:
    """Tests for nested path generation."""

    def test_remote_skill_flat_path(self):
        """Remote skill gets flat path for Claude."""
        h = ParsedHandle(username="maragudk", repo="skills", name="collab")
        assert h.to_skill_path(CLAUDE) == Path("collab")

    def test_remote_skill_nested_path(self):
        """Remote skill gets nested path for Cursor."""
        h = ParsedHandle(username="maragudk", repo="skills", name="collab")
        assert h.to_skill_path(CURSOR) == Path("maragudk/skills/collab")

    def test_remote_skill_no_repo_flat(self):
        """Remote skill without repo gets flat path for Claude."""
        h = ParsedHandle(username="kasperjunge", name="commit")
        assert h.to_skill_path(CLAUDE) == Path("commit")

    def test_remote_skill_no_repo_nested(self):
        """Remote skill without repo gets nested path for Cursor."""
        h = ParsedHandle(username="kasperjunge", name="commit")
        assert h.to_skill_path(CURSOR) == Path("kasperjunge/commit")

    def test_local_skill_flat_path(self):
        """Local skill gets flat path for Claude."""
        h = ParsedHandle(is_local=True, name="my-skill")
        assert h.to_skill_path(CLAUDE) == Path("my-skill")

    def test_local_skill_nested_path(self):
        """Local skill gets nested path for Cursor."""
        h = ParsedHandle(is_local=True, name="my-skill")
        assert h.to_skill_path(CURSOR) == Path("local/my-skill")


class TestSkillNameForTool:
    """Tests for SKILL.md name field based on tool."""

    def test_skill_name_flat(self):
        """Flat tools default to the skill name."""
        h = ParsedHandle(username="maragudk", repo="skills", name="collab")
        assert h.get_skill_name_for_tool(CLAUDE) == "collab"

    def test_skill_name_nested(self):
        """Nested tools get just the skill name."""
        h = ParsedHandle(username="maragudk", repo="skills", name="collab")
        assert h.get_skill_name_for_tool(CURSOR) == "collab"

    def test_local_skill_name_flat(self):
        """Local skills default to the skill name for flat tools."""
        h = ParsedHandle(is_local=True, name="my-skill")
        assert h.get_skill_name_for_tool(CLAUDE) == "my-skill"

    def test_local_skill_name_nested(self):
        """Local skills get just the name for nested tools."""
        h = ParsedHandle(is_local=True, name="my-skill")
        assert h.get_skill_name_for_tool(CURSOR) == "my-skill"


class TestCursorInstallation:
    """Tests for installing skills to Cursor."""

    def test_install_local_skill_to_cursor(self, tmp_path, skill_fixture):
        """Install a local skill with nested structure."""
        dest_dir = tmp_path / ".cursor" / "skills"
        dest_dir.mkdir(parents=True)

        installed_path = install_local_skill(skill_fixture, dest_dir, CURSOR)

        # Should be nested: local/test-skill/
        assert installed_path == dest_dir / "local" / skill_fixture.name
        assert installed_path.exists()
        assert (installed_path / SKILL_MARKER).exists()

    def test_install_preserves_nested_structure(self, tmp_path, skill_fixture):
        """Nested installation creates proper directory hierarchy."""
        dest_dir = tmp_path / ".cursor" / "skills"
        dest_dir.mkdir(parents=True)

        install_local_skill(skill_fixture, dest_dir, CURSOR)

        # Verify directory structure
        assert (dest_dir / "local").is_dir()
        assert (dest_dir / "local" / skill_fixture.name).is_dir()


class TestCursorUninstallation:
    """Tests for uninstalling skills from Cursor."""

    def test_uninstall_cleans_empty_parents(self, tmp_path, skill_fixture):
        """Uninstalling from Cursor cleans up empty parent directories."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (repo_root / ".git").mkdir()
        skills_dir = repo_root / ".cursor" / "skills"
        skills_dir.mkdir(parents=True)

        # Install skill
        install_local_skill(skill_fixture, skills_dir, CURSOR)

        # Verify nested structure exists
        local_dir = skills_dir / "local"
        assert local_dir.exists()

        # Uninstall
        handle = ParsedHandle(
            is_local=True, name=skill_fixture.name, local_path=skill_fixture
        )
        removed = uninstall_skill(handle, repo_root, CURSOR)

        assert removed
        # Empty parent should be cleaned up
        assert not local_dir.exists()


class TestMultiToolInstallation:
    """Tests for installing to multiple tools."""

    def test_install_to_both_tools(self, tmp_path, skill_fixture):
        """Installing to both Claude and Cursor creates different structures."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (repo_root / ".git").mkdir()

        # Install to Claude
        claude_skills = repo_root / ".claude" / "skills"
        claude_skills.mkdir(parents=True)
        install_local_skill(skill_fixture, claude_skills, CLAUDE)

        # Install to Cursor
        cursor_skills = repo_root / ".cursor" / "skills"
        cursor_skills.mkdir(parents=True)
        install_local_skill(skill_fixture, cursor_skills, CURSOR)

        # Verify Claude has flat structure
        claude_path = claude_skills / skill_fixture.name
        assert claude_path.exists()
        assert (claude_path / SKILL_MARKER).exists()

        # Verify Cursor has nested structure
        cursor_path = cursor_skills / "local" / skill_fixture.name
        assert cursor_path.exists()
        assert (cursor_path / SKILL_MARKER).exists()


class TestGetInstalledSkillsNested:
    """Tests for get_installed_skills with nested structures."""

    def test_get_nested_skills(self, tmp_path, skill_fixture):
        """Get installed skills from nested structure."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (repo_root / ".git").mkdir()
        skills_dir = repo_root / ".cursor" / "skills"
        skills_dir.mkdir(parents=True)

        install_local_skill(skill_fixture, skills_dir, CURSOR)

        skills = get_installed_skills(repo_root, CURSOR)
        assert len(skills) == 1
        assert skills[0] == f"local/{skill_fixture.name}"


class TestIsSkillInstalledNested:
    """Tests for is_skill_installed with nested structures."""

    def test_check_nested_skill(self, tmp_path, skill_fixture):
        """Check if nested skill is installed."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (repo_root / ".git").mkdir()
        skills_dir = repo_root / ".cursor" / "skills"
        skills_dir.mkdir(parents=True)

        install_local_skill(skill_fixture, skills_dir, CURSOR)

        handle = ParsedHandle(
            is_local=True, name=skill_fixture.name, local_path=skill_fixture
        )
        assert is_skill_installed(handle, repo_root, CURSOR)


class TestConfigTools:
    """Tests for tools field in config."""

    def test_default_tools(self, tmp_path):
        """Default tools is just Claude."""
        config = AgrConfig()
        assert config.tools == ["claude"]

    def test_load_tools_from_config(self, tmp_path):
        """Load tools list from config file."""
        config_path = tmp_path / "agr.toml"
        config_path.write_text(
            """
tools = ["claude", "cursor"]
dependencies = []
"""
        )

        config = AgrConfig.load(config_path)
        assert config.tools == ["claude", "cursor"]

    def test_save_non_default_tools(self, tmp_path):
        """Save tools array when not default."""
        config_path = tmp_path / "agr.toml"

        config = AgrConfig()
        config.tools = ["claude", "cursor"]
        config.save(config_path)

        content = config_path.read_text()
        assert 'tools = ["claude", "cursor"]' in content

    def test_save_default_tools_omits(self, tmp_path):
        """Default tools (just claude) is not saved."""
        config_path = tmp_path / "agr.toml"

        config = AgrConfig()
        config.tools = ["claude"]
        config.save(config_path)

        content = config_path.read_text()
        assert "tools" not in content


class TestFetchAndInstallWithTool:
    """Tests for fetch_and_install with tool parameter."""

    def test_fetch_local_with_cursor(self, tmp_path, skill_fixture):
        """Fetch and install local skill to Cursor."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (repo_root / ".git").mkdir()

        handle = ParsedHandle(
            is_local=True, name=skill_fixture.name, local_path=skill_fixture
        )

        installed_path = fetch_and_install(handle, repo_root, CURSOR)

        # Should be nested structure
        expected = repo_root / ".cursor" / "skills" / "local" / skill_fixture.name
        assert installed_path == expected
        assert installed_path.exists()


class TestSeparatorInNestedTool:
    """Tests that nested tools don't reject -- in names."""

    def test_cursor_allows_separator_in_name(self, tmp_path):
        """Cursor allows -- in skill names since it uses nested paths."""
        # Create a skill with -- in its name
        bad_for_claude = tmp_path / "my--special--skill"
        bad_for_claude.mkdir()
        (bad_for_claude / SKILL_MARKER).write_text("# Special Skill")

        dest_dir = tmp_path / ".cursor" / "skills"
        dest_dir.mkdir(parents=True)

        # Should NOT raise for Cursor (nested tool)
        installed_path = install_local_skill(bad_for_claude, dest_dir, CURSOR)
        assert installed_path.exists()
        assert installed_path == dest_dir / "local" / "my--special--skill"
