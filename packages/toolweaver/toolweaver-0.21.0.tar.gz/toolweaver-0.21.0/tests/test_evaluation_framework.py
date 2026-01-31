"""
Tests for Evaluation Framework
"""

import json
from typing import Any

from orchestrator.evaluation.runner import EvaluationResult, EvaluationRunner


def test_evaluation_result_creation() -> None:
    """Test creating an evaluation result."""
    result = EvaluationResult(
        test_name="test_example",
        passed=True,
        expected=42,
        actual=42,
        duration_ms=10.5,
        tags=["smoke"],
    )
    assert result.test_name == "test_example"
    assert result.passed is True
    assert result.expected == 42
    assert result.actual == 42


def test_runner_initialization() -> None:
    """Test runner initializes with defaults."""
    runner = EvaluationRunner()
    assert runner.results_dir.exists()
    assert runner.default_tolerance == 0.0


def test_runner_with_custom_settings(tmp_path: Any) -> None:
    """Test runner with custom results directory and tolerance."""
    runner = EvaluationRunner(results_dir=str(tmp_path), default_tolerance=0.5)
    assert runner.results_dir == tmp_path
    assert runner.default_tolerance == 0.5


def test_load_yaml_suite(tmp_path: Any) -> None:
    """Test loading a YAML suite."""
    suite_file = tmp_path / "test_suite.yaml"
    suite_file.write_text("""
name: test_suite
tests:
  - name: test1
    endpoint: /api/health
    expected:
      success: true
""")

    runner = EvaluationRunner()
    suite = runner.load_suite(str(suite_file))

    assert suite["name"] == "test_suite"
    assert len(suite["tests"]) == 1
    assert suite["tests"][0]["name"] == "test1"


def test_load_json_suite(tmp_path: Any) -> None:
    """Test loading a JSON suite."""
    suite_file = tmp_path / "test_suite.json"
    suite_data = {"name": "json_suite", "tests": [{"name": "test1", "endpoint": "/api/health"}]}
    suite_file.write_text(json.dumps(suite_data))

    runner = EvaluationRunner()
    suite = runner.load_suite(str(suite_file))

    assert suite["name"] == "json_suite"
    assert len(suite["tests"]) == 1


def test_compare_exact_match() -> None:
    """Test exact value comparison."""
    runner = EvaluationRunner()
    assert runner._compare(42, 42, {}) is True
    assert runner._compare("test", "test", {}) is True
    assert runner._compare(42, 43, {}) is False


def test_compare_with_tolerance() -> None:
    """Test numeric comparison with tolerance."""
    runner = EvaluationRunner(default_tolerance=0.1)

    # Within tolerance
    assert runner._compare(10.0, 10.05, {}) is True
    assert runner._compare(10.0, 9.95, {}) is True

    # Outside tolerance
    assert runner._compare(10.0, 10.2, {}) is False

    # Custom tolerance
    assert runner._compare(10.0, 10.5, {"tolerance": 0.5}) is True


def test_compare_regex_match() -> None:
    """Test regex pattern matching."""
    runner = EvaluationRunner()

    test_spec = {"match_type": "regex"}
    assert runner._compare("test123", r"test\d+", test_spec) is True
    assert runner._compare("hello world", r"world$", test_spec) is True
    assert runner._compare("test", r"\d+", test_spec) is False


def test_run_suite_with_mock_api(tmp_path: Any) -> None:
    """Test running a suite with mocked API client."""

    # Create a simple mock client
    class MockResponse:
        def __init__(self, data: Any) -> None:
            self._data = data
            self.is_json = True

        def get_json(self) -> Any:
            return self._data

    class MockClient:
        def get(self, endpoint: str, headers: Any = None) -> MockResponse:
            return MockResponse({"success": True, "status": "healthy"})

    # Create suite
    suite_file = tmp_path / "test.yaml"
    suite_file.write_text("""
name: mock_test
tests:
  - name: test_success
    endpoint: /api/health
    field: success
    expected: true
  - name: test_status
    endpoint: /api/health
    field: status
    expected: healthy
""")

    runner = EvaluationRunner(api_client=MockClient(), results_dir=str(tmp_path))
    result = runner.run_suite(str(suite_file))

    assert result.suite_name == "mock_test"
    assert result.total == 2
    assert result.passed == 2
    assert result.failed == 0
    assert result.success_rate == 100.0


def test_run_suite_saves_artifacts(tmp_path: Any) -> None:
    """Test that suite results are saved as JSON artifacts."""

    class MockResponse:
        def __init__(self, data: Any) -> None:
            self._data = data
            self.is_json = True

        def get_json(self) -> Any:
            return self._data

    class MockClient:
        def get(self, endpoint: str, headers: Any = None) -> MockResponse:
            return MockResponse({"value": 42})

    suite_file = tmp_path / "test.yaml"
    suite_file.write_text("""
name: artifact_test
tests:
  - name: test1
    endpoint: /test
    field: value
    expected: 42
""")

    runner = EvaluationRunner(api_client=MockClient(), results_dir=str(tmp_path))
    runner.run_suite(str(suite_file))

    # Find artifact
    artifacts = list(tmp_path.glob("artifact_test_*.json"))
    assert len(artifacts) >= 1

    # Verify artifact content
    with open(artifacts[0]) as f:
        data = json.load(f)

    assert data["suite_name"] == "artifact_test"
    assert data["total"] == 1
    assert data["passed"] == 1


def test_tag_filtering(tmp_path: Any) -> None:
    """Test filtering tests by tags."""

    class MockResponse:
        def __init__(self, data: Any) -> None:
            self._data = data
            self.is_json = True

        def get_json(self) -> Any:
            return self._data

    class MockClient:
        def get(self, endpoint: str, headers: Any = None) -> MockResponse:
            return MockResponse({"result": "ok"})

    suite_file = tmp_path / "test.yaml"
    suite_file.write_text("""
name: tag_test
tests:
  - name: smoke_test
    endpoint: /test
    expected: {"result": "ok"}
    tags:
      - smoke
  - name: full_test
    endpoint: /test
    expected: {"result": "ok"}
    tags:
      - full
""")

    runner = EvaluationRunner(api_client=MockClient(), results_dir=str(tmp_path))

    # Run with smoke tag only
    result = runner.run_suite(str(suite_file), tags=["smoke"])
    assert result.total == 1
    assert result.results[0].test_name == "smoke_test"
