# lib/pytest_fixtures.py
"""
Shared pytest fixtures
"""
import pytest
from .error_collector import ErrorCollector
from .formatters import format_errors, format_summary

@pytest.fixture(scope="session", autouse=True)
def print_collected_errors():
    """Print all collected errors after pytest runs"""
    yield
    errors = ErrorCollector.get_errors()
    summary = ErrorCollector.get_summary()
    
    if errors:
        print("\n" + format_summary(summary))
        print("\n" + "=" * 60)
        print("FAILURE DETAILS")
        print("=" * 60)
        print(format_errors(errors))
        print("=" * 60)
    else:
        print("\n✅ All equivalence class tests passed!")


@pytest.fixture
def reset_error_collector():
    """Reset error collector before each test module"""
    ErrorCollector.reset()
    yield