"""AIandMe pytest plugin for AI agent security testing.

This plugin provides pytest integration for running AIandMe security tests
as part of your test suite.

Usage:
    # Install with pytest support
    pip install aiandme-cli[pytest]

    # Run security tests
    pytest --aiandme tests/
    pytest -m aiandme
    pytest --aiandme-category=adversarial

    # In your test files
    import pytest

    @pytest.mark.aiandme
    def test_prompt_injection(aiandme):
        result = aiandme.test("llm001")
        assert result.passed, f"Failed: {result.findings}"
"""

import pytest
from typing import Optional
import json
import sys

from .fixtures import AIandMeTestClient
from .report import AIandMeReporter


def pytest_addoption(parser):
    """Add AIandMe command line options."""
    group = parser.getgroup("aiandme", "AIandMe security testing")

    group.addoption(
        "--aiandme",
        action="store_true",
        default=False,
        help="Enable AIandMe security tests",
    )

    group.addoption(
        "--aiandme-category",
        action="store",
        default=None,
        metavar="CATEGORY",
        help="Test category to run (e.g., adversarial, behavioral)",
    )

    group.addoption(
        "--aiandme-level",
        action="store",
        default="unit",
        metavar="LEVEL",
        choices=["unit", "system", "acceptance"],
        help="Testing level (default: unit)",
    )

    group.addoption(
        "--aiandme-project",
        action="store",
        default=None,
        metavar="PROJECT_ID",
        help="Project ID to test against (uses config if not specified)",
    )

    group.addoption(
        "--aiandme-fail-on",
        action="store",
        default="high",
        metavar="SEVERITY",
        choices=["critical", "high", "medium", "low", "any"],
        help="Fail tests on findings at or above this severity (default: high)",
    )

    group.addoption(
        "--aiandme-baseline",
        action="store",
        default=None,
        metavar="FILE",
        help="Baseline file for regression detection",
    )

    group.addoption(
        "--aiandme-save-baseline",
        action="store",
        default=None,
        metavar="FILE",
        help="Save current results as baseline",
    )


def pytest_configure(config):
    """Configure pytest with AIandMe markers and settings."""
    # Register markers
    config.addinivalue_line(
        "markers",
        "aiandme: mark test as an AIandMe security test"
    )
    config.addinivalue_line(
        "markers",
        "aiandme_category(name): mark test for a specific category (e.g., adversarial)"
    )
    config.addinivalue_line(
        "markers",
        "aiandme_skip_ci: skip this test in CI environments"
    )

    # Initialize reporter if AIandMe is enabled
    if config.getoption("--aiandme"):
        config._aiandme_reporter = AIandMeReporter(config)


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on AIandMe options."""
    if not config.getoption("--aiandme"):
        # Skip all aiandme-marked tests if --aiandme not provided
        skip_aiandme = pytest.mark.skip(reason="need --aiandme option to run")
        for item in items:
            if "aiandme" in item.keywords:
                item.add_marker(skip_aiandme)
        return

    # Filter by category if specified
    category_filter = config.getoption("--aiandme-category")
    if category_filter:
        for item in items:
            if "aiandme" in item.keywords:
                # Check if test has matching category marker
                category_marker = item.get_closest_marker("aiandme_category")
                if category_marker:
                    if category_marker.args[0] != category_filter:
                        item.add_marker(pytest.mark.skip(
                            reason=f"filtered by --aiandme-category={category_filter}"
                        ))


def pytest_sessionstart(session):
    """Called before test collection."""
    if session.config.getoption("--aiandme"):
        # Print AIandMe banner
        print("\n" + "=" * 60)
        print("  AIandMe Security Testing")
        print("=" * 60)


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Add AIandMe summary to test report."""
    if not config.getoption("--aiandme"):
        return

    reporter = getattr(config, "_aiandme_reporter", None)
    if reporter:
        reporter.terminal_summary(terminalreporter)


@pytest.fixture
def aiandme(request) -> AIandMeTestClient:
    """Fixture providing AIandMe test client.

    Usage:
        def test_security(aiandme):
            result = aiandme.test("llm001")
            assert result.passed
    """
    config = request.config

    return AIandMeTestClient(
        project_id=config.getoption("--aiandme-project"),
        testing_level=config.getoption("--aiandme-level"),
        fail_on=config.getoption("--aiandme-fail-on"),
    )


@pytest.fixture
def aiandme_baseline(request) -> Optional[dict]:
    """Fixture providing baseline results for regression detection.

    Usage:
        def test_no_regressions(aiandme, aiandme_baseline):
            result = aiandme.test("llm001")
            if aiandme_baseline:
                regressions = result.compare(aiandme_baseline)
                assert not regressions
    """
    baseline_path = request.config.getoption("--aiandme-baseline")
    if not baseline_path:
        return None

    try:
        with open(baseline_path) as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        pytest.fail(f"Invalid baseline file: {baseline_path}")


@pytest.fixture
def aiandme_posture(aiandme) -> dict:
    """Fixture providing current security posture.

    Usage:
        def test_posture_threshold(aiandme_posture):
            assert aiandme_posture["score"] >= 70, "Posture too low"
    """
    return aiandme.get_posture()
