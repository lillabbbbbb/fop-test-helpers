import ast


def parse_source(filename):
    """
    Parse a Python source file into an AST.
    """
    with open(filename, encoding="utf-8") as f:
        return ast.parse(f.read())


def function_exists(filename, name):
    """
    True if the source file contains a function named 'name'.
    """
    return name in get_functions(filename)


def get_functions(filename):
    """
    Returns a dictionary mapping function names to their AST nodes.
    """
    tree = parse_source(filename)

    return {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }


def check_signature(filename, function_name, expected_parameters):
    """
    Checks whether a function exists and has the expected parameters.

    Returns:
        True  -> function exists and parameters match
        False -> function missing or parameters differ
    """

    functions = get_functions(filename)

    if function_name not in functions:
        return False

    actual_parameters = [
        arg.arg
        for arg in functions[function_name].args.args
    ]

    return (
        actual_parameters == expected_parameters,
        actual_parameters,
        expected_parameters,
    )


def get_missing_functions(filename, required):
    """
    Returns a list of missing function names.
    """
    return [
        name
        for name in required
        if not function_exists(filename, name)
    ]


def get_parameters(filename, function_name):
    """
    Returns the parameter names of a function.
    Returns None if the function does not exist.
    """
    functions = get_functions(filename)

    if function_name not in functions:
        return None

    return [arg.arg for arg in functions[function_name].args.args]


def has_return_statement(filename, function_name):
    """
    True if the function contains at least one return statement.
    """
    functions = get_functions(filename)

    if function_name not in functions:
        return False

    return any(
        isinstance(node, ast.Return)
        for node in ast.walk(functions[function_name])
    )


def uses_function(filename, function_name):
    """
    True if the source code calls a function with the given name.
    Useful for checking forbidden or required built-ins.
    """
    tree = parse_source(filename)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id == function_name:
                    return True

    return False


def get_imports(filename):
    """
    Returns a list of imported module names.
    """
    tree = parse_source(filename)

    imports = []

    for node in ast.walk(tree):

        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)

        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module)

    return imports


def has_class(filename, class_name):
    """
    True if the source contains the specified class.
    """
    tree = parse_source(filename)

    return any(
        isinstance(node, ast.ClassDef) and node.name == class_name
        for node in ast.walk(tree)
    )


def get_methods(filename, class_name):
    """
    Returns a dictionary mapping method names to AST nodes.
    """
    tree = parse_source(filename)

    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {
                method.name: method
                for method in node.body
                if isinstance(method, ast.FunctionDef)
            }

    return {}


def check_open_mode(filename, function_name, expected_mode):
    """
    Check whether a function opens a file using the expected mode.

    Returns:
        (matches, actual_mode)

    actual_mode is one of:
        "r", "w", "a", "r+", ...
        None    (no open() call found)
        "dynamic" (mode supplied via a variable/expression)
    """

    with open(filename, encoding="utf-8") as f:
        tree = ast.parse(f.read())

    for node in tree.body:

        if not isinstance(node, ast.FunctionDef):
            continue

        if node.name != function_name:
            continue

        for call in ast.walk(node):

            if not (
                isinstance(call, ast.Call)
                and isinstance(call.func, ast.Name)
                and call.func.id == "open"
            ):
                continue

            # -------------------------------
            # default mode
            # -------------------------------

            mode = "r"

            # positional mode
            if len(call.args) >= 2:

                arg = call.args[1]

                if (
                    isinstance(arg, ast.Constant)
                    and isinstance(arg.value, str)
                ):
                    mode = arg.value
                else:
                    mode = "dynamic"

            # keyword mode overrides positional
            for kw in call.keywords:

                if kw.arg == "mode":

                    if (
                        isinstance(kw.value, ast.Constant)
                        and isinstance(kw.value.value, str)
                    ):
                        mode = kw.value.value
                    else:
                        mode = "dynamic"

            return mode == expected_mode, mode

        return False, None

    return False, None

import ast


def check_file_closed(filename, function_name):
    """
    Returns:
        (found_open, properly_closed)

        found_open:
            True  -> at least one open() call exists
            False -> no open() call found

        properly_closed:
            True  -> every opened file was closed
            False -> at least one opened file was not closed
    """

    with open(filename, encoding="utf-8") as f:
        tree = ast.parse(f.read())

    for node in tree.body:

        if not isinstance(node, ast.FunctionDef):
            continue

        if node.name != function_name:
            continue

        opened = set()
        closed = set()

        for stmt in ast.walk(node):

            # file = open(...)
            if (
                isinstance(stmt, ast.Assign)
                and isinstance(stmt.value, ast.Call)
                and isinstance(stmt.value.func, ast.Name)
                and stmt.value.func.id == "open"
            ):

                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        opened.add(target.id)

            # file.close()
            elif (
                isinstance(stmt, ast.Call)
                and isinstance(stmt.func, ast.Attribute)
                and stmt.func.attr == "close"
                and isinstance(stmt.func.value, ast.Name)
            ):

                closed.add(stmt.func.value.id)

        if not opened:
            return False, False

        return True, opened <= closed

    return False, False