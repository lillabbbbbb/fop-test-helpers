# lib/test_helpers.py
import random
import pytest

# Try to import from cg_pytest_reporter, but fallback to dummy markers
try:
    from cg_pytest_reporter import name, description, weight
    print("✅ Using cg_pytest_reporter")
except ImportError:
    print("⚠️ cg_pytest_reporter not found, using dummy markers")
    # Create dummy markers
    def name(n): return lambda f: f
    def description(d): return lambda f: f
    def weight(w): return lambda f: f

from .error_collector import ErrorCollector
from .io_formatter import format_errors

def run_tests(student_module, reference_module, config, use_pytest=False):
    """
    Run tests against student code.
    
    Args:
        student_module: Student's solution module
        reference_module: Reference solution module
        config: Test configuration dictionary
        use_pytest: If True, generates individual pytest tests (one per equivalence class).
                  If False, returns errors list directly.
    
    Returns:
        dict: {
            'passed': bool or None,
            'errors': list,
            'test_count': int,
            'mode': 'pytest' or 'direct'
        }
    """
    
    if use_pytest:
        ErrorCollector.reset()
        test_count = 0
        
        for function_name, data in config.items():
            runtime = data.get("runtime")
            if runtime is None:
                continue
            
            for i, case in enumerate(runtime["cases"]):
                test_count += 1
                _register_individual_test(
                    student_module, reference_module, 
                    function_name, case, i
                )
        
        return {
            'passed': None,
            'errors': [],
            'test_count': test_count,
            'mode': 'pytest'
        }
    
    # Direct mode - run immediately
    errors = []
    for function_name, data in config.items():
        runtime = data.get("runtime")
        if runtime is None:
            continue
        
        for case in runtime["cases"]:
            error = _run_single_test_direct(
                student_module, reference_module,
                function_name, case
            )
            if error:
                errors.append(error)
    
    return {
        'passed': len(errors) == 0,
        'errors': errors,
        'test_count': len(errors),
        'mode': 'direct'
    }


def _register_individual_test(student_module, reference_module, function_name, case, index):
    """
    Register a single individual pytest test with its own feedback.
    Each test case becomes a separate test with its own name and output.
    """
    args = case["input"]
    descr = case.get("description", f"Case {index}")
    feedback = case.get("feedback", f"Test case {index}")
    formatted_args = repr(args[0]) if len(args) == 1 else repr(args)
    
    # Create a unique test name based on the description
    test_name = f"test_{function_name}_{descr.replace(' ', '_')[:30]}"
    
    @pytest.mark.parametrize('_', [None])
    @pytest.mark.name(f"Test {function_name}(): {descr}")
    @pytest.mark.description(f"Check {function_name}() behavior: {descr}")
    @pytest.mark.weight(case.get("weight", 1))
    def test_case(_=None):
        random.seed(12345)
        student_func = getattr(student_module, function_name)
        reference_func = getattr(reference_module, function_name)
        
        # Run the test for this equivalence class
        try:
            expected = reference_func(*args)
        except Exception as e:
            try:
                student_func(*args)
                # Student didn't raise exception when it should have
                error = {
                    "heading": f"Expected exception not raised: {descr}",
                    "function": function_name,
                    "details": [
                        f"When calling {function_name}({formatted_args})",
                        f"Expected: {type(e).__name__}",
                        f"Received: No exception (function returned successfully)"
                    ]
                }
                ErrorCollector.add_error(error)
                ErrorCollector.increment_total()
                # This will show the error for THIS specific test
                pytest.fail(format_errors([error]))
            except Exception:
                # Both raised exceptions - correct behavior
                ErrorCollector.increment_total()
                ErrorCollector.add_passed()
                return
        
        try:
            actual = student_func(*args)
        except Exception as e:
            error = {
                "heading": feedback,
                "function": function_name,
                "details": [
                    f"When calling {function_name}({formatted_args})",
                    f"Your code crashed: {e}"
                ]
            }
            ErrorCollector.add_error(error)
            ErrorCollector.increment_total()
            # This will show the error for THIS specific test
            pytest.fail(format_errors([error]))
            return
        
        if actual != expected:
            error = {
                "heading": feedback,
                "function": function_name,
                "details": [
                    f"When calling {function_name}({formatted_args})",
                    f"Expected: {expected!r}",
                    f"Received: {actual!r}"
                ]
            }
            ErrorCollector.add_error(error)
            ErrorCollector.increment_total()
            # This will show the error for THIS specific test
            pytest.fail(format_errors([error]))
            return
        
        # Test passed for this equivalence class
        ErrorCollector.increment_total()
        ErrorCollector.add_passed()
        print(f"✅ {descr} - PASSED")
    
    # Register the test with a unique name
    globals()[test_name] = test_case


def _run_single_test_direct(student_module, reference_module, function_name, case):
    """Run a single test case and return error or None (direct mode)"""
    args = case["input"]
    formatted_args = repr(args[0]) if len(args) == 1 else repr(args)
    
    try:
        expected = getattr(reference_module, function_name)(*args)
    except Exception as e:
        return {
            "heading": "Solution Error",
            "function": function_name,
            "details": [f"The reference solution crashed: {e}"]
        }
    
    try:
        actual = getattr(student_module, function_name)(*args)
    except Exception as e:
        return {
            "heading": "Runtime Error",
            "function": function_name,
            "details": [
                f"When calling {function_name}({formatted_args})",
                f"Your code crashed: {e}"
            ]
        }
    
    if actual != expected:
        return {
            "heading": case.get("feedback", "Incorrect return value."),
            "function": function_name,
            "details": [
                f"When calling {function_name}({formatted_args})",
                f"Expected: {expected!r}",
                f"Received: {actual!r}"
            ]
        }
    
    return None