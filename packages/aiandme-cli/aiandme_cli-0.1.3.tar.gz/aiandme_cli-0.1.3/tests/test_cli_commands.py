"""
Pytest-based CLI command tests.

These tests use Click's CliRunner to test CLI commands in isolation.

Usage:
    export AIANDME_TEST_TOKEN="your-jwt-token"
    export AIANDME_TEST_ORG_ID="your-org-id"
    export AIANDME_BASE_URL="http://localhost:7071/api"

    pytest tests/test_cli_commands.py -v
"""

import json
import os
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from click.testing import CliRunner
from aiandme_cli.main import cli


class TestAuthCommands:
    """Test authentication-related CLI commands."""

    def test_whoami_authenticated(self, cli_runner, test_config, setup_credentials):
        """Test whoami shows authenticated status."""
        env = {"AIANDME_BASE_URL": test_config["base_url"]}
        result = cli_runner.invoke(cli, ["whoami"], env=env)

        assert result.exit_code == 0
        assert "authenticated" in result.output.lower() or "logged in" in result.output.lower()

    def test_logout_clears_session(self, cli_runner, test_config, setup_credentials):
        """Test logout command."""
        env = {"AIANDME_BASE_URL": test_config["base_url"]}
        result = cli_runner.invoke(cli, ["logout"], env=env)

        assert result.exit_code == 0
        assert "logout" in result.output.lower() or "logged out" in result.output.lower()


class TestOrgCommands:
    """Test organisation-related CLI commands."""

    def test_orgs_list(self, cli_runner, test_config, setup_credentials):
        """Test listing organisations."""
        env = {"AIANDME_BASE_URL": test_config["base_url"]}
        result = cli_runner.invoke(cli, ["orgs", "list"], env=env)

        assert result.exit_code == 0
        # Should show at least the test org
        assert test_config["org_id"][:8] in result.output

    def test_orgs_use(self, cli_runner, test_config, setup_credentials):
        """Test selecting an organisation."""
        env = {"AIANDME_BASE_URL": test_config["base_url"]}
        result = cli_runner.invoke(cli, ["orgs", "use", test_config["org_id"]], env=env)

        assert result.exit_code == 0


class TestProjectCommands:
    """Test project-related CLI commands."""

    def test_projects_list(self, cli_runner, test_config, setup_credentials):
        """Test listing projects."""
        env = {"AIANDME_BASE_URL": test_config["base_url"]}
        result = cli_runner.invoke(cli, ["projects", "list"], env=env)

        assert result.exit_code == 0

    def test_projects_use(self, cli_runner, test_config, test_project, setup_credentials):
        """Test selecting a project."""
        env = {"AIANDME_BASE_URL": test_config["base_url"]}
        result = cli_runner.invoke(cli, ["projects", "use", test_project["id"]], env=env)

        assert result.exit_code == 0

    def test_projects_show(self, cli_runner, test_config, test_project, setup_project_credentials):
        """Test showing project details."""
        env = {"AIANDME_BASE_URL": test_config["base_url"]}
        result = cli_runner.invoke(cli, ["projects", "show", test_project["id"]], env=env)

        assert result.exit_code == 0
        assert test_project["id"][:8] in result.output or test_project["name"] in result.output


class TestExperimentCommands:
    """Test experiment-related CLI commands."""

    def test_experiments_list(self, cli_runner, test_config, test_project, setup_project_credentials):
        """Test listing experiments."""
        env = {"AIANDME_BASE_URL": test_config["base_url"]}
        result = cli_runner.invoke(cli, ["experiments", "list"], env=env)

        assert result.exit_code == 0

    def test_status_no_experiment(self, cli_runner, test_config, test_project, setup_project_credentials):
        """Test status when no experiments exist."""
        env = {"AIANDME_BASE_URL": test_config["base_url"]}
        result = cli_runner.invoke(cli, ["status"], env=env)

        # Should handle gracefully
        assert result.exit_code in [0, 1]


class TestPostureCommands:
    """Test posture-related CLI commands."""

    def test_posture(self, cli_runner, test_config, test_project, setup_project_credentials):
        """Test posture command."""
        env = {"AIANDME_BASE_URL": test_config["base_url"]}
        result = cli_runner.invoke(cli, ["posture"], env=env)

        assert result.exit_code == 0
        # Should show some posture info
        assert "score" in result.output.lower() or "posture" in result.output.lower()

    def test_posture_json(self, cli_runner, test_config, test_project, setup_project_credentials):
        """Test posture command with JSON output."""
        env = {"AIANDME_BASE_URL": test_config["base_url"]}
        result = cli_runner.invoke(cli, ["posture", "--json"], env=env)

        assert result.exit_code == 0
        # Should be valid JSON
        try:
            data = json.loads(result.output)
            assert isinstance(data, dict)
        except json.JSONDecodeError:
            pytest.fail("Output is not valid JSON")


class TestGuardrailsCommands:
    """Test guardrails-related CLI commands."""

    def test_guardrails_export_aiandme(self, cli_runner, test_config, test_project, setup_project_credentials):
        """Test guardrails export in aiandme format."""
        env = {"AIANDME_BASE_URL": test_config["base_url"]}
        result = cli_runner.invoke(cli, ["guardrails", "--vendor", "aiandme", "--format", "json"], env=env)

        assert result.exit_code == 0

    def test_guardrails_export_openai(self, cli_runner, test_config, test_project, setup_project_credentials):
        """Test guardrails export in openai format."""
        env = {"AIANDME_BASE_URL": test_config["base_url"]}
        result = cli_runner.invoke(cli, ["guardrails", "--vendor", "openai", "--format", "json"], env=env)

        assert result.exit_code == 0


class TestLogsCommands:
    """Test logs-related CLI commands."""

    def test_logs(self, cli_runner, test_config, test_project, setup_project_credentials):
        """Test logs command."""
        env = {"AIANDME_BASE_URL": test_config["base_url"]}
        result = cli_runner.invoke(cli, ["logs"], env=env)

        # Should handle case where no logs exist
        assert result.exit_code in [0, 1]


class TestTestCommands:
    """Test the 'test' command."""

    def test_test_help(self, cli_runner, test_config, setup_credentials):
        """Test help for test command."""
        env = {"AIANDME_BASE_URL": test_config["base_url"]}
        result = cli_runner.invoke(cli, ["test", "--help"], env=env)

        assert result.exit_code == 0
        assert "category" in result.output.lower()
        assert "level" in result.output.lower()


class TestDocsCommands:
    """Test docs-related CLI commands."""

    def test_docs_help(self, cli_runner, test_config, setup_credentials):
        """Test docs help."""
        env = {"AIANDME_BASE_URL": test_config["base_url"]}
        result = cli_runner.invoke(cli, ["docs", "--help"], env=env)

        assert result.exit_code == 0
