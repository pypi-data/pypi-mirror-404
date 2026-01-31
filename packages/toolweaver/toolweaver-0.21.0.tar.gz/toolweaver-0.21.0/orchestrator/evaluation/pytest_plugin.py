"""
Pytest plugin for Evaluation Framework

Adds --eval-suite option to pytest to run evaluation suites during testing.

Usage:
    pytest --eval-suite benchmarks/task_suites/api_health_check.yaml
    pytest --eval-suite benchmarks/task_suites/ --eval-tags smoke
"""

from pathlib import Path
from typing import Any

import pytest

from orchestrator.evaluation.runner import EvaluationRunner


def pytest_addoption(parser: Any) -> None:
    """Add evaluation suite options to pytest."""
    parser.addoption(
        "--eval-suite",
        action="store",
        default=None,
        help="Path to evaluation suite file or directory",
    )
    parser.addoption(
        "--eval-tags",
        action="store",
        default=None,
        help="Comma-separated tags to filter evaluation tests",
    )


def pytest_configure(config: Any) -> None:
    """Register evaluation markers."""
    config.addinivalue_line(
        "markers",
        "eval_suite: mark test as an evaluation suite runner",
    )


def pytest_collection_modifyitems(config: Any, items: Any) -> None:
    """Add eval suite tests if --eval-suite is specified."""
    suite_path = config.getoption("--eval-suite")
    if not suite_path:
        return

    # Import here to avoid circular dependencies
    from orchestrator.server.app import app
    from orchestrator.skills.skill_executor import get_executor

    client = app.test_client()
    executor = get_executor()
    runner = EvaluationRunner(api_client=client, skill_executor=executor)

    tags_str = config.getoption("--eval-tags")
    tags = tags_str.split(",") if tags_str else None

    path = Path(suite_path)

    # If directory, find all suites
    if path.is_dir():
        suite_files = list(path.glob("**/*.yaml")) + list(path.glob("**/*.yml")) + list(path.glob("**/*.json"))
    else:
        suite_files = [path]

    # Create test items for each suite
    for suite_file in suite_files:
        item = EvalSuiteItem.from_parent(
            parent=items[0].session if items else config.hook,
            name=f"eval_suite[{suite_file.name}]",
            suite_path=str(suite_file),
            runner=runner,
            tags=tags,
        )
        items.append(item)


class EvalSuiteItem(pytest.Item):
    """Custom pytest item for evaluation suite."""

    def __init__(self, name: str, parent: Any, suite_path: str, runner: Any, tags: Any = None) -> None:
        """Initialize evaluation suite test item."""
        super().__init__(name, parent)
        self.suite_path = suite_path
        self.runner = runner
        self.tags = tags

    def runtest(self) -> None:
        """Run the evaluation suite."""
        result = self.runner.run_suite(self.suite_path, tags=self.tags)

        if result.failed > 0:
            failures = [
                f"  - {r.test_name}: {r.error or f'Expected {r.expected}, got {r.actual}'}"
                for r in result.results
                if not r.passed
            ]
            raise EvalSuiteFailure(
                f"\n{result.failed}/{result.total} tests failed:\n" + "\n".join(failures)
            )

    def repr_failure(self, excinfo: Any, style: Any = None) -> Any:
        """Represent test failure."""
        if isinstance(excinfo.value, EvalSuiteFailure):
            return str(excinfo.value)
        return super().repr_failure(excinfo, style)

    def reportinfo(self) -> tuple[Any, int, str]:
        """Report test location."""
        return self.path, 0, f"eval_suite: {self.suite_path}"


class EvalSuiteFailure(Exception):
    """Exception raised when evaluation suite fails."""

    pass
