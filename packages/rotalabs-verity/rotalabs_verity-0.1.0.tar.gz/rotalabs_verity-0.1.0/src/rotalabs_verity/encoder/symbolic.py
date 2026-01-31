"""
Symbolic execution engine.

Executes Python AST symbolically, producing Z3 formulas
that represent the program's behavior.
"""

import ast
from dataclasses import dataclass, field
from typing import Any

import z3

from rotalabs_verity.core import ProblemSpec


class EncodingError(Exception):
    """Error during symbolic execution."""
    pass


@dataclass
class SymbolicState:
    """
    State during symbolic execution.

    Variables map to Z3 expressions.
    Path condition is the conjunction of branch conditions.
    """
    variables: dict[str, z3.ExprRef] = field(default_factory=dict)
    path_condition: z3.BoolRef = field(default_factory=lambda: z3.BoolVal(True))
    return_value: z3.ExprRef | None = None
    has_returned: z3.BoolRef = field(default_factory=lambda: z3.BoolVal(False))

    def copy(self) -> "SymbolicState":
        """Create a copy of this state."""
        return SymbolicState(
            variables=dict(self.variables),
            path_condition=self.path_condition,
            return_value=self.return_value,
            has_returned=self.has_returned
        )


class SymbolicExecutor:
    """
    Symbolically executes Python AST.

    Produces Z3 formulas representing program semantics.
    """

    # Maximum loop unrolling depth
    MAX_UNROLL = 10

    def __init__(self, spec: ProblemSpec):
        """
        Initialize executor with problem specification.

        Args:
            spec: Problem specification for variable types
        """
        self.spec = spec
        self.state_var_types: dict[str, str] = {
            sv.name: sv.var_type for sv in spec.state_variables
        }
        self.input_var_types: dict[str, str] = {
            iv.name: iv.var_type for iv in spec.input_variables
        }

    def execute(
        self,
        body: list[ast.stmt],
        pre_state: dict[str, z3.ExprRef],
        inputs: dict[str, z3.ExprRef]
    ) -> tuple[dict[str, z3.ExprRef], z3.ExprRef, z3.BoolRef]:
        """
        Execute method body symbolically.

        Args:
            body: List of AST statements
            pre_state: Initial state variables (Z3)
            inputs: Input parameters (Z3)

        Returns:
            Tuple of (post_state, return_value, transition_constraint)

        Raises:
            EncodingError: If encoding fails
        """
        # Initialize state with pre_state and inputs
        state = SymbolicState()
        state.variables.update(pre_state)
        state.variables.update(inputs)

        # Execute body
        state = self._execute_body(body, state)

        # Extract post state (only state variables, not inputs)
        post_state = {
            name: state.variables.get(name, pre_state[name])
            for name in pre_state.keys()
        }

        # Get return value (default to False if no return)
        return_value = state.return_value
        if return_value is None:
            return_value = z3.BoolVal(False)

        # Build transition constraint
        transition = state.path_condition

        return post_state, return_value, transition

    def _execute_body(self, body: list[ast.stmt], state: SymbolicState) -> SymbolicState:
        """Execute a list of statements."""
        for stmt in body:
            state = self._execute_stmt(stmt, state)
        return state

    def _execute_stmt(self, stmt: ast.stmt, state: SymbolicState) -> SymbolicState:
        """Execute a single statement."""
        if isinstance(stmt, ast.Assign):
            return self._execute_assign(stmt, state)
        elif isinstance(stmt, ast.AugAssign):
            return self._execute_aug_assign(stmt, state)
        elif isinstance(stmt, ast.AnnAssign):
            return self._execute_ann_assign(stmt, state)
        elif isinstance(stmt, ast.If):
            return self._execute_if(stmt, state)
        elif isinstance(stmt, ast.While):
            return self._execute_while(stmt, state)
        elif isinstance(stmt, ast.For):
            return self._execute_for(stmt, state)
        elif isinstance(stmt, ast.Return):
            return self._execute_return(stmt, state)
        elif isinstance(stmt, ast.Pass):
            return state
        elif isinstance(stmt, ast.Expr):
            # Expression statement (side-effect only)
            self._eval_expr(stmt.value, state)
            return state
        elif isinstance(stmt, ast.Break):
            # Break is handled by loop
            return state
        elif isinstance(stmt, ast.Continue):
            # Continue is handled by loop
            return state
        else:
            raise EncodingError(f"Unsupported statement: {type(stmt).__name__}")

    def _execute_assign(self, stmt: ast.Assign, state: SymbolicState) -> SymbolicState:
        """Execute assignment: x = expr or self.x = expr"""
        target = stmt.targets[0]
        value = self._eval_expr(stmt.value, state)

        var_name = self._get_var_name(target)
        state.variables[var_name] = value

        return state

    def _execute_aug_assign(self, stmt: ast.AugAssign, state: SymbolicState) -> SymbolicState:
        """Execute augmented assignment: x += expr"""
        var_name = self._get_var_name(stmt.target)
        current = state.variables.get(var_name)
        if current is None:
            raise EncodingError(f"Variable '{var_name}' not initialized")

        operand = self._eval_expr(stmt.value, state)
        new_value = self._apply_binop(stmt.op, current, operand)

        state.variables[var_name] = new_value
        return state

    def _execute_ann_assign(self, stmt: ast.AnnAssign, state: SymbolicState) -> SymbolicState:
        """Execute annotated assignment."""
        if stmt.value is not None:
            var_name = self._get_var_name(stmt.target)
            value = self._eval_expr(stmt.value, state)
            state.variables[var_name] = value
        return state

    def _execute_if(self, stmt: ast.If, state: SymbolicState) -> SymbolicState:
        """
        Execute if statement using ITE (if-then-else) encoding.

        For each variable, we compute:
        var_new = If(cond, var_then, var_else)
        """
        condition = self._eval_expr(stmt.test, state)

        # Execute then branch
        then_state = state.copy()
        then_state = self._execute_body(stmt.body, then_state)

        # Execute else branch
        else_state = state.copy()
        if stmt.orelse:
            else_state = self._execute_body(stmt.orelse, else_state)

        # Merge states using ITE
        merged = state.copy()

        # Collect all variables from both branches
        all_vars = set(then_state.variables.keys()) | set(else_state.variables.keys())

        for var_name in all_vars:
            then_val = then_state.variables.get(var_name, state.variables.get(var_name))
            else_val = else_state.variables.get(var_name, state.variables.get(var_name))

            if then_val is not None and else_val is not None:
                merged.variables[var_name] = z3.If(condition, then_val, else_val)
            elif then_val is not None:
                merged.variables[var_name] = then_val
            elif else_val is not None:
                merged.variables[var_name] = else_val

        # Merge return values
        if then_state.return_value is not None or else_state.return_value is not None:
            then_ret = then_state.return_value if then_state.return_value is not None else state.return_value
            else_ret = else_state.return_value if else_state.return_value is not None else state.return_value

            if then_ret is not None and else_ret is not None:
                merged.return_value = z3.If(condition, then_ret, else_ret)
            elif then_ret is not None:
                merged.return_value = z3.If(condition, then_ret, merged.return_value) if merged.return_value else then_ret
            elif else_ret is not None:
                merged.return_value = z3.If(z3.Not(condition), else_ret, merged.return_value) if merged.return_value else else_ret

        # Merge has_returned flags
        merged.has_returned = z3.Or(
            z3.And(condition, then_state.has_returned),
            z3.And(z3.Not(condition), else_state.has_returned)
        )

        return merged

    def _execute_while(self, stmt: ast.While, state: SymbolicState) -> SymbolicState:
        """
        Execute while loop by unrolling.

        Unroll up to MAX_UNROLL iterations.
        """
        for _ in range(self.MAX_UNROLL):
            condition = self._eval_expr(stmt.test, state)

            # Execute body conditionally
            body_state = state.copy()
            body_state = self._execute_body(stmt.body, body_state)

            # Merge: if condition is true, use body_state, else keep state
            for var_name in set(body_state.variables.keys()) | set(state.variables.keys()):
                body_val = body_state.variables.get(var_name)
                orig_val = state.variables.get(var_name)

                if body_val is not None and orig_val is not None:
                    state.variables[var_name] = z3.If(condition, body_val, orig_val)
                elif body_val is not None:
                    state.variables[var_name] = body_val

            # Handle return in loop body
            if body_state.return_value is not None:
                if state.return_value is not None:
                    state.return_value = z3.If(
                        z3.And(condition, z3.Not(state.has_returned)),
                        body_state.return_value,
                        state.return_value
                    )
                else:
                    state.return_value = z3.If(condition, body_state.return_value, state.return_value)

        return state

    def _execute_for(self, stmt: ast.For, state: SymbolicState) -> SymbolicState:
        """
        Execute for loop over range.

        Unroll the loop for small constant ranges.
        """
        # Get range arguments
        if not isinstance(stmt.iter, ast.Call):
            raise EncodingError("For loop must iterate over range()")

        range_args = [self._eval_expr(arg, state) for arg in stmt.iter.args]

        # Try to get concrete bounds
        if len(range_args) == 1:
            start, end, step = 0, range_args[0], 1
        elif len(range_args) == 2:
            start, end, step = range_args[0], range_args[1], 1
        else:
            start, end, step = range_args[0], range_args[1], range_args[2]

        # For symbolic bounds, unroll a fixed number of times
        loop_var = stmt.target.id

        # Unroll loop
        for i in range(self.MAX_UNROLL):
            # Condition: i < end (for simple case)
            if isinstance(end, int):
                if i >= end:
                    break
                state.variables[loop_var] = z3.IntVal(i)
            else:
                # Symbolic bound
                idx = z3.IntVal(i) if isinstance(start, int) else start + i
                state.variables[loop_var] = idx
                # Add path condition that we're in bounds
                in_bounds = idx < end if isinstance(step, int) and step > 0 else idx > end

                body_state = state.copy()
                body_state = self._execute_body(stmt.body, body_state)

                # Merge conditionally
                for var_name in body_state.variables:
                    if var_name in state.variables:
                        state.variables[var_name] = z3.If(
                            in_bounds,
                            body_state.variables[var_name],
                            state.variables[var_name]
                        )
                    else:
                        state.variables[var_name] = body_state.variables[var_name]
                continue

            state = self._execute_body(stmt.body, state)

        return state

    def _execute_return(self, stmt: ast.Return, state: SymbolicState) -> SymbolicState:
        """Execute return statement."""
        if stmt.value is not None:
            value = self._eval_expr(stmt.value, state)
        else:
            value = z3.BoolVal(True)  # Default return

        # Merge with existing return value based on path
        if state.return_value is not None:
            # If we already have a return value, only update if we haven't returned yet
            state.return_value = z3.If(
                state.has_returned,
                state.return_value,
                value
            )
        else:
            state.return_value = value

        state.has_returned = z3.BoolVal(True)
        return state

    def _eval_expr(self, expr: ast.expr, state: SymbolicState) -> z3.ExprRef:
        """Evaluate expression to Z3."""
        if isinstance(expr, ast.Constant):
            return self._make_constant(expr.value)

        elif isinstance(expr, ast.Name):
            var_name = expr.id
            if var_name in state.variables:
                return state.variables[var_name]
            elif var_name == "True":
                return z3.BoolVal(True)
            elif var_name == "False":
                return z3.BoolVal(False)
            else:
                raise EncodingError(f"Unknown variable: {var_name}")

        elif isinstance(expr, ast.Attribute):
            # self.x -> look up x
            if isinstance(expr.value, ast.Name) and expr.value.id == "self":
                var_name = expr.attr
                if var_name in state.variables:
                    return state.variables[var_name]
                else:
                    raise EncodingError(f"Unknown state variable: {var_name}")
            raise EncodingError(f"Unsupported attribute: {ast.unparse(expr)}")

        elif isinstance(expr, ast.BinOp):
            left = self._eval_expr(expr.left, state)
            right = self._eval_expr(expr.right, state)
            return self._apply_binop(expr.op, left, right)

        elif isinstance(expr, ast.Compare):
            left = self._eval_expr(expr.left, state)
            right = self._eval_expr(expr.comparators[0], state)
            return self._apply_cmpop(expr.ops[0], left, right)

        elif isinstance(expr, ast.BoolOp):
            values = [self._eval_expr(v, state) for v in expr.values]
            if isinstance(expr.op, ast.And):
                return z3.And(*values)
            else:  # Or
                return z3.Or(*values)

        elif isinstance(expr, ast.UnaryOp):
            operand = self._eval_expr(expr.operand, state)
            if isinstance(expr.op, ast.Not):
                return z3.Not(operand)
            elif isinstance(expr.op, ast.USub):
                return -operand
            raise EncodingError(f"Unsupported unary op: {type(expr.op)}")

        elif isinstance(expr, ast.IfExp):
            cond = self._eval_expr(expr.test, state)
            then_val = self._eval_expr(expr.body, state)
            else_val = self._eval_expr(expr.orelse, state)
            return z3.If(cond, then_val, else_val)

        elif isinstance(expr, ast.Call):
            return self._eval_call(expr, state)

        else:
            raise EncodingError(f"Unsupported expression: {type(expr).__name__}")

    def _eval_call(self, expr: ast.Call, state: SymbolicState) -> z3.ExprRef:
        """Evaluate function call."""
        if not isinstance(expr.func, ast.Name):
            raise EncodingError("Only built-in function calls supported")

        func_name = expr.func.id
        args = [self._eval_expr(arg, state) for arg in expr.args]

        if func_name == "min":
            if len(args) == 2:
                return z3.If(args[0] <= args[1], args[0], args[1])
            else:
                result = args[0]
                for arg in args[1:]:
                    result = z3.If(result <= arg, result, arg)
                return result

        elif func_name == "max":
            if len(args) == 2:
                return z3.If(args[0] >= args[1], args[0], args[1])
            else:
                result = args[0]
                for arg in args[1:]:
                    result = z3.If(result >= arg, result, arg)
                return result

        elif func_name == "abs":
            arg = args[0]
            return z3.If(arg >= 0, arg, -arg)

        elif func_name == "range":
            # Range is handled by for loop
            raise EncodingError("range() should only be used in for loops")

        else:
            raise EncodingError(f"Unknown function: {func_name}")

    def _apply_binop(self, op: ast.operator, left: z3.ExprRef, right: z3.ExprRef) -> z3.ExprRef:
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
            # Z3 integer division
            return left / right  # For reals, this is regular division
        elif isinstance(op, ast.Mod):
            return left % right
        else:
            raise EncodingError(f"Unsupported operator: {type(op).__name__}")

    def _apply_cmpop(self, op: ast.cmpop, left: z3.ExprRef, right: z3.ExprRef) -> z3.BoolRef:
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
        else:
            raise EncodingError(f"Unsupported comparison: {type(op).__name__}")

    def _get_var_name(self, target: ast.expr) -> str:
        """Get variable name from assignment target."""
        if isinstance(target, ast.Name):
            return target.id
        elif isinstance(target, ast.Attribute):
            # self.x -> x
            return target.attr
        else:
            raise EncodingError(f"Unsupported assignment target: {type(target)}")

    def _make_constant(self, value: Any) -> z3.ExprRef:
        """Create Z3 constant from Python value."""
        if isinstance(value, bool):
            return z3.BoolVal(value)
        elif isinstance(value, int):
            return z3.IntVal(value)
        elif isinstance(value, float):
            return z3.RealVal(value)
        elif value is None:
            return z3.BoolVal(False)
        else:
            raise EncodingError(f"Unsupported constant type: {type(value)}")
