# debug_random.py
import random
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

# Load the reference solution
def load_solution(task_id):
    import importlib.util
    solution_path = Path("private/solutions") / f"{task_id}_solution.py"
    if not solution_path.exists():
        print(f"❌ Solution not found: {solution_path}")
        return None
    
    spec = importlib.util.spec_from_file_location("solution", solution_path)
    solution_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(solution_module)
    return solution_module

# Load student code
def load_student(submission_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("student", submission_path)
    student_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(student_module)
    return student_module

# Debug function
def debug_random_task(task_id, submission_file):
    print(f"\n{'='*60}")
    print(f"DEBUG: {task_id}/{submission_file}")
    print(f"{'='*60}")
    
    # Load solution
    solution = load_solution(task_id)
    if solution is None:
        return
    
    # Load student
    student_path = Path(f"private/mock_submissions/{task_id}/{submission_file}")
    if not student_path.exists():
        print(f"❌ Student file not found: {student_path}")
        return
    
    student = load_student(student_path)
    
    # Test data
    loot_list = ["Wooden Sword", "Magic Potion", "Gold Coins", "Diamond", "Nothing"]
    num = 4
    
    print("\n" + "-"*60)
    print("TRACKING RANDOM CALLS")
    print("-"*60)
    
    # Track random calls for solution
    random.seed(12345)
    solution_call_count = 0
    original_choice = random.choice
    
    def solution_counted_choice(seq):
        nonlocal solution_call_count
        solution_call_count += 1
        return original_choice(seq)
    
    random.choice = solution_counted_choice
    
    print("\n[REFERENCE SOLUTION]")
    print(f"  Calling get_loots({loot_list}, {num})...")
    try:
        result = solution.get_loots(loot_list, num)
        print(f"  Result: {result}")
        print(f"  Random calls: {solution_call_count}")
    except Exception as e:
        print(f"  ❌ CRASHED: {e}")
    
    # Restore random
    random.choice = original_choice
    
    # Track random calls for student
    random.seed(12345)
    student_call_count = 0
    
    def student_counted_choice(seq):
        nonlocal student_call_count
        student_call_count += 1
        return original_choice(seq)
    
    random.choice = student_counted_choice
    
    print("\n[STUDENT CODE]")
    print(f"  Calling get_loots({loot_list}, {num})...")
    try:
        result = student.get_loots(loot_list, num)
        print(f"  Result: {result}")
        print(f"  Random calls: {student_call_count}")
    except Exception as e:
        print(f"  ❌ CRASHED: {e}")
    
    # Restore random
    random.choice = original_choice
    
    print("\n" + "-"*60)
    print("COMPARISON")
    print("-"*60)
    
    # Compare
    random.seed(12345)
    print(f"Solution random calls: {solution_call_count}")
    print(f"Student random calls:  {student_call_count}")
    
    if solution_call_count == student_call_count:
        print("✅ Same number of random calls!")
    else:
        print("❌ DIFFERENT random calls!")
        print(f"   Difference: {abs(solution_call_count - student_call_count)} extra call(s)")
        print("   This is why the results don't match!")
        print("   Check for extra random.choice() or random.random() calls.")
    
    # Show what the sequence should be
    random.seed(12345)
    print("\n[EXPECTED SEQUENCE]")
    sequence = []
    for i in range(max(solution_call_count, student_call_count)):
        sequence.append(random.choice(loot_list))
    print(f"  Random sequence: {sequence}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python debug_random.py <task_id> <submission_file>")
        print("Example: python debug_random.py c8_t3_loot_drop correct1.py")
        sys.exit(1)
    
    debug_random_task(sys.argv[1], sys.argv[2])