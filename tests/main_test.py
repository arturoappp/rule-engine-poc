import sys
import os
import pytest


def main():
    """Run all tests with pytest and generate coverage report"""
    # Add the project root to Python path to make imports work
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)

    args = [
        # Show verbose output
        "-v",
        # Generate coverage report
        "--cov-report", "term-missing",
        # Coverage for app and rule_engine modules
        "--cov=app", "--cov=rule_engine",
        # The directory where tests are located
        os.path.dirname(os.path.abspath(__file__))
    ]

    # Add any command line arguments passed to this script
    args.extend(sys.argv[1:])

    # Run pytest with the configured arguments
    return pytest.main(args)


if __name__ == "__main__":
    sys.exit(main())