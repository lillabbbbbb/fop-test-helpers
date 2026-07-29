# run_tests.py - Complete with unambiguous pass/fail logic

import sys
import importlib.util
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
import types
import shutil

# ===== PATHS =====
REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT))

# Private data (ignored by Git)
PRIVATE_DIR = REPO_ROOT / "private"
TASK_CONFIGS_DIR = PRIVATE_DIR / "task_configs"
MOCK_SUBMISSIONS_DIR = PRIVATE_DIR / "mock_submissions"
SOLUTIONS_DIR = PRIVATE_DIR / "solutions"
TEST_RESULTS_DIR = PRIVATE_DIR / "test_results"

# Import from public library
from fop_test_helpers.function_validator import validate_function_structure, validate_function_run
from fop_test_helpers.file_validator import validate_file_return, validate_file_side_effect, validate_created_files
from fop_test_helpers.io_formatter import format_errors

# Create directories
TEST_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ===== TERMINAL WIDTH =====
try:
    TERMINAL_WIDTH = shutil.get_terminal_size().columns
except:
    TERMINAL_WIDTH = 100


def print_header(title: str, char: str = "=", width: int = TERMINAL_WIDTH):
    """Print a centered header with custom width"""
    if width > 100:
        width = 100
    print(char * width)
    print(title.center(width))
    print(char * width)


# ===== NAMING PARSING =====

def detect_test_type(config: Dict) -> Dict[str, str]:
    """
    Detect test type for each function in the config.
    
    Returns:
        Dict: {"function_name": "test_type", ...}
    """
    result = {}
    
    for function_name, function_config in config.items():
        # print(f"[DEBUG] detect_test_type: {function_name} -> {function_config.get('test_type', 'Not set')}")
        
        # Check explicit test_type
        if "test_type" in function_config:
            result[function_name] = function_config["test_type"]
            continue
        
        # Auto-detect
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
            result[function_name] = "function"
    
    # print(f"[DEBUG] detect_test_type result: {result}")
    return result

def get_task_id_from_config(config_path: Path) -> str:
    """Extract full task ID: c5_t1_greeting"""
    filename = config_path.name
    return filename.replace("_config.py", "")

def get_task_name_from_config(config_path: Path) -> str:
    """Extract task name: greeting"""
    filename = config_path.name
    pattern = r"^c\d+_t\d+_(?P<name>\w+)_config\.py$"
    match = re.match(pattern, filename)
    if match:
        return match.group("name")
    return filename.replace("_config.py", "")

def get_chapter_from_task_id(task_id: str) -> str:
    """Extract chapter number from task ID (e.g., 'c5_t1_greeting' → 'Chapter 5')"""
    import re
    match = re.match(r"c(?P<chapter>\d+)_t\d+", task_id)
    if match:
        return f"Chapter {match.group('chapter')}"
    return "Unknown Chapter"

def read_py_file(filepath: Path) -> str:
    """Read a Python file with automatic encoding detection."""
    # Try encodings in order
    encodings = [
        'utf-8-sig',    # UTF-8 with BOM
        'utf-8',        # UTF-8 without BOM
        'utf-16-le',    # UTF-16 Little Endian
        'utf-16-be',    # UTF-16 Big Endian
        'cp1252',       # Windows default
        'latin-1',      # Fallback
    ]
    
    for encoding in encodings:
        try:
            content = filepath.read_text(encoding=encoding)
            # Remove BOM if present (U+FEFF)
            if content.startswith('\ufeff'):
                content = content[1:]
            # print(f"[DEBUG] Successfully read {filepath.name} with {encoding}")
            return content
        except (UnicodeDecodeError, LookupError):
            continue
    
    # Ultimate fallback
    with open(filepath, 'rb') as f:
        raw = f.read()
        return raw.decode('utf-8', errors='replace')

# ===== LOADERS =====

