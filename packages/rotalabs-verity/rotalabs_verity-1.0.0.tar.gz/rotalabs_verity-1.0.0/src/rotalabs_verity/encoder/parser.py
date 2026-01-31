"""
Python AST parsing for encoding.

Parses method definitions into a structured representation
suitable for symbolic execution.
"""

import ast
from dataclasses import dataclass

from rotalabs_verity.core.python_subset import SubsetViolation, validate_python_subset


@dataclass
class MethodInfo:
    """Parsed method information."""
    name: str
    params: list[tuple[str, str]]  # [(name, type), ...]
    return_type: str | None
    body: list[ast.stmt]
    source: str


class ParseError(Exception):
    """Error during parsing."""
    pass


class MethodParser:
    """
    Parses Python method source into structured representation.

    Validates that code is in the supported subset before parsing.
    """

    def parse(self, source: str) -> MethodInfo:
        """
        Parse method source code.

        Args:
            source: Python source code containing a single method

        Returns:
            MethodInfo with parsed details

        Raises:
            ParseError: If parsing fails
            SubsetViolation: If code uses unsupported features
        """
        # Validate subset first
        try:
            tree = validate_python_subset(source)
        except SubsetViolation as e:
            raise ParseError(f"Subset validation failed: {e}") from e

        # Find the function definition
        func_def = None
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                func_def = node
                break

        if func_def is None:
            raise ParseError("No function definition found")

        # Extract parameters (skip 'self')
        params = []
        for arg in func_def.args.args[1:]:  # Skip self
            arg_name = arg.arg
            arg_type = self._get_annotation_type(arg.annotation)
            params.append((arg_name, arg_type))

        # Extract return type
        return_type = self._get_annotation_type(func_def.returns)

        return MethodInfo(
            name=func_def.name,
            params=params,
            return_type=return_type,
            body=func_def.body,
            source=source
        )

    def _get_annotation_type(self, annotation: ast.expr | None) -> str | None:
        """Extract type name from annotation."""
        if annotation is None:
            return None

        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Constant):
            return str(annotation.value)

        return None


def parse_method(source: str) -> MethodInfo:
    """
    Convenience function to parse a method.

    Args:
        source: Python source code

    Returns:
        MethodInfo

    Raises:
        ParseError: If parsing fails
    """
    parser = MethodParser()
    return parser.parse(source)
