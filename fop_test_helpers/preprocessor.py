from pathlib import Path

def inject_before_substring(file_path, substring, code_to_inject):
    """
    Injects code immediately before the first line containing `substring`,
    executes the modified program, and returns its global namespace.

    Parameters
    ----------
    file_path : str
        Path to the Python file.
    substring : str
        Substring to search for.
    code_to_inject : str
        One or more lines of Python code to inject.

    Returns
    -------
    dict
        The executed program's global namespace.
    """
    path = Path(file_path)
    lines = path.read_text().splitlines()

    for i, line in enumerate(lines):
        if substring in line:
            lines.insert(i, code_to_inject)
            break
    else:
        raise ValueError(f"Substring '{substring}' not found.")

    modified_code = "\n".join(lines)

    env = {}
    exec(modified_code, env)

    return env