def load_config(task_id: str) -> Optional[Dict]:
    """Load config for a task."""
    config_path = TASK_CONFIGS_DIR / f"{task_id}_config.py"
    
    if not config_path.exists():
        return None
    
    try:
        content = read_py_file(config_path)
        
        if "CONFIG" not in content:
            return None
        
        spec = importlib.util.spec_from_file_location("config", config_path)
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)
        
        for var_name in ['CONFIG', 'config', 'TASK_CONFIG', 'cfg']:
            if hasattr(config_module, var_name):
                config_value = getattr(config_module, var_name)
                # print(f"[DEBUG] Found {var_name}: {type(config_value)}")
                if isinstance(config_value, dict) and config_value:
                    # print(f"[DEBUG] Config loaded successfully")
                    return config_value
        
        return None
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None

def load_solution(task_id: str):
    """Load solution for a task"""
    # task_id is like "c9_t1_read_int"
    solution_path = SOLUTIONS_DIR / f"{task_id}_solution.py"
    
    if not solution_path.exists():
        return None
    
    try:
        spec = importlib.util.spec_from_file_location("solution", solution_path)
        solution_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(solution_module)
        return solution_module
    except Exception:
        return None

def load_student_code(submission_path: Path):
    """Load student code into globals"""
    try:
        code = read_py_file(submission_path)
        
        # Check for input()
        # if "input(" in code:
            # print(f"[DEBUG] load_student_code: contains input()")
        
        student_globals = {}
        exec(code, student_globals)
        
        # Filter out builtins
        student_globals = {k: v for k, v in student_globals.items() if not k.startswith("_")}
        
        # print(f"[DEBUG] load_student_code: Found functions: {list(student_globals.keys())}")
        
        return student_globals
    except SyntaxError as e:
        return {"syntax_error": str(e)}
    except Exception as e:
        return {"load_error": str(e)}

# ===== EXPECTED BEHAVIOR =====

def get_expected_behavior(submission_filename: str) -> dict:
    """Determine expected behavior based on filename."""
    filename = submission_filename.lower()
    
    # Correct implementations → PASS
    if filename.startswith("correct"):
        return {
            "should_pass": True,
            "reason": "Correct implementation",
            "expected_failure": None
        }
    
    # Structure mutants → FAIL (structure)
    if "wrong_structure" in filename:
        return {
            "should_pass": False,
            "reason": "Structure mutant - should fail structure check",
            "expected_failure": "structure"
        }
    
    # Runtime mutants → FAIL (runtime)
    if "wrong_runtime" in filename:
        return {
            "should_pass": False,
            "reason": "Runtime mutant - should fail runtime check",
            "expected_failure": "runtime"
        }
    
    # General wrong mutants → FAIL (either)
    if filename.startswith("wrong"):
        return {
            "should_pass": False,
            "reason": "General mutant - should fail",
            "expected_failure": "runtime"
        }
    
    # Edge cases → FAIL
    if filename.startswith("edge"):
        return {
            "should_pass": False,
            "reason": "Edge case - should fail",
            "expected_failure": "runtime"
        }
    
    # Default: unknown → FAIL
    return {
        "should_pass": False,
        "reason": "Unknown file type - default to fail",
        "expected_failure": "runtime"
    }

# ===== HELPER FUNCTIONS =====

def _create_error_result(submission_file, status, formatted, should_pass=False):
    """Create a consistent error result dict"""
    return {
        "submission": submission_file,
        "passed": False,
        "should_pass": should_pass,
        "status": status,
        "errors": [],
        "formatted": formatted
    }

def _run_function_validators(student_path, student_module, solution_module, CONFIG):
    """Run function-based validators only"""
    return validate_function_run(
        str(student_path),
        student_module,
        solution_module,
        CONFIG
    )
    
def _run_file_validators(student_path, student_module, solution_module, CONFIG):
    """Run all file-based validators"""
    errors = validate_file_return(
        student_module,
        solution_module,
        CONFIG
    )
    
    side_effect_errors = validate_file_side_effect(
        student_module,
        solution_module,
        CONFIG
    )
    
    """ created_file_errors = validate_created_files(
        student_module,
        solution_module,
        CONFIG
    ) """
    
    return errors + side_effect_errors

# ===== TEST RUNNERS =====

