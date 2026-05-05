"""Utility helpers — kept in a single file."""

from __future__ import annotations

import ast
import re


def count_functions(source_code: str) -> int:
    """Count top-level function definitions in *source_code*.

    Uses Python's AST when possible; falls back to a regex heuristic
    for files that aren't valid Python (e.g. JS/TS with a .py extension).
    """
    try:
        tree = ast.parse(source_code)
        return sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
    except SyntaxError:
        # Fallback: count lines that look like function defs
        pattern = re.compile(r"^\s*(?:def |function )\w+", re.MULTILINE)
        return len(pattern.findall(source_code))
