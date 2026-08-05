from pathlib import Path
import importlib

def inject_into_code(file_path, substring, code_to_inject, before=True, after=None):
    """
    Inject code into a file and return the executed environment.
    """
    if after is not None:
        before = not after
    
    path = Path(file_path)
    
    print(f"[DEBUG] Injecting into file: {path}")
    print(f"[DEBUG] Substring: '{substring}'")
    print(f"[DEBUG] Position: {'BEFORE' if before else 'AFTER'}")
    print(f"[DEBUG] Code: {repr(code_to_inject)}")
    
    lines = path.read_text().splitlines()
    
    found = False
    for i, line in enumerate(lines):
        if substring in line:
            insert_pos = i if before else i + 1
            lines.insert(insert_pos, code_to_inject)
            found = True
            print(f"[DEBUG] Found at line {i+1}: {line}")
            print(f"[DEBUG] Inserting at position {insert_pos}")
            break
    
    if not found:
        raise ValueError(f"Substring '{substring}' not found in {file_path}")
    
    modified_code = "\n".join(lines)
    path.write_text(modified_code)
    
    print(f"[DEBUG] File written successfully")
    
    # Execute the modified code and return the environment
    env = {}
    exec(modified_code, env)
    
    return env


import ast

KEEP = (
    ast.Import,
    ast.ImportFrom,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.ClassDef,
)

def extract_definitions(source):
    tree = ast.parse(source)

    tree.body = [
        node for node in tree.body
        if isinstance(node, KEEP)
    ]

    return ast.unparse(tree)