def run_structure_test(task_id: str, submission_file: str, suppress: bool = False):
    """Run structure test with proper error handling"""
    if not suppress:
        print(f"\n[STRUCT] {task_id}/{submission_file}")
    
    CONFIG = load_config(task_id)
    if CONFIG is None:
        if not suppress:
            print("   [SKIP] No config found")
        return {
            "submission": submission_file,
            "passed": False,
            "should_pass": False,
            "status": "SKIP (no config)",
            "errors": [],
            "formatted": "Config not found"
        }
    
    student_path = MOCK_SUBMISSIONS_DIR / task_id / submission_file
    
    if not student_path.exists():
        if not suppress:
            print(f"   [SKIP] File not found: {student_path}")
        return {
            "submission": submission_file,
            "passed": False,
            "should_pass": False,
            "status": "SKIP (file not found)",
            "errors": [],
            "formatted": "Submission file not found"
        }
    
    # ===== CHECK FOR SYNTAX ERRORS =====
    try:
        code = read_py_file(student_path)
        import ast
        ast.parse(code)
    except SyntaxError as e:
        if not suppress:
            print(f"   [SYNTAX ERROR] {e}")
        expected = get_expected_behavior(submission_file)
        should_pass = expected["should_pass"]
        
        status = "PASS (correctly failed - syntax error)" if not should_pass else "FAIL - SYNTAX ERROR (should pass!)"
        return {
            "submission": submission_file,
            "passed": False,
            "should_pass": should_pass,
            "status": status,
            "errors": [{"heading": "Syntax Error", "details": [str(e)]}],
            "formatted": f"Syntax Error: {e}"
        }
    
    # ===== CONTINUE WITH NORMAL TESTING =====
    try:
        errors = validate_function_structure(str(student_path), CONFIG)
        formatted = format_errors(errors)
        if not suppress:
            print(formatted)
        
        actual_passed = len(errors) == 0
        expected = get_expected_behavior(submission_file)
        should_pass = expected["should_pass"]
        
        # === UNAMBIGUOUS STATUS ===
        if actual_passed == should_pass:
            if actual_passed:
                status = "PASS"
            else:
                status = "FAIL"
        else:
            if actual_passed and not should_pass:
                status = "STRUCTURE PASSED (but should fail overall)"
            else:
                status = "FALSE NEGATIVE (structure failed)"
        
        if not suppress:
            print(f"Result: {status}")
            print(f"Expected: {'PASS' if should_pass else 'FAIL'} - {expected['reason']}")
        
        return {
            "submission": submission_file,
            "passed": actual_passed,
            "should_pass": should_pass,
            "status": status,
            "errors": errors,
            "formatted": formatted
        }
    except Exception as e:
        if not suppress:
            print(f"   [ERROR] Test crashed: {e}")
        return {
            "submission": submission_file,
            "passed": False,
            "should_pass": False,
            "status": f"ERROR: {str(e)[:50]}",
            "errors": [],
            "formatted": f"Test crashed: {e}"
        }


def _run_io_validators(student_module, solution_module, CONFIG):
    """Run IO validators"""
    from fop_test_helpers import validate_io_function
    return validate_io_function(
        student_module,
        solution_module,
        CONFIG
    )

# run_tests.py (updated)

