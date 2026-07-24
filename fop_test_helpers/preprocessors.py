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


