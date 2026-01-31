"""
Python subset definition and validation.

This module defines exactly what Python constructs we can verify,
and provides validation to reject unsupported code.
"""

import ast
from enum import Enum


class SubsetViolation(Exception):
    """Raised when code uses unsupported Python features."""
    def __init__(self, message: str, line: int | None = None, node: ast.AST | None = None):
        self.message = message
        self.line = line or (node.lineno if node and hasattr(node, 'lineno') else None)
        super().__init__(f"Line {self.line}: {message}" if self.line else message)


class VarType(Enum):
    """Types we can encode to Z3."""
    BOOL = "bool"
    INT = "int"
    REAL = "real"
    UNKNOWN = "unknown"


# Supported built-in functions
SUPPORTED_BUILTINS = {"min", "max", "abs", "range"}

# Supported binary operators
SUPPORTED_BINOPS = {
    ast.Add, ast.Sub, ast.Mult, ast.Div,
    ast.FloorDiv, ast.Mod
}

# Supported comparison operators
SUPPORTED_CMPOPS = {
    ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.Eq, ast.NotEq
}

# Supported boolean operators
SUPPORTED_BOOLOPS = {ast.And, ast.Or}

# Supported unary operators
SUPPORTED_UNARYOPS = {ast.Not, ast.USub}

# Supported augmented assignment operators
SUPPORTED_AUGASSIGN = {
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod
}


