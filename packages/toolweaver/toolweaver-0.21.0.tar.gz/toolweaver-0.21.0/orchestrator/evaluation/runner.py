"""
Evaluation Suite Runner

Executes test suites defined in YAML/JSON against API endpoints or skills.
Supports regex matching, tolerance-based comparison, and artifact generation.
"""

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


@dataclass
class EvaluationResult:
    """Result of a single evaluation test."""

    test_name: str
    passed: bool
    expected: Any
    actual: Any
    error: str | None = None
    duration_ms: float | None = None
    tags: list[str] = field(default_factory=list)


@dataclass
class SuiteResult:
    """Result of an entire evaluation suite."""

    suite_name: str
    total: int
    passed: int
    failed: int
    duration_ms: float
    results: list[EvaluationResult]
    timestamp: str

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        return (self.passed / self.total * 100) if self.total > 0 else 0.0


class EvaluationRunner:
    """
    Executes evaluation suites against API or skills.

    Features:
    - Load suites from YAML/JSON
    - Regex and exact matching
    - Tolerance-based numeric comparison
    - Tag-based filtering
    - Artifact generation (JSON results)
    """

    def __init__(
        self,
        api_client: Any = None,
        skill_executor: Any = None,
        results_dir: str | None = None,
        default_tolerance: float = 0.0,
    ):
        """
        Initialize evaluation runner.

        Args:
            api_client: Flask test client for API evaluation
            skill_executor: SkillExecutor for direct skill evaluation
            results_dir: Directory for storing results artifacts
            default_tolerance: Default numeric tolerance for comparisons
        """
        self.api_client = api_client
        self.skill_executor = skill_executor
        results_dir_val = results_dir or os.getenv("EVAL_RESULTS_DIR", "STATISTICS")
        self.results_dir = Path(results_dir_val) if results_dir_val else Path("STATISTICS")
        self.default_tolerance = default_tolerance or float(
            os.getenv("EVAL_TOLERANCE_DEFAULT", "0.0")
        )

        # Create results directory if it doesn't exist
        if not self.results_dir.exists():
            self.results_dir.mkdir(parents=True, exist_ok=True)

    def load_suite(self, suite_path: str) -> dict[str, Any]:
        """Load evaluation suite from YAML or JSON file."""
        path = Path(suite_path)
        if not path.exists():
            raise FileNotFoundError(f"Suite file not found: {suite_path}")

        with open(path, encoding="utf-8") as f:
            if path.suffix in [".yaml", ".yml"]:
                return yaml.safe_load(f)
            elif path.suffix == ".json":
                return json.load(f)
            else:
                raise ValueError(f"Unsupported suite format: {path.suffix}")

    def run_suite(self, suite_path: str, tags: list[str] | None = None) -> SuiteResult:
        """
        Run evaluation suite from file.

        Args:
            suite_path: Path to YAML/JSON suite definition
            tags: Optional list of tags to filter tests

        Returns:
            SuiteResult with all test outcomes
        """
        suite_data = self.load_suite(suite_path)
        suite_name = suite_data.get("name", Path(suite_path).stem)
        tests = suite_data.get("tests", [])

        # Filter by tags if specified
        if tags:
            tests = [t for t in tests if any(tag in t.get("tags", []) for tag in tags)]

        results = []
        start_time = datetime.now()

        for test_spec in tests:
            result = self._run_test(test_spec)
            results.append(result)

        duration_ms = (datetime.now() - start_time).total_seconds() * 1000

        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed

        suite_result = SuiteResult(
            suite_name=suite_name,
            total=len(results),
            passed=passed,
            failed=failed,
            duration_ms=duration_ms,
            results=results,
            timestamp=datetime.now().isoformat(),
        )

        # Save artifact
        self._save_results(suite_result)

        return suite_result

    def _run_test(self, test_spec: dict[str, Any]) -> EvaluationResult:
        """Execute a single test from specification."""
        import time

        start = time.time()

        try:
            # Determine target (API or skill)
            if "endpoint" in test_spec:
                actual = self._call_api(test_spec)
            elif "skill" in test_spec:
                actual = self._call_skill(test_spec)
            else:
                raise ValueError("Test must specify 'endpoint' or 'skill'")

            # Compare result
            expected = test_spec.get("expected")
            passed = self._compare(actual, expected, test_spec)

            duration_ms = (time.time() - start) * 1000

            return EvaluationResult(
                test_name=test_spec.get("name", "unnamed"),
                passed=passed,
                expected=expected,
                actual=actual,
                duration_ms=duration_ms,
                tags=test_spec.get("tags", []),
            )
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            return EvaluationResult(
                test_name=test_spec.get("name", "unnamed"),
                passed=False,
                expected=test_spec.get("expected"),
                actual=None,
                error=str(e),
                duration_ms=duration_ms,
                tags=test_spec.get("tags", []),
            )

    def _call_api(self, test_spec: dict[str, Any]) -> Any:
        """Call API endpoint via test client."""
        if not self.api_client:
            raise ValueError("API client not configured")

        method = test_spec.get("method", "GET").upper()
        endpoint = test_spec["endpoint"]
        headers = test_spec.get("headers", {})
        body = test_spec.get("body")

        if method == "GET":
            response = self.api_client.get(endpoint, headers=headers)
        elif method == "POST":
            response = self.api_client.post(endpoint, json=body, headers=headers)
        elif method == "PUT":
            response = self.api_client.put(endpoint, json=body, headers=headers)
        elif method == "DELETE":
            response = self.api_client.delete(endpoint, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        # Extract field if specified
        result = response.get_json() if response.is_json else response.data
        if "field" in test_spec:
            for key in test_spec["field"].split("."):
                result = result.get(key) if isinstance(result, dict) else None

        return result

    def _call_skill(self, test_spec: dict[str, Any]) -> Any:
        """Call skill capability directly."""
        if not self.skill_executor:
            raise ValueError("Skill executor not configured")

        skill_id = test_spec["skill"]
        capability = test_spec["capability"]
        parameters = test_spec.get("parameters", {})

        result = self.skill_executor.execute(skill_id, capability, parameters)

        if not result.success:
            raise RuntimeError(f"Skill execution failed: {result.error}")

        # Extract field if specified
        output = result.result
        if "field" in test_spec:
            for key in test_spec["field"].split("."):
                output = output.get(key) if isinstance(output, dict) else None

        return output

    def _compare(self, actual: Any, expected: Any, test_spec: dict[str, Any]) -> bool:
        """Compare actual vs expected with tolerance/regex support."""
        # Regex match
        if test_spec.get("match_type") == "regex":
            if not isinstance(expected, str):
                return False
            return bool(re.search(expected, str(actual)))

        # Numeric tolerance
        if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
            tolerance = test_spec.get("tolerance", self.default_tolerance)
            return abs(actual - expected) <= tolerance

        # Exact match
        return actual == expected

    def _save_results(self, suite_result: SuiteResult) -> None:
        """Save suite results as JSON artifact."""
        artifact_path = (
            self.results_dir
            / f"{suite_result.suite_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        data = {
            "suite_name": suite_result.suite_name,
            "timestamp": suite_result.timestamp,
            "total": suite_result.total,
            "passed": suite_result.passed,
            "failed": suite_result.failed,
            "success_rate": suite_result.success_rate,
            "duration_ms": suite_result.duration_ms,
            "results": [
                {
                    "test_name": r.test_name,
                    "passed": r.passed,
                    "expected": r.expected,
                    "actual": r.actual,
                    "error": r.error,
                    "duration_ms": r.duration_ms,
                    "tags": r.tags,
                }
                for r in suite_result.results
            ],
        }

        with open(artifact_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Results saved to: {artifact_path}")
