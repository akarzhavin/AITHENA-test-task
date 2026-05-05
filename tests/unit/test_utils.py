"""Unit tests for utility functions."""

import pytest
from analyzer.utils import count_functions


@pytest.mark.parametrize(
    "source_code, expected_count, description",
    [
        ("def foo(): pass\ndef bar(x, y): return x+y", 2, "Simple Python functions"),
        ("x = 1\ny = 2", 0, "No functions"),
        ("def outer():\n    def inner(): pass", 2, "Nested Python functions (AST walks all nodes)"),
        ("function hello() {}\nfunction bye() {}", 2, "JavaScript functions (regex fallback)"),
        ("", 0, "Empty string"),
        ("class MyClass:\n    def method(self): pass", 1, "Class methods (counted as FunctionDef)"),
        ("  def indented(): pass", 1, "Indented Python function"),
    ],
)
def test_count_functions(source_code, expected_count, description):
    """
    Test that count_functions correctly identifies function definitions
    using both AST (for Python) and regex fallback (for other languages).
    """
    assert count_functions(source_code) == expected_count, description
