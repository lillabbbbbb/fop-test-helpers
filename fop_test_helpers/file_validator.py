from .file_helpers import (
    create_temp_text,
    read_text,
    remove_file
)
from .io_formatter import format_file_contents

def validate_file_return(
    student_module,
    reference_module,
    config
):

    errors = []

    for function_name, data in config.items():

        runtime = data.get("runtime")

        if runtime is None:
            continue
        
         # Get structure to check must_return
        structure = data.get("structure", {})
        must_return = structure.get("must_return", False)
        
        # Skip this validator if function doesn't need to return anything
        if not must_return:
            continue

        student_func = getattr(student_module, function_name)
        reference_func = getattr(reference_module, function_name)

        for case in runtime["cases"]:
            
            file_content = case.get("file", "")
            additional_args = case.get("input", ())
            
            # Convert to tuple if needed
            if not isinstance(additional_args, tuple):
                additional_args = (additional_args,)
            
            # ===== HANDLE SPECIAL MARKERS =====
            using_missing = False
            if file_content == "__MISSING__":
                # File should NOT exist - create a path that doesn't exist
                # Since create_temp_text would create a file, we need to handle differently
                student_file = "/tmp/nonexistent_file_12345.txt"
                reference_file = "/tmp/nonexistent_file_12345.txt"
                using_missing = True
                
                # Ensure file doesn't exist
                import os
                if os.path.exists(student_file):
                    os.remove(student_file)
                    
            else:
                student_file = create_temp_text(file_content)
                reference_file = create_temp_text(file_content)

            try:
                if "expected" not in case or case["expected"] is None:
                    try:
                        expected = reference_func(reference_file, *additional_args)
                    except Exception as e:
                        errors.append({
                            "heading": "Solution Error",
                            "function": function_name,
                            "details": [f"The reference solution crashed: {e}"]
                        })
                        break
                else:
                    expected = case["expected"]
                
                    actual = student_func(student_file, *additional_args)

                    if actual != expected:

                        errors.append({
                            "heading": case.get(
                                "feedback",
                                "Incorrect return value."
                            ),
                            "function": function_name,
                            "details": [
                                f"When calling {function_name}()",
                                f"Expected: {expected!r}",
                                f"Received: {actual!r}",
                                *format_file_contents(
                                    "Input file",
                                    file_content
                                )
                            ]
                        })
                        break
            except Exception as e:
                # ✅ Catch errors and report them as failures
                errors.append({
                    "heading": "Runtime Error",
                    "function": function_name,
                    "details": [
                        f"Student code crashed when calling {function_name}(): {e}",
                        *format_file_contents("Input file", file_content)
                    ]
                })
                break
            finally:
                if not using_missing:
                    remove_file(student_file)
                    remove_file(reference_file)

    return errors


def validate_file_side_effect(
    student_module,
    reference_module,
    config
):

    errors = []

    for function_name, data in config.items():

        runtime = data.get("runtime")

        if runtime is None:
            continue

        student_func = getattr(student_module, function_name)
        reference_func = getattr(reference_module, function_name)

        for case in runtime["cases"]:

            file_content = case["file"]
            additional_args = case.get("input", ())
            
            if not isinstance(additional_args, tuple):
                additional_args = (additional_args,)
                
            # ===== HANDLE SPECIAL MARKERS =====
            using_missing = False
            if file_content == "__MISSING__":
                # File should NOT exist
                student_file = "/tmp/nonexistent_file_12345.txt"
                reference_file = "/tmp/nonexistent_file_12345.txt"
                using_missing = True
                
                # Ensure file doesn't exist
                import os
                if os.path.exists(student_file):
                    os.remove(student_file)
            else:
                student_file = create_temp_text(file_content)
                reference_file = create_temp_text(file_content)

            try:

                reference_func(reference_file, *additional_args)
                student_func(student_file, *additional_args)

                # ===== ONLY CHECK FILE CONTENTS IF NOT A MISSING FILE TEST =====
                if not using_missing:
                    expected = read_text(reference_file)
                    actual = read_text(student_file)

                    if expected != actual:

                        errors.append({
                            "heading": case.get(
                                "feedback",
                                "Incorrect file contents."
                            ),
                            "function": function_name,
                            "details": [
                                *format_file_contents("Input file", case["file"]),
                                *format_file_contents("Expected file", expected),
                                *format_file_contents("Your file", actual),
                            ]
                        })
                        break
            except Exception as e:
                # ✅ Catch errors and report them as failures
                errors.append({
                    "heading": "Runtime Error",
                    "function": function_name,
                    "details": [
                        f"Student code crashed when calling {function_name}(): {e}",
                        *format_file_contents("Input file", file_content)
                    ]
                })
                break
            finally:
                if not using_missing:
                    remove_file(student_file)
                    remove_file(reference_file)

    return errors


import os
from .file_helpers import (
    create_temp_directory,
    remove_temp_directory,
    read_text
)

def validate_created_files(
    student_module,
    reference_module,
    config
):

    errors = []

    for function_name, data in config.items():

        runtime = data.get("runtime")

        if runtime is None:
            continue

        student_func = getattr(student_module, function_name)
        reference_func = getattr(reference_module, function_name)

        for case in runtime["cases"]:
            
            additional_args = case.get("input", ())
            
            if not isinstance(additional_args, tuple):
                additional_args = (additional_args,)
                
            # Get output file path
            output_file = case.get("output_file", "output.txt")

            student_dir = create_temp_directory()
            reference_dir = create_temp_directory()
            
            # If there's initial file content, write it to both directories
            file_content = case.get("file", "")
            
            if file_content:
                student_file_path = os.path.join(student_dir, "input.txt")
                reference_file_path = os.path.join(reference_dir, "input.txt")
                with open(student_file_path, 'w') as f:
                    f.write(file_content)
                with open(reference_file_path, 'w') as f:
                    f.write(file_content)


            old_cwd = os.getcwd()

            try:

                os.chdir(reference_dir)
                reference_func(reference_file_path, *additional_args) if file_content else reference_func(*additional_args)

                os.chdir(student_dir)
                student_func(student_file_path, *additional_args) if file_content else student_func(*additional_args)

                expected = read_text(
                    os.path.join(reference_dir, case["output_file"])
                )

                actual = read_text(
                    os.path.join(student_dir, case["output_file"])
                )

                if expected != actual:

                    errors.append({
                        "heading": case.get(
                            "feedback",
                            "Incorrect file output."
                        ),
                        "function": function_name,
                        "details": [
                            f"Output file: {case['output_file']}",
                            *format_file_contents("Expected file", expected),
                            *format_file_contents("Your file", actual),
                        ]
                    })

            finally:

                os.chdir(old_cwd)

                remove_temp_directory(student_dir)
                remove_temp_directory(reference_dir)

    return errors