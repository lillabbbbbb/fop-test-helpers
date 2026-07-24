# tasks/task1_leap_year/conftest.py
import pytest

def pytest_configure(config):
    """Register custom markers to avoid warnings."""
    config.addinivalue_line("markers", "name: Set the name of the test")
    config.addinivalue_line("markers", "description: Set the description of the test")
    config.addinivalue_line("markers", "weight: Set the weight/priority of the test")