import pytest

# This registers the markers that are used in CodeGrade
def pytest_configure(config):
    """Register custom markers to avoid warnings."""
    config.addinivalue_line("markers", "name: Set the name of the test")
    config.addinivalue_line("markers", "description: Set the description of the test")
    config.addinivalue_line("markers", "weight: Set the weight/priority of the test")
    
    
def pytest_collection_modifyitems(config, items):
    """
    Hook to ensure dynamically created tests are collected.
    This runs after pytest discovers tests.
    """
    # Any special handling needed for dynamic tests
    pass