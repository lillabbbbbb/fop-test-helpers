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
    
    Config format:
    {
        "test_type": "io",
        "function_name": {
            "structure": {...},
            "runtime": {
                "cases": [
                    {
                        "inputs": ["42"],      # Simulated user input
                        "args": ("prompt",),   # Function arguments
                        "check_output": True,  # ← NEW: Check print() output
                        "feedback": "Error message"
                    }
                ]
            }
        }
    }
    """
    errors = []
    
    for function_name, data in config.items():
        # Skip functions that are not IO tests
        if data.get("test_type") != "io":
            continue
        
        # Skip if not a runtime test
        runtime = data.get("runtime")
        if runtime is None:
            continue
        
        # Get functions
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
            inputs = case.get("inputs", [])
            args = case.get("args", ())
            feedback = case.get("feedback", f"Test case {case_index + 1} failed")
            check_output = case.get("check_output", True)  # ← NEW: Default to True
            
            # ===== SET UP INPUT MOCK =====
            input_queue = list(inputs)
            original_input = builtins.input
            
            def mock_input(prompt=""):
                if input_queue:
                    return input_queue.pop(0)
                return ""
            
            # ===== SET UP OUTPUT CAPTURE =====
            student_output = io.StringIO()
            reference_output = io.StringIO()
            original_stdout = sys.stdout
            
            try:
                # ===== RUN REFERENCE =====
                builtins.input = mock_input
                sys.stdout = reference_output
                expected_return = reference_func(*args)
                expected_output = reference_output.getvalue()
                
                # ===== RESET INPUT QUEUE =====
                input_queue = list(inputs)
                
                # ===== RUN STUDENT =====
                builtins.input = mock_input
                sys.stdout = student_output
                actual_return = student_func(*args)
                actual_output = student_output.getvalue()
                
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
                
                # ===== COMPARE OUTPUT (if check_output is True) =====
                if check_output and actual_output != expected_output:
                    errors.append({
                        "heading": "Incorrect output",
                        "function": function_name,
                        "details": [
                            f"Inputs: {inputs}",
                            f"Expected output: {expected_output!r}",
                            f"Received output: {actual_output!r}"
                        ]
                    })
                
            except Exception as e:
                errors.append({
                    "heading": "Runtime Error",
                    "function": function_name,
                    "details": [
                        f"With inputs {inputs}: {e}"
                    ]
                })
            finally:
                builtins.input = original_input
                sys.stdout = original_stdout
    
    return errors