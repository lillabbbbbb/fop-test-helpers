def format_errors(errors):
    """
    Convert a list of error messages into a nicely formatted string.
    """
    
    print("--------- OUTPUT FROM TEST ---------")

    if not errors:
        return "✓ All tests passed!"

    lines = [
        f"____________________________\nFound {len(errors)} error{'s' if len(errors) != 1 else ''}:",
        ""
    ]

    for i, error in enumerate(errors, start=1):

        # Heading from config feedback
        lines.append(f"{i}. {error['heading']}")
        lines.append("")

        # Optional function name
        if "function" in error:
            lines.append(
                f"   Function : {error['function']}"
            )

        # Detailed feedback
        for detail in error.get("details", []):
            lines.append(
                f"   {detail}"
            )

        # Blank line between errors
        if i != len(errors):
            lines.append("")
            lines.append("-" * 40)
            lines.append("")

    return "\n".join(lines)

def format_param_list(params):
    """Format a list of parameters without quotes or brackets."""
    if params is None:
        return "None"
    if not params:
        return "no parameters"
    return ", ".join(params)


def format_file_contents(title, text):
    lines = text.splitlines()

    formatted = ["", title, "-" * len(title)]

    if not lines:
        formatted.append("<empty>")
    else:
        for i, line in enumerate(lines, 1):
            formatted.append(f"{i:>3} | {line}")

    return formatted

def display_newlines(text):
    """
    Display newline characters as actual new lines.
    Shows special characters like \n, \t, \r visually.
    """
    if text is None:
        return ""
    
    # Replace common escape sequences with visible representations
    # First, handle the actual newlines
    lines = text.split('\n')
    
    result = []
    for i, line in enumerate(lines):
        # Show line number for clarity
        result.append(f"{line}")
    
    return '\n'.join(result)