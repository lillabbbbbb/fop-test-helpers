from cg_feedback_helpers import asserter


def run_cases(func, cases):
    """
    Run a series of test cases against a function.

    Parameters
    ----------
    func : callable
        The student's function.

    cases : iterable
        Each element should be:
            (args, expected)

        where args is a tuple of positional arguments.
    """

    for args, expected in cases:

        result = func(*args)

        asserter.equals(
            result,
            expected,
            negative_feedback=(
                f"{func.__name__}{args} should return "
                f"{expected!r}, but returned {result!r}."
            )
        )


def assert_return_type(func, args, expected_type):
    """
    Check that the function returns the expected type.
    """

    result = func(*args)

    asserter.is_true(
        isinstance(result, expected_type),
        negative_feedback=(
            f"{func.__name__}{args} should return "
            f"{expected_type.__name__}, "
            f"but returned {type(result).__name__}."
        )
    )


def assert_raises(func, args, exception):
    """
    Check that a function raises the expected exception.
    """

    try:
        func(*args)

        asserter.is_true(
            False,
            negative_feedback=(
                f"{func.__name__}{args} should raise "
                f"{exception.__name__}."
            )
        )

    except exception:
        pass


def assert_does_not_raise(func, args):
    """
    Ensure a function executes without raising an exception.
    """

    try:
        func(*args)

    except Exception as e:

        asserter.is_true(
            False,
            negative_feedback=(
                f"{func.__name__}{args} raised "
                f"{type(e).__name__}: {e}"
            )
        )


def assert_mutates_list(func, original, expected):
    """
    Check that a function modifies a list in place.
    """

    data = original.copy()

    func(data)

    asserter.equals(
        data,
        expected,
        negative_feedback=(
            f"The list should become {expected}, "
            f"but became {data}."
        )
    )


def assert_returns_new_list(func, original, expected):
    """
    Check that a function returns a new list.
    """

    data = original.copy()

    result = func(data)

    asserter.equals(
        result,
        expected,
        negative_feedback=(
            f"Expected {expected}, but got {result}."
        )
    )

    asserter.equals(
        data,
        original,
        negative_feedback=(
            "The original list should not be modified."
        )
    )