class SubsetValidator(ast.NodeVisitor):
    """
    Validates that Python code is in the verifiable subset.

    Raises SubsetViolation for any unsupported construct.
    """

    def __init__(self):
        self.in_function = False
        self.loop_depth = 0

    def validate(self, code: str) -> ast.Module:
        """
        Validate code and return AST if valid.

        Raises SubsetViolation if code uses unsupported features.
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise SubsetViolation(f"Syntax error: {e.msg}", e.lineno) from e

        self.visit(tree)
        return tree

    def visit_Module(self, node: ast.Module):
        """Module should contain exactly one function definition."""
        func_defs = [n for n in node.body if isinstance(n, ast.FunctionDef)]

        if len(func_defs) == 0:
            raise SubsetViolation("Code must contain a function definition")
        if len(func_defs) > 1:
            raise SubsetViolation("Code must contain exactly one function")

        # Check for other top-level statements
        for n in node.body:
            if not isinstance(n, ast.FunctionDef):
                raise SubsetViolation(
                    f"Only function definitions allowed at top level, got {type(n).__name__}",
                    node=n
                )

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Validate function definition."""
        self.in_function = True

        # First parameter must be 'self'
        if not node.args.args or node.args.args[0].arg != "self":
            raise SubsetViolation(
                "Method must have 'self' as first parameter",
                node=node
            )

        # No *args, **kwargs
        if node.args.vararg:
            raise SubsetViolation("*args not supported", node=node)
        if node.args.kwarg:
            raise SubsetViolation("**kwargs not supported", node=node)
        if node.args.kwonlyargs:
            raise SubsetViolation("Keyword-only args not supported", node=node)

        # No decorators
        if node.decorator_list:
            raise SubsetViolation("Decorators not supported", node=node)

        # Visit body
        for stmt in node.body:
            self.visit(stmt)

        self.in_function = False

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        raise SubsetViolation("Async functions not supported", node=node)

    def visit_ClassDef(self, node: ast.ClassDef):
        raise SubsetViolation("Class definitions not supported", node=node)

    # =========================================================================
    # Statements
    # =========================================================================

    def visit_Assign(self, node: ast.Assign):
        """Simple assignment: x = expr or self.x = expr"""
        if len(node.targets) != 1:
            raise SubsetViolation("Multiple assignment targets not supported", node=node)

        target = node.targets[0]
        if not isinstance(target, (ast.Name, ast.Attribute)):
            raise SubsetViolation(
                f"Assignment target must be variable or attribute, got {type(target).__name__}",
                node=node
            )

        if isinstance(target, ast.Attribute):
            if not (isinstance(target.value, ast.Name) and target.value.id == "self"):
                raise SubsetViolation("Only self.x attribute access supported", node=node)

        self.visit(node.value)

    def visit_AugAssign(self, node: ast.AugAssign):
        """Augmented assignment: x += expr"""
        if type(node.op) not in SUPPORTED_AUGASSIGN:
            raise SubsetViolation(
                f"Augmented assignment operator {type(node.op).__name__} not supported",
                node=node
            )

        if not isinstance(node.target, (ast.Name, ast.Attribute)):
            raise SubsetViolation("Augmented assignment target must be variable", node=node)

        self.visit(node.value)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        """Annotated assignment - allow but ignore annotation."""
        if node.value:
            self.visit(node.value)

    def visit_If(self, node: ast.If):
        """If statement."""
        self.visit(node.test)
        for stmt in node.body:
            self.visit(stmt)
        for stmt in node.orelse:
            self.visit(stmt)

    def visit_While(self, node: ast.While):
        """While loop (must be bounded in practice)."""
        self.loop_depth += 1
        self.visit(node.test)
        for stmt in node.body:
            self.visit(stmt)
        if node.orelse:
            raise SubsetViolation("while-else not supported", node=node)
        self.loop_depth -= 1

    def visit_For(self, node: ast.For):
        """For loop - only range() supported."""
        if not isinstance(node.iter, ast.Call):
            raise SubsetViolation("For loop must iterate over range()", node=node)

        if not (isinstance(node.iter.func, ast.Name) and node.iter.func.id == "range"):
            raise SubsetViolation("For loop must iterate over range()", node=node)

        if not isinstance(node.target, ast.Name):
            raise SubsetViolation("For loop variable must be simple name", node=node)

        self.loop_depth += 1
        for stmt in node.body:
            self.visit(stmt)
        if node.orelse:
            raise SubsetViolation("for-else not supported", node=node)
        self.loop_depth -= 1

    def visit_Return(self, node: ast.Return):
        """Return statement."""
        if node.value:
            self.visit(node.value)

    def visit_Pass(self, node: ast.Pass):
        """Pass is allowed."""
        pass

    def visit_Break(self, node: ast.Break):
        if self.loop_depth == 0:
            raise SubsetViolation("Break outside loop", node=node)

    def visit_Continue(self, node: ast.Continue):
        if self.loop_depth == 0:
            raise SubsetViolation("Continue outside loop", node=node)

    # Rejected statements
    def visit_Import(self, node):
        raise SubsetViolation("Import not supported", node=node)

    def visit_ImportFrom(self, node):
        raise SubsetViolation("Import not supported", node=node)

    def visit_Global(self, node):
        raise SubsetViolation("Global not supported", node=node)

    def visit_Nonlocal(self, node):
        raise SubsetViolation("Nonlocal not supported", node=node)

    def visit_Delete(self, node):
        raise SubsetViolation("Delete not supported", node=node)

    def visit_Assert(self, node):
        raise SubsetViolation("Assert not supported", node=node)

    def visit_Try(self, node):
        raise SubsetViolation("Try/except not supported", node=node)

    def visit_Raise(self, node):
        raise SubsetViolation("Raise not supported", node=node)

    def visit_With(self, node):
        raise SubsetViolation("With not supported", node=node)

    def visit_Match(self, node):
        raise SubsetViolation("Match not supported", node=node)

    # =========================================================================
    # Expressions
    # =========================================================================

    def visit_BinOp(self, node: ast.BinOp):
        """Binary operation."""
        if type(node.op) not in SUPPORTED_BINOPS:
            raise SubsetViolation(
                f"Operator {type(node.op).__name__} not supported",
                node=node
            )
        self.visit(node.left)
        self.visit(node.right)

    def visit_Compare(self, node: ast.Compare):
        """Comparison."""
        if len(node.ops) > 1:
            raise SubsetViolation("Chained comparisons not supported", node=node)
        if type(node.ops[0]) not in SUPPORTED_CMPOPS:
            raise SubsetViolation(
                f"Comparison {type(node.ops[0]).__name__} not supported",
                node=node
            )
        self.visit(node.left)
        for comp in node.comparators:
            self.visit(comp)

    def visit_BoolOp(self, node: ast.BoolOp):
        """Boolean operation."""
        if type(node.op) not in SUPPORTED_BOOLOPS:
            raise SubsetViolation(
                f"Boolean operator {type(node.op).__name__} not supported",
                node=node
            )
        for value in node.values:
            self.visit(value)

    def visit_UnaryOp(self, node: ast.UnaryOp):
        """Unary operation."""
        if type(node.op) not in SUPPORTED_UNARYOPS:
            raise SubsetViolation(
                f"Unary operator {type(node.op).__name__} not supported",
                node=node
            )
        self.visit(node.operand)

    def visit_IfExp(self, node: ast.IfExp):
        """Conditional expression: a if cond else b"""
        self.visit(node.test)
        self.visit(node.body)
        self.visit(node.orelse)

    def visit_Call(self, node: ast.Call):
        """Function call - only built-ins."""
        if isinstance(node.func, ast.Name):
            if node.func.id not in SUPPORTED_BUILTINS:
                raise SubsetViolation(
                    f"Function '{node.func.id}' not supported. "
                    f"Only {SUPPORTED_BUILTINS} allowed.",
                    node=node
                )
        else:
            raise SubsetViolation("Only built-in function calls supported", node=node)

        for arg in node.args:
            self.visit(arg)

    def visit_Attribute(self, node: ast.Attribute):
        """Attribute access: self.x"""
        if not (isinstance(node.value, ast.Name) and node.value.id == "self"):
            raise SubsetViolation("Only self.x attribute access supported", node=node)

    def visit_Name(self, node: ast.Name):
        """Variable reference."""
        pass  # Always allowed

    def visit_Constant(self, node: ast.Constant):
        """Literal value."""
        if not isinstance(node.value, (int, float, bool, type(None))):
            raise SubsetViolation(
                f"Literal type {type(node.value).__name__} not supported",
                node=node
            )

    # Rejected expressions
    def visit_List(self, node):
        raise SubsetViolation("Lists not supported", node=node)

    def visit_Dict(self, node):
        raise SubsetViolation("Dicts not supported", node=node)

    def visit_Set(self, node):
        raise SubsetViolation("Sets not supported", node=node)

    def visit_Tuple(self, node):
        raise SubsetViolation("Tuples not supported (use separate variables)", node=node)

    def visit_Subscript(self, node):
        raise SubsetViolation("Subscript (indexing) not supported", node=node)

    def visit_Lambda(self, node):
        raise SubsetViolation("Lambda not supported", node=node)

    def visit_ListComp(self, node):
        raise SubsetViolation("List comprehension not supported", node=node)

    def visit_DictComp(self, node):
        raise SubsetViolation("Dict comprehension not supported", node=node)

    def visit_SetComp(self, node):
        raise SubsetViolation("Set comprehension not supported", node=node)

    def visit_GeneratorExp(self, node):
        raise SubsetViolation("Generator expression not supported", node=node)

    def visit_Await(self, node):
        raise SubsetViolation("Await not supported", node=node)

    def visit_Yield(self, node):
        raise SubsetViolation("Yield not supported", node=node)

    def visit_YieldFrom(self, node):
        raise SubsetViolation("Yield from not supported", node=node)

    def visit_JoinedStr(self, node):
        raise SubsetViolation("F-strings not supported", node=node)

    def visit_NamedExpr(self, node):
        raise SubsetViolation("Walrus operator not supported", node=node)


def validate_python_subset(code: str) -> ast.Module:
    """
    Validate that code is in the verifiable Python subset.

    Args:
        code: Python source code

    Returns:
        Parsed AST if valid

    Raises:
        SubsetViolation: If code uses unsupported features
    """
    validator = SubsetValidator()
    return validator.validate(code)
