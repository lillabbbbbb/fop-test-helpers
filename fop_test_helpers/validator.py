# fop_test_helpers/unified_validator.py
"""
Unified validator that routes to the appropriate validator(s) based on test_type.
"""

from typing import Dict, List
from .function_validator import validate_function_run
from .file_validator import validate_file_return, validate_file_side_effect, validate_created_files
from .io_validator import validate_io_function

def validate_solution(
    student_module,
    reference_module,
    config: Dict,
    is_unit_test=False
) -> List[Dict]:
    """
    Unified validator that routes to the appropriate validator(s).
    
    It looks at each function's "test_type" in the config:
        - "function" → validate_function_run()
        - "io" → validate_io_function()
        - "file" → validate_file_return(), validate_file_side_effect()
    
        If no test_type is specified, it auto-detects from the config.
    """
    errors = []
    
    # Detect test types for each function
    function_test_types = detect_test_type(config)
    
    for function_name, test_type in function_test_types.items():
        # Create sub-config for this function only
        function_config = {function_name: config[function_name]}
        
        if test_type == "io":
            # Use IO validator
            errors.extend(validate_io_function(
                student_module,
                reference_module,
                function_config
            ))
        
        elif test_type == "file":
            # Use file validators
            from .file_validator import (
                validate_file_return,
                validate_file_side_effect
            )
            errors.extend(validate_file_return(
                student_module,
                reference_module,
                function_config
            ))
            errors.extend(validate_file_side_effect(
                student_module,
                reference_module,
                function_config
            ))
        
        else:  # "function" or unknown
            # Use function validator
            errors.extend(validate_function_run(
                student_module,
                reference_module,
                function_config,
                unit_test=is_unit_test
            ))
    
    return errors


def detect_test_type(config: Dict) -> Dict[str, str]:
    """
    Detect test type for each function in the config.
    
    Returns:
        Dict: {"function_name": "test_type", ...}
    """
    result = {}
    
    for function_name, function_config in config.items():
        # Skip if not a function config
        if not isinstance(function_config, dict):
            continue
        
        # Check explicit test_type
        if "test_type" in function_config:
            result[function_name] = function_config["test_type"]
            continue
        
        # Auto-detect based on runtime cases
        runtime = function_config.get("runtime", {})
        cases = runtime.get("cases", [])
        
        for case in cases:
            if "file" in case:
                result[function_name] = "file"
                break
            elif "inputs" in case:
                result[function_name] = "io"
                break
            elif "input" in case or "expected" in case:
                result[function_name] = "function"
                break
        else:
            # Default to function if no cases or no match
            result[function_name] = "function"
    
    return result