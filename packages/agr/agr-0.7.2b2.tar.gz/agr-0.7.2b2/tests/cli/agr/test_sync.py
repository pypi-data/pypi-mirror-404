"""CLI tests for agr sync command."""

from tests.cli.assertions import assert_cli


class TestAgrSync:
    """Tests for agr sync command."""

    def test_sync_no_config_message(self, agr):
        """agr sync without config shows message."""
        result = agr("sync")

        assert_cli(result).succeeded().stdout_contains("No agr.toml")

    def test_sync_empty_deps_message(self, agr, cli_config):
        """agr sync with empty deps shows message."""
        cli_config("dependencies = []")

        result = agr("sync")

        assert_cli(result).succeeded().stdout_contains("Nothing to sync")

    def test_sync_reports_up_to_date(self, agr, cli_project, cli_skill):
        """agr sync reports already installed skills."""
        agr("add", "./skills/test-skill")

        result = agr("sync")

        assert_cli(result).succeeded().stdout_contains("up to date")

    def test_sync_instructions(self, agr, cli_project, cli_config):
        """agr sync syncs instruction files when configured."""
        (cli_project / "CLAUDE.md").write_text("Claude instructions\n")
        (cli_project / "AGENTS.md").write_text("Agents instructions\n")
        cli_config(
            """
tools = ["claude", "codex"]
sync_instructions = true
dependencies = []
"""
        )

        result = agr("sync")

        assert_cli(result).succeeded()
        assert (cli_project / "AGENTS.md").read_text() == (
            cli_project / "CLAUDE.md"
        ).read_text()
