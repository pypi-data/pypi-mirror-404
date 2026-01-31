"""
CLI for Evaluation Framework

Usage:
    python -m orchestrator.evaluation.cli run <suite_path> [--tags tag1,tag2]
    python -m orchestrator.evaluation.cli list <directory>
"""

import argparse
import sys
from pathlib import Path
from typing import Any

from .runner import EvaluationRunner


def run_suite(args: Any) -> int:
    """Run evaluation suite from file."""
    # Import here to avoid circular dependencies
    from orchestrator.server.app import app
    from orchestrator.skills.skill_executor import get_executor

    client = app.test_client()
    executor = get_executor()

    runner = EvaluationRunner(api_client=client, skill_executor=executor)

    tags = args.tags.split(",") if args.tags else None
    result = runner.run_suite(args.suite_path, tags=tags)

    # Print summary
    print("\n" + "=" * 60)
    print(f"Suite: {result.suite_name}")
    print("=" * 60)
    print(f"Total:   {result.total}")
    print(f"Passed:  {result.passed} ✅")
    print(f"Failed:  {result.failed} ❌")
    print(f"Success: {result.success_rate:.1f}%")
    print(f"Duration: {result.duration_ms:.0f}ms")
    print("=" * 60)

    # Print failures
    if result.failed > 0:
        print("\nFailed Tests:")
        for r in result.results:
            if not r.passed:
                print(f"  ❌ {r.test_name}")
                if r.error:
                    print(f"     Error: {r.error}")
                else:
                    print(f"     Expected: {r.expected}")
                    print(f"     Actual:   {r.actual}")

    return 0 if result.failed == 0 else 1


def list_suites(args: Any) -> int:
    """List available evaluation suites in directory."""
    directory = Path(args.directory)
    if not directory.exists():
        print(f"Directory not found: {directory}")
        return 1

    suites = (
        list(directory.glob("**/*.yaml"))
        + list(directory.glob("**/*.yml"))
        + list(directory.glob("**/*.json"))
    )

    if not suites:
        print(f"No suites found in {directory}")
        return 0

    print(f"\nAvailable Suites in {directory}:")
    print("=" * 60)
    for suite in sorted(suites):
        rel_path = suite.relative_to(directory)
        print(f"  - {rel_path}")
    print("=" * 60)
    print(f"Total: {len(suites)} suite(s)")

    return 0


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="ToolWeaver Evaluation Framework CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run evaluation suite")
    run_parser.add_argument("suite_path", help="Path to suite YAML/JSON file")
    run_parser.add_argument("--tags", help="Comma-separated tags to filter tests")

    # List command
    list_parser = subparsers.add_parser("list", help="List available suites")
    list_parser.add_argument(
        "directory", default="benchmarks/task_suites", nargs="?", help="Directory to search"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "run":
        return run_suite(args)
    elif args.command == "list":
        return list_suites(args)
    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