def run_runtime_test(task_id: str, submission_file: str, suppress: bool = False):
    """Run runtime tests using the unified validator."""
    
    print(f"\n[RUNTIME] {task_id}/{submission_file}")
    
    CONFIG = load_config(task_id)
    if CONFIG is None:
        return _create_error_result(submission_file, "SKIP (no config)", "Config not found")
    
    student_path = MOCK_SUBMISSIONS_DIR / task_id / submission_file
    
    if not student_path.exists():
        return _create_error_result(submission_file, "SKIP (file not found)", "Submission file not found")
    
    solution_module = load_solution(task_id)
    if solution_module is None and not suppress:
        print("   [WARN] No solution found - tests may fail")
    
    # Load student code
    student_ns = load_student_code(student_path)
    
    # Check for syntax error
    if student_ns and student_ns.get("syntax_error"):
        return _create_error_result(
            submission_file,
            "FAIL (syntax error)",
            f"Syntax Error: {student_ns['syntax_error']}",
            should_pass=get_expected_behavior(submission_file)["should_pass"]
        )
    
    # Check for load error
    if student_ns and student_ns.get("load_error"):
        return _create_error_result(
            submission_file,
            f"ERROR: {student_ns['load_error'][:50]}",
            f"Load Error: {student_ns['load_error']}",
            should_pass=get_expected_behavior(submission_file)["should_pass"]
        )
    
    student_module = types.SimpleNamespace(**student_ns)
    
    # ===== DETECT TEST TYPES =====
    from fop_test_helpers.validator import detect_test_type
    test_types = detect_test_type(CONFIG)
    
    if not suppress:
        print(f"   [INFO] Test types: {test_types}")
    
    # ===== USE UNIFIED VALIDATOR =====
    from fop_test_helpers.validator import validate_solution
    errors = validate_solution(
        student_module,
        solution_module,
        CONFIG
    )
    
    # ===== SHARED RESULTS =====
    formatted = format_errors(errors)
    if not suppress:
        print(formatted)
    
    actual_passed = len(errors) == 0
    expected = get_expected_behavior(submission_file)
    should_pass = expected["should_pass"]
    
    if actual_passed == should_pass:
        status = "PASS" if actual_passed else "FAIL"
    else:
        status = "FALSE POSITIVE" if actual_passed else "FALSE NEGATIVE"
    
    if not suppress:
        print(f"Result: {status}")
        print(f"Expected: {'PASS' if should_pass else 'FAIL'} - {expected['reason']}")
    
    return {
        "submission": submission_file,
        "passed": actual_passed,
        "should_pass": should_pass,
        "status": status,
        "errors": errors,
        "formatted": formatted
    }

# ===== DISCOVER TASKS =====

def discover_tasks() -> list:
    """Discover all tasks from config files"""
    config_files = list(TASK_CONFIGS_DIR.glob("c*_t*_*_config.py"))
    
    tasks = []
    for config_path in config_files:
        try:
            content = read_py_file(config_path)
            if "CONFIG" not in content:
                continue
            
            # Get task ID from filename: c9_t1_read_int_config.py -> c9_t1_read_int
            task_id = config_path.stem.replace("_config", "")
            
            # Extract chapter and task number for sorting
            parts = task_id.split("_")
            chapter = parts[0]  # "c9"
            task_num = parts[1]  # "t1"
            task_name = "_".join(parts[2:])  # "read_int"
            
            tasks.append({
                "task_id": task_id,
                "chapter": chapter,
                "task_num": task_num,
                "task_name": task_name,
                "config_path": config_path,
                "student_filename": f"{task_name}.py"
            })
        except Exception:
            continue
    
    return sorted(tasks, key=lambda x: x["task_id"])

# ===== MAIN TEST RUNNER =====

