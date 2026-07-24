import pytest
from .ast_checks import function_exists, check_signature, has_return_statement, check_open_mode, check_file_closed

def validate_function_structure(
    filename,
    config
):
    
    
    errors = []

    for function_name, data in config.items():
        
        structure = data.get("structure", {})

        # ---------- existence ----------

        if not function_exists(filename, function_name):
            errors.append({
                "heading": "Incorrect function structure",
                "function": function_name,
                "details": [
                    f"Could not find '{function_name}()' function."
                ]
            })
            continue

        # ---------- parameters ----------

        expected_params = structure.get("params")

        if expected_params is not None:
            matches, actual, expected = check_signature(
                filename,
                function_name,
                expected_params,
            )

            if not matches:
                errors.append({
                    "heading": "Incorrect function structure",
                    "function": function_name,
                    "details": [
                        f"'{function_name}()' has incorrect parameters.",
                        f"Expected: {expected!r}",
                        f"Received: {actual!r}"
                    ]
                })
                continue
            
        # ---------- return ----------

        if structure.get("must_return", False):

            if not has_return_statement(
                filename,
                function_name
            ):
                errors.append({
                    "heading": "Incorrect function structure",
                    "function": function_name,
                    "details": [
                        "The function should return a value."
                    ]
                })
        
        
        # ---------- open mode ----------
        
        expected_mode = structure.get("open_mode")

        if expected_mode is not None:

            matches, actual = check_open_mode(
                filename,
                function_name,
                expected_mode
            )

            if not matches:

                errors.append({
                    "heading": "Incorrect file mode",
                    "function": function_name,
                    "details": [
                        f"Expected open(..., {expected_mode!r})",
                        f"Found: {actual!r}"
                    ]
                })

                
        # ---------- file closed ----------

        found_open, properly_closed = check_file_closed(
            filename,
            function_name
        )

        if found_open and not properly_closed:

            errors.append({
                "heading": "File not closed",
                "function": function_name,
                "details": [
                    "Any file opened with open() should be closed using close()."
                ]
            })

    return errors

import random
import pytest
from .error_collector import ErrorCollector
from .io_formatter import format_errors

def validate_function_run(student_module, reference_module, config, unit_test=False):
    """
    Validate functions against test cases.
    
    Args:
        student_module: Student's solution module
        reference_module: Reference solution module
        config: Test configuration dictionary
        unit_test: If True, generates individual pytest tests (one per equivalence class).
                 If False, returns errors list directly.
    
    Returns:
        list: List of error dictionaries (empty if all tests pass)
    """
    
    if unit_test:
        ErrorCollector.reset()
    
    errors = []

    for function_name, data in config.items():
        
        runtime = data.get("runtime")
        
        if runtime is None:
            continue

        student_func = getattr(student_module, function_name)
        reference_func = getattr(reference_module, function_name)

        for i, case in enumerate(runtime["cases"]):
            
            random.seed(12345)
            args = case["input"]
            descr = case.get("description", f"Case {i}")
            formatted_args = repr(args[0]) if len(args) == 1 else repr(args)
            
            # ================================================================
            # UNIT TEST MODE: Generate ONE pytest test per equivalence class
            # ================================================================
            if unit_test:
                
                @pytest.mark.parametrize('_', [None])
                @pytest.mark.name(f"Test {function_name}() - {descr}")
                @pytest.mark.description(f"Check {function_name}() behavior: {descr}")
                @pytest.mark.weight(case.get("weight", 1))
                def test_case(_=None, 
                             fn=function_name, 
                             a=args, 
                             c=case,
                             f_args=formatted_args,
                             student_mod=student_module,
                             ref_mod=reference_module):
                    
                    random.seed(12345)
                    student_func = getattr(student_mod, fn)
                    reference_func = getattr(ref_mod, fn)
                    
                    # Run the test for this equivalence class
                    try:
                        expected = reference_func(*a)
                    except Exception as e:
                        try:
                            student_func(*a)
                            error = {
                                "heading": c.get('feedback', f'Expected exception: {descr}'),
                                "function": fn,
                                "details": [
                                    f"When calling {fn}({f_args})",
                                    f"Expected: {type(e).__name__}",
                                    f"Received: No exception"
                                ]
                            }
                            ErrorCollector.add_error(error)
                            ErrorCollector.increment_total()
                            pytest.fail(format_errors([error]))
                        except Exception:
                            ErrorCollector.increment_total()
                            ErrorCollector.add_passed()
                            return
                    
                    try:
                        actual = student_func(*a)
                    except Exception as e:
                        error = {
                            "heading": c.get('feedback', f'Runtime Error: {descr}'),
                            "function": fn,
                            "details": [
                                f"When calling {fn}({f_args})",
                                f"Your code crashed: {e}"
                            ]
                        }
                        ErrorCollector.add_error(error)
                        ErrorCollector.increment_total()
                        pytest.fail(format_errors([error]))
                        return
                    
                    if actual != expected:
                        error = {
                            "heading": c.get('feedback', f'Incorrect return value: {descr}'),
                            "function": fn,
                            "details": [
                                f"When calling {fn}({f_args})",
                                f"Expected: {expected!r}",
                                f"Received: {actual!r}"
                            ]
                        }
                        ErrorCollector.add_error(error)
                        ErrorCollector.increment_total()
                        pytest.fail(format_errors([error]))
                        return
                    
                    ErrorCollector.increment_total()
                    ErrorCollector.add_passed()
                
                # Register the test with unique name
                test_name = f"test_{function_name}_case_{i}"
                globals()[test_name] = test_case
                
                # Continue to next test case
                continue
            
            # ================================================================
            # DIRECT MODE: Collect errors immediately (no pytest)
            # ================================================================
            
            try:
                expected = reference_func(*args)
            except Exception as e:
                errors.append({
                    "heading": "Solution Error",
                    "function": function_name,
                    "details": [f"The reference solution crashed: {e}"]
                })
                continue
            
            try:
                actual = student_func(*args)
            except Exception as e:
                errors.append({
                    "heading": "Runtime Error",
                    "function": function_name,
                    "details": [
                        f"When calling {function_name}({formatted_args})",
                        f"Your code crashed: {e}"
                    ]
                })
                continue
            
            if actual != expected:
                errors.append({
                    "heading": case.get("feedback", "Incorrect return value."),
                    "function": function_name,
                    "details": [
                        f"When calling {function_name}({formatted_args})",
                        f"Expected: {expected!r}",
                        f"Received: {actual!r}"
                    ]
                })
    
    if not unit_test:
        return errors
    
    # In unit_test mode, errors are collected during test execution
    return []


def run_validation(student_module, reference_module, config):
    """
    Run validation directly (non-pytest mode)
    Returns: (passed, errors, formatted_output)
    """
    errors = validate_function_run(
        student_module, 
        reference_module, 
        config, 
        unit_test=False
    )
    
    passed = len(errors) == 0
    formatted = format_errors(errors)
    
    return passed, errors, formatted