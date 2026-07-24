# recreate_all_files.py
import os
from pathlib import Path

def create_file(filepath, content=""):
    """Create a file with UTF-8 encoding (no BOM)"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content, encoding="utf-8")
    print(f"✅ Created: {filepath}")

def create_all_files():
    """Recreate ALL empty files with UTF-8 encoding"""
    
    # Create directories
    os.makedirs("private/task_configs", exist_ok=True)
    os.makedirs("private/solutions", exist_ok=True)
    
    # List all your tasks
    tasks = [
        # Chapter 3
        {"id": "c3_t1", "name": "compare"},
        {"id": "c3_t2", "name": "months"},
        {"id": "c3_t3", "name": "num_check"},
        {"id": "c3_t4", "name": "slope"},
        {"id": "c3_t5", "name": "even_odd"},
        {"id": "c3_t6", "name": "temperature"},
        
        # Chapter 4
        {"id": "c4_t1", "name": "characters"},
        {"id": "c4_t2", "name": "for_demo"},
        {"id": "c4_t3", "name": "while_demo"},
        {"id": "c4_t4", "name": "digits"},
        {"id": "c4_t5", "name": "factorial"},
        {"id": "c4_t6", "name": "fibonacci"},
        {"id": "c4_t7", "name": "shape"},
    ]
    
    # Create configs, mocks, and solutions
    for task in tasks:
        task_id = task["id"]
        task_name = task["name"]
        full_id = f"{task_id}_{task_name}"
        
        # Create config file (empty for now)
        create_file(Path(f"private/task_configs/{full_id}_config.py"))
        
        # Create mock submissions folder
        mock_dir = Path(f"private/mock_submissions/{full_id}")
        mock_dir.mkdir(parents=True, exist_ok=True)
        
        # Create mock files
        create_file(mock_dir / "correct1.py")
        create_file(mock_dir / "correct2.py")
        create_file(mock_dir / "wrong1.py")
        create_file(mock_dir / "wrong2.py")
        
        # Create solution file
        create_file(Path(f"private/solutions/{full_id}_solution.py"))
    
    print("\n✅ ALL FILES RECREATED WITH UTF-8 ENCODING!")
    print("   (They are empty — you'll need to add content)")

if __name__ == "__main__":
    create_all_files()