def run_all_tasks_for_task(task_id: str, suppress: bool = False):
    """Run all submissions for a single task"""
    task_dir = MOCK_SUBMISSIONS_DIR / task_id
    
    if not task_dir.exists():
        print(f"❌ Task folder not found: {task_dir}")
        return [], [], []
    
    print_header(f"TESTING ALL SUBMISSIONS FOR: {task_id}")
    
    submissions = sorted(task_dir.glob("*.py"))
    
    if not submissions:
        print(f"⚠️  No submissions found in {task_dir}")
        return [], [], []
    
    # Load config
    CONFIG = load_config(task_id)
    if CONFIG is None:
        print(f"❌ No config found for {task_id}")
        return [], [], []
    
    # Detect test types
    function_test_types = detect_test_type(CONFIG)
    has_io_test = any(t == "io" for t in function_test_types.values())
    print(f"Test types: {function_test_types}")
    print(f"Has IO tests: {has_io_test}")
    
    results = []
    false_positives = []
    false_negatives = []
    
    for submission_path in submissions:
        submission_file = submission_path.name
        
        print("-" * 60)
        print(f"[Testing] {submission_file}")
        
        # === STRUCTURE TEST ===
        struct_result = run_structure_test(task_id, submission_file)
        structure_passed = struct_result["passed"]
        structure_status = struct_result["status"]
        structure_errors = struct_result.get("errors", [])
        should_pass = get_expected_behavior(submission_file)["should_pass"]
        
        # === RUNTIME TEST ===
        if structure_passed:
            # Check for input()
            student_path = MOCK_SUBMISSIONS_DIR / task_id / submission_file
            contains_input = False
            try:
                with open(student_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                    if "input(" in code:
                        contains_input = True
            except Exception:
                pass
            
            # Only skip if NO IO tests AND contains input()
            if contains_input and not has_io_test:
                if not suppress:
                    print(f"   ⏭️  Skipping runtime - contains input()")
                runtime_passed = False
                runtime_status = "SKIP (contains input)"
                runtime_errors = []
            else:
                # Run runtime (IO tests will handle input() with mocks)
                runtime_result = run_runtime_test(task_id, submission_file, suppress)
                runtime_passed = runtime_result["passed"]
                runtime_status = runtime_result["status"]
                runtime_errors = runtime_result.get("errors", [])
        else:
            if not suppress:
                print(f"   ⏭️  Skipping runtime - structure failed")
            runtime_passed = False
            runtime_status = "SKIPPED (structure failed)"
            runtime_errors = []
        
        # === OVERALL RESULT ===
        # Determine if this is a true skip (input, no config) or a structure failure
        if "SKIP" in structure_status or "SKIP" in runtime_status:
            overall_passed = False
            
            # Check the reason for the skip
            if "no config" in structure_status.lower():
                overall_status = "SKIPPED (no config)"
            elif "contains input" in runtime_status.lower():
                overall_status = "SKIPPED (input)"
            elif not structure_passed:
                # Structure failed → this is a FAIL, not a skip
                overall_status = "FAIL"
                overall_passed = False
            else:
                overall_status = "SKIPPED"
        else:
            overall_passed = structure_passed and runtime_passed
            if overall_passed:
                overall_status = "PASS"
            else:
                overall_status = "FAIL"

        # === DETERMINE PASS/FAIL ===
        is_pass = False
        is_fail = False
        is_false_positive = False
        is_false_negative = False

        if structure_passed:
            if "contains input" in runtime_status:
                is_pass = False
                is_fail = False
                is_false_positive = False
                is_false_negative = False
            elif overall_passed and should_pass:
                is_pass = True
                is_fail = False
                is_false_positive = False
                is_false_negative = False
            elif not overall_passed and not should_pass:
                is_pass = True
                is_fail = False
                is_false_positive = False
                is_false_negative = False
            elif overall_passed and not should_pass:
                is_pass = False
                is_fail = True
                is_false_positive = True
                is_false_negative = False
                false_positives.append(f"{task_id}/{submission_file}")
            elif not overall_passed and should_pass:
                is_pass = False
                is_fail = True
                is_false_positive = False
                is_false_negative = True
                false_negatives.append(f"{task_id}/{submission_file}")
        else:
            if should_pass:
                is_pass = False
                is_fail = True
                is_false_positive = False
                is_false_negative = True
                false_negatives.append(f"{task_id}/{submission_file}")
            else:
                is_pass = True
                is_fail = False
                is_false_positive = False
                is_false_negative = False
        
        # === PRINT OVERALL (Smart Suppression) ===
        if suppress:
            # Only show detailed output for FAIL or SKIP
            if is_pass:
                print(f"   ✅ PASS")
            elif is_fail:
                print(f"   ❌ FAIL (incorrectly identified)")
                if not structure_passed:
                    print(f"      - Structure: FAIL ({structure_status})")
                if not runtime_passed and not runtime_status.startswith("SKIP"):
                    print(f"      - Runtime: FAIL ({runtime_status})")
                if structure_errors:
                    print("      Structure errors:")
                    for err in structure_errors:
                        print(f"        • {err.get('heading', 'Error')}")
                if runtime_errors:
                    print("      Runtime errors:")
                    for err in runtime_errors:
                        print(f"        • {err.get('heading', 'Error')}")
            elif "SKIPPED" in overall_status:
                print(f"   ⏭️  {overall_status}")
            else:
                print(f"   ❓ {overall_status}")
        else:
            # Full output mode
            if overall_passed:
                print(f"   ✅ Overall: PASS")
            elif "SKIPPED" in overall_status:
                print(f"   ⏭️  Overall: {overall_status}")
            else:
                print(f"   ❌ Overall: FAIL")
                if not structure_passed:
                    print(f"      - Structure: FAIL ({structure_status})")
                if not runtime_passed and not runtime_status.startswith("SKIP"):
                    print(f"      - Runtime: FAIL ({runtime_status})")
        
        # === STORE RESULT ===
        result = {
            "submission": submission_file,
            "overall_passed": overall_passed,
            "overall_status": overall_status,
            "structure_passed": structure_passed,
            "structure_status": structure_status,
            "runtime_passed": runtime_passed,
            "runtime_status": runtime_status,
            "structure_errors": structure_errors,
            "runtime_errors": runtime_errors,
            "should_pass": should_pass,
            "is_pass": is_pass,
            "is_fail": is_fail,
            "is_false_positive": is_false_positive,
            "is_false_negative": is_false_negative,
            "contains_input": contains_input if structure_passed else False
        }
        results.append(result)
    
    # === SUMMARY FOR TASK ===
    print(f"\n{'_'*80}")
    print(f"SUMMARY FOR: {task_id}")

    passed = sum(1 for r in results if r.get("is_pass", False))
    failed = sum(1 for r in results if r.get("is_fail", False))
    skipped = sum(1 for r in results if "SKIPPED" in r.get("overall_status", ""))
    total = len(results)
    fp_count = sum(1 for r in results if r.get("is_false_positive", False))
    fn_count = sum(1 for r in results if r.get("is_false_negative", False))

    print(f"Total submissions: {total}")
    print(f"  [PASS] Correctly identified:   {passed}")
    print(f"  [FAIL] Incorrectly identified: {failed}")
    print(f"  [SKIP] Skipped:                {skipped}")
    if fp_count > 0:
        print(f"  [FP] False Positives: {fp_count}")
    if fn_count > 0:
        print(f"  [FN] False Negatives: {fn_count}")

    if passed + failed + skipped != total:
        print(f"\n⚠️  WARNING: Total mismatch! {passed + failed + skipped} != {total}")

    print("\nDetailed results:")
    for r in results:
        if r.get("is_pass", False):
            status = "✅ PASS"
        elif r.get("is_fail", False):
            status = "❌ FAIL"
        elif "SKIPPED" in r.get("overall_status", ""):
            status = "⏭️ SKIP"
        else:
            status = "❓ UNKNOWN"
        
        fp_tag = " [FP]" if r.get("is_false_positive", False) else ""
        fn_tag = " [FN]" if r.get("is_false_negative", False) else ""
        print(f"  {status}{fp_tag}{fn_tag} {r['submission']}")
        print(f"    Structure: {r['structure_status']}")
        print(f"    Runtime:   {r['runtime_status']}")
    
    return results, false_positives, false_negatives

def run_all_tests(suppress: bool = False):
    """Run ALL tests for all tasks"""
    
    import random
    random.seed(12345)  # ← SEED ONCE AT THE VERY START!
    
    print_header(f"RUNNING ALL TESTS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Private data path: {PRIVATE_DIR}")
    if suppress:
        print("Suppress mode: ON (only showing failures)")
    
    if not MOCK_SUBMISSIONS_DIR.exists():
        print(f"\n[ERROR] Mock submissions not found at: {MOCK_SUBMISSIONS_DIR}")
        return {}
    
    tasks = discover_tasks()
    
    all_results = {}
    false_positives = []
    false_negatives = []
    
    for task in tasks:
        task_id = task["task_id"]
        print(f"\n{'='*80}")
        print(f"TASK: {task_id}")
        
        results, fp, fn = run_all_tasks_for_task(task_id, suppress=suppress)
        
        if results:
            all_results[task_id] = results
            false_positives.extend(fp)
            false_negatives.extend(fn)
            
    # ===== CHAPTER STATISTICS =====
    print("=" * 60 + " SUMMARY BY CHAPTER " + "=" * 60)

    chapter_stats = {}

    for task_id, task_results in all_results.items():
        if not task_results:
            continue
        
        chapter = get_chapter_from_task_id(task_id)
        
        if chapter not in chapter_stats:
            chapter_stats[chapter] = {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "false_positives": 0,
                "false_negatives": 0,
                "tasks": set()
            }
        
        for r in task_results:
            chapter_stats[chapter]["total"] += 1
            chapter_stats[chapter]["tasks"].add(task_id)
            
            if r.get("is_pass", False):
                chapter_stats[chapter]["passed"] += 1
            elif r.get("is_fail", False):
                chapter_stats[chapter]["failed"] += 1
            elif "SKIPPED" in r.get("overall_status", ""):
                chapter_stats[chapter]["skipped"] += 1
            
            if r.get("is_false_positive", False):
                chapter_stats[chapter]["false_positives"] += 1
            if r.get("is_false_negative", False):
                chapter_stats[chapter]["false_negatives"] += 1

    for chapter, stats in sorted(chapter_stats.items(), key=lambda x: int(x[0].split()[1]) if x[0] != "Unknown Chapter" else 999):
        task_count = len(stats["tasks"])
        pass_rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
        
        print(f"\n[ {chapter} ]")
        print(f"  Tasks:        {task_count}")
        print(f"  Submissions:  {stats['total']}")
        print(f"  [PASS] Correct:  {stats['passed']}")
        print(f"  [FAIL] Incorrect: {stats['failed']}")
        print(f"  [SKIP] Skipped:   {stats['skipped']}")
        print(f"  Pass Rate:    {pass_rate:.1f}%")
        
        if stats["false_positives"] > 0:
            print(f"  False Positives: {stats['false_positives']}")
        if stats["false_negatives"] > 0:
            print(f"  False Negatives: {stats['false_negatives']}")

    
    # ===== FINAL SUMMARY =====
    print("=" * 60 + " FINAL SUMMARY " + "=" * 60)
    
    total_submissions = 0
    total_passed = 0
    total_failed = 0
    total_skipped = 0
    
    for task_id, task_results in all_results.items():
        if not task_results:
            continue
        for r in task_results:
            total_submissions += 1
            if r.get("is_pass", False):
                total_passed += 1
            elif r.get("is_fail", False):
                total_failed += 1
            elif "SKIPPED" in r.get("overall_status", ""):
                total_skipped += 1
    
    print(f"Total submissions: {total_submissions}")
    print(f"  [PASS] Correctly identified:   {total_passed}")
    print(f"  [FAIL] Incorrectly identified: {total_failed}")
    print(f"  [SKIP] Skipped:                {total_skipped}")
    
    if total_submissions > 0:
        accuracy = (total_passed / total_submissions) * 100
        print(f"\nFramework Accuracy: {accuracy:.1f}%")
    
    if false_positives:
        print(f"\n[FAIL] FALSE POSITIVES ({len(false_positives)}):")
        for fp in false_positives:
            print(f"   - {fp}")
    
    if false_negatives:
        print(f"\n[FAIL] FALSE NEGATIVES ({len(false_negatives)}):")
        for fn in false_negatives:
            print(f"   - {fn}")
    
    if not false_positives and not false_negatives and total_skipped == 0:
        print("\n[PASS] PERFECT! All submissions correctly identified!")
    else:
        print(f"\n[INFO] Total failures: {total_failed}, Skips: {total_skipped}")
    
    return all_results

# ===== COMMAND LINE =====

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Local test runner")
    parser.add_argument("--task", help="Test a specific task (e.g., c5_t1_greeting)")
    parser.add_argument("--submission", default="correct1.py", help="Submission to test")
    parser.add_argument("--all", action="store_true", help="Test all tasks")
    parser.add_argument("--suppress", action="store_true", help="Suppress output for correctly identified tests")
    
    args = parser.parse_args()
    
    if args.all or (not args.task and not args.all):
        run_all_tests(suppress=args.suppress)
    elif args.task:
        run_all_tasks_for_task(args.task, suppress=args.suppress)
    else:
        print("Usage: python run_tests.py --task <task_id>")