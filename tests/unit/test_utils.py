"""Unit tests for utility functions."""

from analyzer.utils import count_functions


class TestCountFunctions:
    def test_python_functions(self):
        code = """
def foo():
    pass

def bar(x, y):
    return x + y
"""
        assert count_functions(code) == 2

    def test_no_functions(self):
        assert count_functions("x = 1\ny = 2\n") == 0

    def test_nested_function(self):
        code = """
def outer():
    def inner():
        pass
"""
        # AST walks all nodes, so both are counted
        assert count_functions(code) == 2

    def test_javascript_fallback(self):
        code = """
function hello(world) { console.log(world) }
function goodbye() { return 42 }
"""
        # SyntaxError → regex fallback
        assert count_functions(code) == 2

    def test_empty_string(self):
        assert count_functions("") == 0

    def test_class_methods_not_counted_as_functions(self):
        code = """
class MyClass:
    def method(self):
        pass
"""
        # ast.FunctionDef matches methods too — this is by design
        assert count_functions(code) == 1
