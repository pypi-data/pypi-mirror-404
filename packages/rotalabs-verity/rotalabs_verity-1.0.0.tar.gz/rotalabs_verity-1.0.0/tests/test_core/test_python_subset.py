"""Tests for Python subset validation."""

import pytest
from rotalabs_verity.core.python_subset import validate_python_subset, SubsetViolation


class TestValidCode:
    """Code that should be accepted."""

    @pytest.mark.parametrize("code", [
        # Simple method
        "def f(self): return True",
        # With parameters
        "def f(self, x: int) -> bool: return x > 0",
        # Assignment
        "def f(self, x: int) -> int:\n    y = x + 1\n    return y",
        # Self assignment
        "def f(self, x: int) -> None:\n    self.count = x",
        # Augmented assignment
        "def f(self, x: int) -> None:\n    self.count += x",
        # Conditional
        "def f(self, x: int) -> bool:\n    if x > 0:\n        return True\n    return False",
        # While loop
        "def f(self, n: int) -> int:\n    i = 0\n    while i < n:\n        i += 1\n    return i",
        # For range
        "def f(self, n: int) -> int:\n    s = 0\n    for i in range(n):\n        s += i\n    return s",
        # Built-ins
        "def f(self, x: int, y: int) -> int:\n    return min(max(x, y), abs(x - y))",
        # Conditional expression
        "def f(self, x: int) -> int:\n    return x if x > 0 else -x",
    ])
    def test_valid(self, code):
        ast = validate_python_subset(code)
        assert ast is not None

    def test_simple_method(self):
        code = '''
def allow(self, timestamp: float) -> bool:
    return True
'''
        ast = validate_python_subset(code)
        assert ast is not None

    def test_assignment(self):
        code = '''
def method(self, x: int) -> int:
    y = x + 1
    self.count = y
    return y
'''
        validate_python_subset(code)

    def test_augmented_assignment(self):
        code = '''
def method(self, x: int) -> None:
    self.count += x
    self.total -= 1
'''
        validate_python_subset(code)

    def test_conditional(self):
        code = '''
def method(self, x: int) -> bool:
    if x > 0:
        return True
    elif x == 0:
        return False
    else:
        return False
'''
        validate_python_subset(code)

    def test_while_loop(self):
        code = '''
def method(self, n: int) -> int:
    i = 0
    while i < n:
        i += 1
    return i
'''
        validate_python_subset(code)

    def test_for_range(self):
        code = '''
def method(self, n: int) -> int:
    total = 0
    for i in range(n):
        total += i
    return total
'''
        validate_python_subset(code)

    def test_builtins(self):
        code = '''
def method(self, x: int, y: int) -> int:
    return min(max(x, y), abs(x - y))
'''
        validate_python_subset(code)

    def test_conditional_expression(self):
        code = '''
def method(self, x: int) -> int:
    return x if x > 0 else -x
'''
        validate_python_subset(code)


class TestInvalidCode:
    """Code that should be rejected."""

    @pytest.mark.parametrize("code,error_match", [
        ("x = 1", "must contain a function"),
        ("class Foo: pass", "must contain a function"),  # No function def found
        ("import math\ndef f(self): pass", "Only function definitions allowed"),  # Import before function
        ("def f(self): return [1,2,3]", "Lists not supported"),
        ("def f(self): return {'a': 1}", "Dicts not supported"),
        ("def f(self):\n    try:\n        pass\n    except:\n        pass", "Try/except not supported"),
        ("def f(self): return len('x')", "not supported"),
        ("def f(x): return x", "must have 'self'"),
        ("def f(self): f = lambda x: x", "Lambda not supported"),
        ("def f(self): return [i for i in range(3)]", "List comprehension not supported"),
    ])
    def test_invalid(self, code, error_match):
        with pytest.raises(SubsetViolation, match=error_match):
            validate_python_subset(code)

    def test_no_function(self):
        code = "x = 1"
        with pytest.raises(SubsetViolation, match="must contain a function"):
            validate_python_subset(code)

    def test_class_definition(self):
        code = '''
class Foo:
    pass
'''
        # No function definition found, so the "must contain a function" error is raised first
        with pytest.raises(SubsetViolation, match="must contain a function"):
            validate_python_subset(code)

    def test_import(self):
        code = '''
import math
def method(self):
    return math.pi
'''
        # Import is detected as a non-function top-level statement
        with pytest.raises(SubsetViolation, match="Only function definitions allowed"):
            validate_python_subset(code)

    def test_list(self):
        code = '''
def method(self):
    return [1, 2, 3]
'''
        with pytest.raises(SubsetViolation, match="Lists not supported"):
            validate_python_subset(code)

    def test_dict(self):
        code = '''
def method(self):
    return {"a": 1}
'''
        with pytest.raises(SubsetViolation, match="Dicts not supported"):
            validate_python_subset(code)

    def test_try_except(self):
        code = '''
def method(self):
    try:
        return 1
    except:
        return 0
'''
        with pytest.raises(SubsetViolation, match="Try/except not supported"):
            validate_python_subset(code)

    def test_unsupported_function(self):
        code = '''
def method(self, x: int):
    return len(str(x))
'''
        with pytest.raises(SubsetViolation, match="not supported"):
            validate_python_subset(code)

    def test_no_self(self):
        code = '''
def method(x: int) -> int:
    return x
'''
        with pytest.raises(SubsetViolation, match="must have 'self'"):
            validate_python_subset(code)

    def test_lambda(self):
        code = '''
def method(self, x: int):
    f = lambda y: y + 1
    return f(x)
'''
        with pytest.raises(SubsetViolation, match="Lambda not supported"):
            validate_python_subset(code)

    def test_list_comprehension(self):
        code = '''
def method(self, n: int):
    return [i for i in range(n)]
'''
        with pytest.raises(SubsetViolation, match="List comprehension not supported"):
            validate_python_subset(code)

    def test_subscript(self):
        code = '''
def method(self, x: int):
    return x[0]
'''
        with pytest.raises(SubsetViolation, match="Subscript"):
            validate_python_subset(code)

    def test_fstring(self):
        code = '''
def method(self, x: int):
    return f"value: {x}"
'''
        with pytest.raises(SubsetViolation, match="F-strings not supported"):
            validate_python_subset(code)

    def test_multiple_functions(self):
        code = '''
def f(self):
    return 1

def g(self):
    return 2
'''
        with pytest.raises(SubsetViolation, match="exactly one function"):
            validate_python_subset(code)

    def test_string_literal(self):
        code = '''
def method(self):
    return "hello"
'''
        with pytest.raises(SubsetViolation, match="Literal type str not supported"):
            validate_python_subset(code)
