from .ast_checks import function_exists, check_signature, has_return_statement, check_open_mode, check_file_closed
from.preprocessor import inject_into_code
from .io_formatter import format_param_list
import numpy as np

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
                        f"Expected: {format_param_list(expected)!r}",
                        f"Received: {format_param_list(actual)!r}"
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
import copy

def validate_function_run(student_module, reference_module, config, unit_test=False):
    
    errors = []

    for function_name, data in config.items():
        
        runtime = data.get("runtime")
        
        if runtime is None:
            continue
        
        student_func = getattr(student_module, function_name)
        reference_func = getattr(reference_module, function_name)

        for i, case in enumerate(runtime["cases"]):
            
            args = case["input"]
            reference_args = copy.deepcopy(args) # the deepcopy is especially needed when handling dictionaries
            student_args = copy.deepcopy(args)
            
            
            # ---------- handle injection into both student and reference ----------
            if "inject" in case:
                
                try:
                    inject_config = case["inject"]
                    substring = inject_config["substring"]
                    code_to_inject = inject_config["code"]
                    before = inject_config.get("before", True)
                    after = inject_config.get("after", None)
                    
                    # Inject into student code
                    try:
                        student_module_name = inject_into_code(
                            student_module,
                            substring,
                            code_to_inject,
                            before,
                            after
                        )
                    except Exception as e:
                        errors.append({
                            "heading": "Injection Error",
                            "function": function_name,
                            "details": [
                                f"Injection failed in STUDENT code ({student_module.__name__})",
                                f"Error: {e}"
                            ]
                        })
                        break
                    
                    # Inject into reference code
                    try:
                        reference_module_name = inject_into_code(
                            reference_module,
                            substring,
                            code_to_inject,
                            before,
                            after
                        )
                    except Exception as e:
                        errors.append({
                            "heading": "Injection Error",
                            "function": function_name,
                            "details": [
                                f"Injection failed in REFERENCE code ({reference_module.__name__})",
                                f"Error: {e}"
                            ]
                        })
                        break
                    
                    # Reload both modules
                    student_module = importlib.reload(student_module)
                    reference_module = importlib.reload(reference_module)
                    student_func = getattr(student_module, function_name)
                    reference_func = getattr(reference_module, function_name)
                    
                except Exception as e:
                    errors.append({
                        "heading": "Injection Error",
                        "function": function_name,
                        "details": [f"Injection failed: {e}"]
                    })
                    break
            
            
            if "expected" not in case or case["expected"] is None:
                try:
                    expected = reference_func(*reference_args)
                except Exception as e:
                    errors.append({
                        "heading": "Solution Error",
                        "function": function_name,
                        "details": [f"The reference solution crashed: {e}"]
                    })
                    break
            else:
                expected = case["expected"]
            
            
            try:
                actual = student_func(*student_args)
            except Exception as e:
                formatted_args = repr(args[0]) if len(args) == 1 else repr(args)
                errors.append({
                    "heading": "Runtime Error",
                    "function": function_name,
                    "details": [
                        f"When calling {function_name}({formatted_args})",
                        f"Your code crashed: {e}"
                    ]
                })
                break
            
            
            if not values_equal(actual, expected):
                formatted_args = repr(args[0]) if len(args) == 1 else repr(args)
                errors.append({
                    "heading": case.get("feedback", "Incorrect return value."),
                    "function": function_name,
                    "details": [
                        f"When calling {function_name}({formatted_args})",
                        f"Expected: {expected!r}",
                        f"Received: {actual!r}"
                    ]
                })
                break

    return errors

def values_equal(actual, expected):
    """
    Compare two values with proper type handling.
    Returns True if values are equal, False otherwise.
    """
    
    # Handle None
    if actual is None or expected is None:
        return actual is None and expected is None
    
    # Handle NumPy arrays
    if isinstance(actual, np.ndarray) and isinstance(expected, np.ndarray):
        return np.array_equal(actual, expected)
    
    # Handle mixed array/non-array
    if isinstance(actual, np.ndarray) or isinstance(expected, np.ndarray):
        return False
    
    # Handle lists and tuples with recursion
    if isinstance(actual, (list, tuple)) and isinstance(expected, (list, tuple)):
        if len(actual) != len(expected):
            return False
        for i in range(len(actual)):
            if not values_equal(actual[i], expected[i]):
                return False
        return True
    
    # Handle dictionaries
    if isinstance(actual, dict) and isinstance(expected, dict):
        if len(actual) != len(expected):
            return False
        for key in actual:
            if key not in expected:
                return False
            if not values_equal(actual[key], expected[key]):
                return False
        return True
    
    # Handle everything else
    return actual == expected