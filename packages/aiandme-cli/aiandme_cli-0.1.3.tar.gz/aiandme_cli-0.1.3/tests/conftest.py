"""
Pytest fixtures for CLI integration tests.

Usage:
    # Set environment variables before running
    export AIANDME_TEST_TOKEN="your-jwt-token"
    export AIANDME_TEST_ORG_ID="your-org-id"
    export AIANDME_BASE_URL="http://localhost:7071/api"

    # Run tests
    pytest tests/ -v
"""

import os
import json
import time
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from click.testing import CliRunner
from aiandme_cli.client import AIandMeClient
from aiandme_cli.config import CONFIG_DIR, TOKEN_FILE


# =============================================================================
# Test Configuration
# =============================================================================

TEST_PREFIX = "_PYTEST_CLI_"


def get_test_config():
    """Get test configuration from environment variables."""
    token = os.environ.get("AIANDME_TEST_TOKEN")
    org_id = os.environ.get("AIANDME_TEST_ORG_ID")
    base_url = os.environ.get("AIANDME_BASE_URL", "http://localhost:7071/api")

    if not token or not org_id:
        pytest.skip(
            "AIANDME_TEST_TOKEN and AIANDME_TEST_ORG_ID environment variables required. "
            "Run: export AIANDME_TEST_TOKEN='...' AIANDME_TEST_ORG_ID='...'"
        )

    return {
        "token": token,
        "org_id": org_id,
        "base_url": base_url,
    }


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def test_config():
    """Session-scoped test configuration."""
    return get_test_config()


@pytest.fixture(scope="session")
def cli_runner():
    """Click CLI runner."""
    return CliRunner()


@pytest.fixture(scope="session")
def api_client(test_config):
    """Configured API client for direct API calls."""
    client = AIandMeClient(base_url=test_config["base_url"])
    client._api_token = test_config["token"]
    client._token_expires_at = time.time() + 3600
    client._organisation_id = test_config["org_id"]
    return client


@pytest.fixture(scope="session")
def credentials_backup():
    """Backup and restore credentials around tests."""
    original = None
    if TOKEN_FILE.exists():
        original = TOKEN_FILE.read_text()

    yield original

    # Restore after all tests
    if original:
        TOKEN_FILE.write_text(original)
    elif TOKEN_FILE.exists():
        TOKEN_FILE.unlink()


@pytest.fixture(scope="function")
def setup_credentials(test_config, credentials_backup):
    """Setup test credentials for each test."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    credentials = {
        "api_token": test_config["token"],
        "expires_at": time.time() + 3600,
        "refresh_token": None,
        "organisation_id": test_config["org_id"],
        "project_id": None,
        "base_url": test_config["base_url"],
    }

    TOKEN_FILE.write_text(json.dumps(credentials))
    TOKEN_FILE.chmod(0o600)

    yield credentials

    # Cleanup handled by credentials_backup fixture


@pytest.fixture(scope="session")
def test_project(api_client, test_config):
    """Create a test project for the session."""
    project_name = f"{TEST_PREFIX}project_{int(time.time())}"

    # Setup credentials first
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    credentials = {
        "api_token": test_config["token"],
        "expires_at": time.time() + 3600,
        "refresh_token": None,
        "organisation_id": test_config["org_id"],
        "project_id": None,
        "base_url": test_config["base_url"],
    }
    TOKEN_FILE.write_text(json.dumps(credentials))

    try:
        response = api_client.post("projects", data={
            "name": project_name,
            "description": "Pytest CLI integration test project",
            "scope": {
                "overall_business_scope": "Test chatbot for pytest CLI testing",
                "intents": {
                    "permitted": ["Answer questions", "Provide help"],
                    "restricted": ["Share secrets", "Execute code"]
                }
            }
        })

        project_id = response.get("id")
        api_client._project_id = project_id

        # Update credentials with project
        credentials["project_id"] = project_id
        TOKEN_FILE.write_text(json.dumps(credentials))

        yield {
            "id": project_id,
            "name": project_name,
        }

        # Cleanup
        try:
            api_client.delete(f"projects/{project_id}")
        except Exception:
            pass

    except Exception as e:
        pytest.skip(f"Could not create test project: {e}")


@pytest.fixture(scope="function")
def setup_project_credentials(test_config, test_project, credentials_backup):
    """Setup credentials with project selected."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    credentials = {
        "api_token": test_config["token"],
        "expires_at": time.time() + 3600,
        "refresh_token": None,
        "organisation_id": test_config["org_id"],
        "project_id": test_project["id"],
        "base_url": test_config["base_url"],
    }

    TOKEN_FILE.write_text(json.dumps(credentials))
    TOKEN_FILE.chmod(0o600)

    yield credentials


# =============================================================================
# Cleanup Fixture
# =============================================================================

@pytest.fixture(scope="session", autouse=True)
def cleanup_test_data(api_client):
    """Cleanup any leftover test data after all tests."""
    yield

    # After all tests, clean up any TEST_PREFIX projects
    try:
        response = api_client.list_projects(size=100)
        for project in response.get("data", []):
            if project.get("name", "").startswith(TEST_PREFIX):
                try:
                    api_client.delete(f"projects/{project['id']}")
                    print(f"\nCleaned up: {project['name']}")
                except Exception:
                    pass
    except Exception:
        pass
