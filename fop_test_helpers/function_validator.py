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

def validate_function_run(student_module, reference_module, config, unit_test=False):
    
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
            
            
            # Always collect errors
            random.seed(12345)
            try:
                expected = reference_func(*args)
            except Exception as e:
                errors.append({
                    "heading": "Solution Error",
                    "function": function_name,
                    "details": [f"The reference solution crashed: {e}"]
                })
                break
            
            try:
                actual = student_func(*args)
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
            
            if actual != expected:
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