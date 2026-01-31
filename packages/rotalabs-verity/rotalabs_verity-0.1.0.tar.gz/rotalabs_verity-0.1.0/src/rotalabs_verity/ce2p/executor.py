"""
Concrete execution for trace generation.

Unlike the symbolic executor (which produces Z3 formulas),
this executor runs with concrete values to show exactly what happened.
"""

import ast
from dataclasses import dataclass
from typing import Any

from rotalabs_verity.core import Counterexample, TraceStep


@dataclass
class ExecutionTrace:
    """Result of concrete execution."""
    steps: list[TraceStep]
    final_state: dict[str, Any]
    return_value: Any
    completed: bool = True
    error: str | None = None


class ConcreteExecutor:
    """
    Executes Python code with concrete values.

    Used by CE2P to generate execution traces showing
    exactly how the counterexample leads to a violation.
    """

    MAX_ITERATIONS = 100

    def __init__(self, initial_state: dict[str, Any], inputs: dict[str, Any]):
        """
        Initialize executor.

        Args:
            initial_state: State variable values (self.x)
            inputs: Input parameter values
        """
        self.state = dict(initial_state)
        self.inputs = dict(inputs)
        self.trace: list[TraceStep] = []
        self.iteration_count = 0

    def execute(self, code: str) -> ExecutionTrace:
        """
        Execute code and return trace.

        Args:
            code: Python source code

        Returns:
            ExecutionTrace with all steps
        """
        try:
            tree = ast.parse(code)
            func = self._find_function(tree)

            # Add inputs to local scope
            for name, value in self.inputs.items():
                self.state[name] = value

            result = self._execute_body(func.body)

            return ExecutionTrace(
                steps=self.trace,
                final_state=self._get_state_vars(),
                return_value=result,
                completed=True
            )
        except Exception as e:
            return ExecutionTrace(
                steps=self.trace,
                final_state=self._get_state_vars(),
                return_value=None,
                completed=False,
                error=str(e)
            )

    def _find_function(self, tree: ast.Module) -> ast.FunctionDef:
        """Find the function definition."""
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                return node
        raise ValueError("No function found")

    def _execute_body(self, body: list[ast.stmt]) -> Any:
        """Execute a list of statements."""
        for stmt in body:
            result = self._execute_stmt(stmt)
            if result is not None:  # Return statement
                return result
        return None

    def _execute_stmt(self, stmt: ast.stmt) -> Any:
        """Execute a single statement."""
        state_before = dict(self.state)

        if isinstance(stmt, ast.Assign):
            target = self._get_target_name(stmt.targets[0])
            value = self._eval(stmt.value)
            self.state[target] = value

            self.trace.append(TraceStep(
                line_number=stmt.lineno,
                source_code=ast.unparse(stmt),
                state_before=self._filter_state(state_before),
                state_after=self._filter_state(self.state),
                is_fault=False
            ))

        elif isinstance(stmt, ast.AugAssign):
            target = self._get_target_name(stmt.target)
            current = self.state.get(target, 0)
            operand = self._eval(stmt.value)
            value = self._apply_op(stmt.op, current, operand)
            self.state[target] = value

            self.trace.append(TraceStep(
                line_number=stmt.lineno,
                source_code=ast.unparse(stmt),
                state_before=self._filter_state(state_before),
                state_after=self._filter_state(self.state),
                is_fault=False
            ))

        elif isinstance(stmt, ast.AnnAssign):
            if stmt.value is not None:
                target = self._get_target_name(stmt.target)
                value = self._eval(stmt.value)
                self.state[target] = value

                self.trace.append(TraceStep(
                    line_number=stmt.lineno,
                    source_code=ast.unparse(stmt),
                    state_before=self._filter_state(state_before),
                    state_after=self._filter_state(self.state),
                    is_fault=False
                ))

        elif isinstance(stmt, ast.If):
            condition = self._eval(stmt.test)

            self.trace.append(TraceStep(
                line_number=stmt.lineno,
                source_code=f"if {ast.unparse(stmt.test)}: # {condition}",
                state_before=self._filter_state(state_before),
                state_after=self._filter_state(self.state),
                is_fault=False
            ))

            if condition:
                return self._execute_body(stmt.body)
            elif stmt.orelse:
                return self._execute_body(stmt.orelse)

        elif isinstance(stmt, ast.While):
            while True:
                self.iteration_count += 1
                if self.iteration_count > self.MAX_ITERATIONS:
                    raise RuntimeError("Loop iteration limit exceeded")

                condition = self._eval(stmt.test)
                if not condition:
                    break

                result = self._execute_body(stmt.body)
                if result is not None:
                    return result

        elif isinstance(stmt, ast.For):
            iter_val = self._eval(stmt.iter)
            var_name = stmt.target.id

            for item in iter_val:
                self.state[var_name] = item
                result = self._execute_body(stmt.body)
                if result is not None:
                    return result

        elif isinstance(stmt, ast.Return):
            value = self._eval(stmt.value) if stmt.value else None

            self.trace.append(TraceStep(
                line_number=stmt.lineno,
                source_code=ast.unparse(stmt),
                state_before=self._filter_state(state_before),
                state_after=self._filter_state(self.state),
                is_fault=False
            ))

            return value

        elif isinstance(stmt, ast.Pass):
            pass

        elif isinstance(stmt, ast.Expr):
            self._eval(stmt.value)

        elif isinstance(stmt, ast.Break):
            pass  # Handled by loop

        elif isinstance(stmt, ast.Continue):
            pass  # Handled by loop

        return None

    def _eval(self, expr: ast.expr) -> Any:
        """Evaluate expression."""
        if isinstance(expr, ast.Constant):
            return expr.value

        elif isinstance(expr, ast.Name):
            if expr.id == "True":
                return True
            elif expr.id == "False":
                return False
            return self.state.get(expr.id, 0)

        elif isinstance(expr, ast.Attribute):
            if isinstance(expr.value, ast.Name) and expr.value.id == "self":
                return self.state.get(expr.attr, 0)
            raise ValueError(f"Unsupported attribute: {ast.unparse(expr)}")

        elif isinstance(expr, ast.BinOp):
            left = self._eval(expr.left)
            right = self._eval(expr.right)
            return self._apply_op(expr.op, left, right)

        elif isinstance(expr, ast.Compare):
            left = self._eval(expr.left)
            right = self._eval(expr.comparators[0])
            return self._apply_cmp(expr.ops[0], left, right)

        elif isinstance(expr, ast.BoolOp):
            if isinstance(expr.op, ast.And):
                return all(self._eval(v) for v in expr.values)
            else:  # Or
                return any(self._eval(v) for v in expr.values)

        elif isinstance(expr, ast.UnaryOp):
            operand = self._eval(expr.operand)
            if isinstance(expr.op, ast.Not):
                return not operand
            elif isinstance(expr.op, ast.USub):
                return -operand

        elif isinstance(expr, ast.IfExp):
            if self._eval(expr.test):
                return self._eval(expr.body)
            else:
                return self._eval(expr.orelse)

        elif isinstance(expr, ast.Call):
            if isinstance(expr.func, ast.Name):
                name = expr.func.id
                args = [self._eval(a) for a in expr.args]

                if name == "min":
                    return min(args)
                elif name == "max":
                    return max(args)
                elif name == "abs":
                    return abs(args[0])
                elif name == "range":
                    return range(*args)

        raise ValueError(f"Cannot evaluate: {ast.unparse(expr)}")

    def _apply_op(self, op: ast.operator, left: Any, right: Any) -> Any:
        """Apply binary operator."""
        if isinstance(op, ast.Add):
            return left + right
        elif isinstance(op, ast.Sub):
            return left - right
        elif isinstance(op, ast.Mult):
            return left * right
        elif isinstance(op, ast.Div):
            return left / right
        elif isinstance(op, ast.FloorDiv):
            return left // right
        elif isinstance(op, ast.Mod):
            return left % right
        raise ValueError(f"Unknown operator: {type(op)}")

    def _apply_cmp(self, op: ast.cmpop, left: Any, right: Any) -> bool:
        """Apply comparison operator."""
        if isinstance(op, ast.Lt):
            return left < right
        elif isinstance(op, ast.LtE):
            return left <= right
        elif isinstance(op, ast.Gt):
            return left > right
        elif isinstance(op, ast.GtE):
            return left >= right
        elif isinstance(op, ast.Eq):
            return left == right
        elif isinstance(op, ast.NotEq):
            return left != right
        raise ValueError(f"Unknown comparison: {type(op)}")

    def _get_target_name(self, target: ast.expr) -> str:
        """Get variable name from assignment target."""
        if isinstance(target, ast.Name):
            return target.id
        elif isinstance(target, ast.Attribute):
            return target.attr
        raise ValueError(f"Unknown target: {type(target)}")

    def _filter_state(self, state: dict) -> dict:
        """Filter state to only include relevant variables."""
        # Exclude inputs and local variables starting with _
        return {k: v for k, v in state.items()
                if not k.startswith('_') and k not in self.inputs}

    def _get_state_vars(self) -> dict:
        """Get state variables only."""
        return self._filter_state(self.state)


def execute_on_counterexample(
    code: str,
    counterexample: Counterexample
) -> ExecutionTrace:
    """
    Execute code on counterexample values.

    Convenience function for CE2P.
    """
    executor = ConcreteExecutor(
        initial_state=dict(counterexample.pre_state),
        inputs=dict(counterexample.inputs)
    )
    return executor.execute(code)
