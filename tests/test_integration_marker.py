"""The ``integration`` marker: skipped by ``uv run pytest``, run with ``-m integration``."""

import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION_TEST = """
import pytest

@pytest.mark.integration
def test_talks_to_real_postgres():
    pass
"""


@pytest.fixture
def project(pytester: pytest.Pytester) -> pytest.Pytester:
    """A sandbox with this repo's ``[tool.pytest]`` settings and one integration test."""
    settings = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    pytest_settings = settings["tool"]["pytest"]
    markers = ", ".join(repr(m) for m in pytest_settings["markers"])
    addopts = ", ".join(repr(a) for a in pytest_settings["addopts"])
    pytester.makepyprojecttoml(
        f"[tool.pytest]\nstrict = true\nmarkers = [{markers}]\naddopts = [{addopts}]\n"
    )
    pytester.makepyfile(INTEGRATION_TEST)
    return pytester


def test_ci_run_skips_integration_tests(project: pytest.Pytester) -> None:
    result = project.runpytest()
    result.assert_outcomes(deselected=1)


def test_local_run_with_marker_runs_integration_tests(project: pytest.Pytester) -> None:
    result = project.runpytest("-m", "integration")
    result.assert_outcomes(passed=1)
