"""Tests for parser module."""

import pytest
from rotalabs_verity.encoder import parse_method, ParseError, MethodInfo


class TestParser:
    def test_simple_method(self):
        """Parse a simple method."""
        code = '''
def allow(self, timestamp: float) -> bool:
    return True
'''
        info = parse_method(code)

        assert info.name == "allow"
        assert info.params == [("timestamp", "float")]
        assert info.return_type == "bool"
        assert len(info.body) == 1

    def test_method_with_multiple_params(self):
        """Parse method with multiple parameters."""
        code = '''
def transfer(self, amount: int, target: int) -> bool:
    return True
'''
        info = parse_method(code)

        assert info.name == "transfer"
        assert info.params == [("amount", "int"), ("target", "int")]

    def test_method_without_type_hints(self):
        """Parse method without type annotations."""
        code = '''
def simple(self, x):
    return x
'''
        info = parse_method(code)

        assert info.name == "simple"
        assert info.params == [("x", None)]
        assert info.return_type is None

    def test_method_with_body(self):
        """Parse method with statements in body."""
        code = '''
def decrement(self, amount: int) -> bool:
    if self.count >= amount:
        self.count = self.count - amount
        return True
    return False
'''
        info = parse_method(code)

        assert info.name == "decrement"
        assert len(info.body) == 2  # if statement + return

    def test_parse_error_on_invalid(self):
        """ParseError on invalid code."""
        code = "x = 1"  # Not a function

        with pytest.raises(ParseError, match="Subset validation failed"):
            parse_method(code)

    def test_parse_error_on_list(self):
        """ParseError on unsupported features."""
        code = '''
def method(self):
    return [1, 2, 3]
'''
        with pytest.raises(ParseError, match="Subset validation failed"):
            parse_method(code)
