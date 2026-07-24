import pytest
import warnings

_markers = ['name', 'description', 'weight']

for marker in _markers:
    if not hasattr(pytest.mark, marker):
        # Create a dummy marker that does nothing
        setattr(pytest.mark, marker, lambda *args, **kwargs: lambda f: f)

# Suppress warnings about unknown marks
warnings.filterwarnings("ignore", category=pytest.PytestUnknownMarkWarning)