import pytest
import warnings

_markers = ['name', 'description', 'weight']

def _dummy_marker(*args, **kwargs):
    return lambda f: f

pytest.mark.name = _dummy_marker
pytest.mark.description = _dummy_marker
pytest.mark.weight = _dummy_marker

# Suppress warnings about unknown marks
warnings.filterwarnings("ignore", category=pytest.PytestUnknownMarkWarning)