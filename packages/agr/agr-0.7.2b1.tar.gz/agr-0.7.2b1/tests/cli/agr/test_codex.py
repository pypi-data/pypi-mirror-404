"""CLI tests for OpenAI Codex tool support."""

from tests.cli.assertions import assert_cli


class TestCodexAdd:
    """Tests for agr add with Codex tool."""

    def test_add_local_skill_to_codex_flat_structure(
        self, agr, cli_project, cli_skill, cli_config
    ):
        """agr add local skill installs to .codex/skills/<name>/."""
        cli_config('tools = ["codex"]\ndependencies = []')

        result = agr("add", "./skills/test-skill")

        assert_cli(result).succeeded()
        installed = cli_project / ".codex" / "skills" / "test-skill"
        assert installed.exists()
        assert (installed / "SKILL.md").exists()


class TestCodexSync:
    """Tests for agr sync with Codex tool."""

    def test_sync_installs_to_codex_when_configured(
        self, agr, cli_project, cli_skill, cli_config
    ):
        """agr sync with tools = ["codex"] installs to correct path."""
        cli_config(
            """
tools = ["codex"]
dependencies = [
    { path = "./skills/test-skill", type = "skill" },
]
"""
        )

        result = agr("sync")

        assert_cli(result).succeeded()
        installed = cli_project / ".codex" / "skills" / "test-skill"
        assert installed.exists()

    def test_sync_creates_codex_skills_directory(
        self, agr, cli_project, cli_skill, cli_config
    ):
        """agr sync creates .codex/skills/ if it doesn't exist."""
        cli_config(
            """
tools = ["codex"]
dependencies = [
    { path = "./skills/test-skill", type = "skill" },
]
"""
        )
        codex_dir = cli_project / ".codex"
        assert not codex_dir.exists()

        result = agr("sync")

        assert_cli(result).succeeded()
        assert codex_dir.exists()
        assert (codex_dir / "skills" / "test-skill").exists()


class TestCodexRemove:
    """Tests for agr remove with Codex tool."""

    def test_remove_cleans_up_codex_flat_structure(
        self, agr, cli_project, cli_skill, cli_config
    ):
        """agr remove removes skill from .codex/skills/."""
        cli_config('tools = ["codex"]\ndependencies = []')
        agr("add", "./skills/test-skill")

        installed = cli_project / ".codex" / "skills" / "test-skill"
        assert installed.exists()

        result = agr("remove", "./skills/test-skill")

        assert_cli(result).succeeded()
        assert not installed.exists()


class TestMultiToolCodexClaude:
    """Tests for multi-tool scenarios with Codex and Claude."""

    def test_add_installs_to_both_claude_and_codex(
        self, agr, cli_project, cli_skill, cli_config
    ):
        """agr add with tools = ["claude", "codex"] installs to both."""
        cli_config('tools = ["claude", "codex"]\ndependencies = []')

        result = agr("add", "./skills/test-skill")

        assert_cli(result).succeeded()
        assert (cli_project / ".claude" / "skills" / "test-skill").exists()
        assert (cli_project / ".codex" / "skills" / "test-skill").exists()
