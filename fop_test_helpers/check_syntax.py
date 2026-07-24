#!/usr/bin/env python3

import py_compile
from cg_feedback_helpers import asserter


def check_syntax(filename):
    try:
        py_compile.compile(filename, doraise=True)
        return True

    except py_compile.PyCompileError as e:
        asserter.is_true(
            e is not None,
            positive_feedback="",
            negative_feedback="Your program crashed due to syntax errors. Test your program locally before you hand it in to CodeGrade"
        )
        print("Syntax errors found:")
        print(e)
        return False
