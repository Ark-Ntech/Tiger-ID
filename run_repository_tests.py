#!/usr/bin/env python3
"""Test runner for repository pattern and ServiceFactory tests.

This script provides an easy way to run all tests related to the
repository pattern refactoring and ServiceFactory implementation.
"""

import sys
import subprocess
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(message):
    """Print a colored header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}\n")


def print_success(message):
    """Print a success message."""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_error(message):
    """Print an error message."""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")


def print_info(message):
    """Print an info message."""
    print(f"{Colors.OKCYAN}ℹ {message}{Colors.ENDC}")


def run_command(cmd, description):
    """Run a command and return success status."""
    print_info(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, capture_output=False, text=True)

    if result.returncode == 0:
        print_success(f"{description} passed")
        return True
    else:
        print_error(f"{description} failed")
        return False


def main():
    """Main test runner."""
    print_header("Repository Pattern and ServiceFactory Test Suite")

    # Get project root
    project_root = Path(__file__).parent

    # Test suites
    test_suites = [
        {
            "name": "Service Repository Pattern Tests",
            "description": "Verify services use repositories correctly",
            "paths": [
                "tests/test_services/test_facility_service_repository.py",
                "tests/test_services/test_investigation_service_repository.py",
            ]
        },
        {
            "name": "ServiceFactory Route Tests",
            "description": "Verify routes use ServiceFactory",
            "paths": [
                "tests/test_routes/test_service_factory_routes.py",
            ]
        },
        {
            "name": "Repository Pattern Enforcement",
            "description": "Scan codebase for pattern violations",
            "paths": [
                "tests/test_services/test_repository_pattern_enforcement.py",
            ]
        },
        {
            "name": "Base Repository Tests",
            "description": "Test generic repository operations",
            "paths": [
                "tests/test_repositories/test_base_repository.py",
            ]
        },
    ]

    # Check if running all tests or specific suite
    if len(sys.argv) > 1:
        suite_name = sys.argv[1]
        test_suites = [s for s in test_suites if suite_name.lower() in s["name"].lower()]

        if not test_suites:
            print_error(f"No test suite matching '{suite_name}' found")
            print_info("Available suites:")
            for suite in test_suites:
                print(f"  - {suite['name']}")
            return 1

    results = []

    # Run each test suite
    for suite in test_suites:
        print_header(suite["name"])
        print(f"Description: {suite['description']}\n")

        # Check if test files exist
        missing_files = []
        for path in suite["paths"]:
            full_path = project_root / path
            if not full_path.exists():
                missing_files.append(path)

        if missing_files:
            print_error("Missing test files:")
            for file in missing_files:
                print(f"  - {file}")
            results.append(False)
            continue

        # Run tests
        cmd = ["pytest"] + suite["paths"] + ["-v", "--tb=short"]

        success = run_command(cmd, suite["name"])
        results.append(success)

    # Summary
    print_header("Test Summary")

    total = len(results)
    passed = sum(results)
    failed = total - passed

    print(f"Total suites: {total}")
    print_success(f"Passed: {passed}")

    if failed > 0:
        print_error(f"Failed: {failed}")
        return 1
    else:
        print_success("All test suites passed!")
        return 0


def run_all_with_coverage():
    """Run all tests with coverage report."""
    print_header("Running All Tests with Coverage")

    cmd = [
        "pytest",
        "tests/test_services/test_facility_service_repository.py",
        "tests/test_services/test_investigation_service_repository.py",
        "tests/test_routes/test_service_factory_routes.py",
        "tests/test_services/test_repository_pattern_enforcement.py",
        "tests/test_repositories/test_base_repository.py",
        "--cov=backend.services",
        "--cov=backend.repositories",
        "--cov-report=html",
        "--cov-report=term-missing",
        "-v"
    ]

    success = run_command(cmd, "All tests with coverage")

    if success:
        print_info("Coverage report generated at: htmlcov/index.html")

    return 0 if success else 1


def run_enforcement_only():
    """Run only the enforcement tests."""
    print_header("Repository Pattern Enforcement Tests")

    cmd = [
        "pytest",
        "tests/test_services/test_repository_pattern_enforcement.py",
        "-v",
        "--tb=short"
    ]

    success = run_command(cmd, "Enforcement tests")
    return 0 if success else 1


if __name__ == "__main__":
    # Check for special commands
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "coverage":
            sys.exit(run_all_with_coverage())
        elif command == "enforce":
            sys.exit(run_enforcement_only())
        elif command == "help":
            print("Repository Pattern Test Runner")
            print("\nUsage:")
            print("  python run_repository_tests.py              # Run all test suites")
            print("  python run_repository_tests.py <suite>      # Run specific suite")
            print("  python run_repository_tests.py coverage     # Run with coverage report")
            print("  python run_repository_tests.py enforce      # Run enforcement tests only")
            print("  python run_repository_tests.py help         # Show this help")
            print("\nAvailable suites:")
            print("  - service")
            print("  - route")
            print("  - enforcement")
            print("  - repository")
            sys.exit(0)

    sys.exit(main())
