# fop_test_helpers/io_validator.py
"""
IO Validator for functions that use input() and print()
"""

import builtins
import io
import sys
from typing import Dict, List, Any

def validate_io_function(
    student_module,
    reference_module,
    config: Dict
) -> List[Dict]:
    """
    Validate functions that use input() by mocking input and checking return value AND output.
    """
    errors = []
    
    for function_name, data in config.items():
        runtime = data.get("runtime")
        if runtime is None:
            continue
        
        is_io_test = data.get("test_type") == "io"
        
        if hasattr(student_module, function_name):
            student_func = getattr(student_module, function_name)
        else:
            errors.append({
                "heading": "Function not found",
                "function": function_name,
                "details": [f"Could not find '{function_name}()'"]
            })
            continue
        
        if hasattr(reference_module, function_name):
            reference_func = getattr(reference_module, function_name)
        else:
            errors.append({
                "heading": "Reference solution missing",
                "function": function_name,
                "details": [f"Reference solution for '{function_name}()' not found"]
            })
            continue
        
        for case_index, case in enumerate(runtime["cases"]):
            inputs = case.get("user_input", [])
            args = case.get("input", ())
            expected_output = case.get("expected", None)
            feedback = case.get("feedback", f"Test case {case_index + 1} failed")
            
            check_output = is_io_test or isinstance(expected_output, str)
            
            def create_input_queue():
                return list(inputs)
            
            original_input = builtins.input
            original_stdout = sys.stdout
            
            try:
                # ===== RUN REFERENCE =====
                input_queue = create_input_queue()
                
                def mock_input_ref(prompt=""):
                    sys.stdout.write(prompt)  # Print prompt to stdout
                    if input_queue:
                        return input_queue.pop(0)
                    raise EOFError("No more input available")
                
                reference_output = io.StringIO()
                builtins.input = mock_input_ref
                sys.stdout = reference_output
                
                expected_return = reference_func(*args)
                actual_output_ref = reference_output.getvalue()
                
                # ===== RUN STUDENT =====
                input_queue = create_input_queue()
                
                def mock_input_stu(prompt=""):
                    sys.stdout.write(prompt)  # Print prompt to stdout
                    if input_queue:
                        return input_queue.pop(0)
                    raise EOFError("No more input available")
                
                student_output = io.StringIO()
                builtins.input = mock_input_stu
                sys.stdout = student_output
                
                actual_return = student_func(*args)
                actual_output_stu = student_output.getvalue()
                
                # ===== COMPARE RETURN VALUES =====
                if actual_return != expected_return:
                    errors.append({
                        "heading": feedback,
                        "function": function_name,
                        "details": [
                            f"Inputs: {inputs}",
                            f"Expected return: {expected_return!r}",
                            f"Received return: {actual_return!r}"
                        ]
                    })
                    continue
                
                # ===== COMPARE OUTPUT =====
                if check_output and expected_output is not None:
                    if expected_output not in actual_output_stu:
                        errors.append({
                            "heading": "Incorrect output",
                            "function": function_name,
                            "details": [
                                f"Inputs: {inputs}",
                                f"Expected to find: {expected_output!r}",
                                f"Actual output: {actual_output_stu!r}"
                            ]
                        })
                        continue
                
                elif check_output and expected_output is None:
                    if actual_output_stu != actual_output_ref:
                        errors.append({
                            "heading": "Incorrect output",
                            "function": function_name,
                            "details": [
                                f"Inputs: {inputs}",
                                f"Expected output: {actual_output_ref!r}",
                                f"Received output: {actual_output_stu!r}"
                            ]
                        })
                        continue
                
            except EOFError as e:
                errors.append({
                    "heading": "Input Error",
                    "function": function_name,
                    "details": [
                        f"With inputs {inputs}: Not enough input provided",
                        f"Error: {e}"
                    ]
                })
                continue
            except Exception as e:
                errors.append({
                    "heading": "Runtime Error",
                    "function": function_name,
                    "details": [
                        f"With inputs {inputs}: {e}"
                    ]
                })
                continue
            finally:
                builtins.input = original_input
                sys.stdout = original_stdout
    
    return errors