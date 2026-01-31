"""
Abductive repair synthesis.

Key insight: Find the weakest precondition that would prevent the violation.
"""

import ast
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from rotalabs_verity.core import ProblemSpec


@dataclass
class RepairSuggestion:
    """Synthesized repair."""
    guard_condition: str      # Python code for the guard
    insert_before_line: int   # Where to insert
    action_if_false: str      # What to do if guard fails


def synthesize_repair(
    fault_line: int,
    fault_statement: str,
    property_formula: str,
    counterexample: Any,
    spec: "ProblemSpec | None" = None
) -> RepairSuggestion | None:
    """
    Synthesize a repair guard using weakest precondition.

    Args:
        fault_line: Line number of the fault
        fault_statement: The faulty statement
        property_formula: The violated property formula
        counterexample: The counterexample that triggered the violation
        spec: Problem specification (used to resolve symbolic bounds)

    Examples:
    - stmt="self.votes_yes += 1", prop="□(votes_yes <= required)"
      → guard="self.votes_yes < 3" (if required=3 from spec)

    - stmt="self.tokens -= 1", prop="□(tokens >= 0)"
      → guard="self.tokens >= 1"

    - stmt="self.votes += 1", prop="□(votes <= max_votes)"
      → guard="self.votes < 5" (if votes bounds=(0,5) from spec)
    """
    try:
        # Parse the fault statement to get target variable, operation, and operand
        target_var, op, operand = parse_update_statement(fault_statement)

        # Parse the property to get bound type and value
        # Pass spec to resolve symbolic bounds to actual values
        prop_var, bound_type, bound_value = parse_property_bound(property_formula, spec)

        # Verify the property is about the same variable we're modifying
        target_base = target_var.replace("self.", "")
        if prop_var != target_base:
            # Property is about a different variable - use fallback
            return _fallback_suggestion(fault_line, fault_statement)

        # Generate guard based on operation and bound type
        guard = generate_guard(target_var, op, operand, bound_type, bound_value)

        if guard is None:
            return _fallback_suggestion(fault_line, fault_statement)

        return RepairSuggestion(
            guard_condition=guard,
            insert_before_line=fault_line,
            action_if_false="pass  # Skip operation"
        )

    except Exception:
        return _fallback_suggestion(fault_line, fault_statement)


def parse_update_statement(stmt: str) -> tuple[str, str, Any]:
    """
    Parse update statement to get target variable, operation, and operand.

    Returns: (target_var, op, operand)
    - target_var: "self.x"
    - op: "add", "sub", "assign"
    - operand: numeric value or variable name

    Examples:
    - "self.x += 1" → ("self.x", "add", 1)
    - "self.x -= 1" → ("self.x", "sub", 1)
    - "self.x = self.x + delta" → ("self.x", "add", "delta")
    - "self.votes = self.votes + 1" → ("self.votes", "add", 1)
    """
    tree = ast.parse(stmt)
    node = tree.body[0]

    if isinstance(node, ast.AugAssign):
        target = ast.unparse(node.target)

        if isinstance(node.op, ast.Add):
            op = "add"
        elif isinstance(node.op, ast.Sub):
            op = "sub"
        else:
            op = "other"

        # Get operand
        if isinstance(node.value, ast.Constant):
            operand = node.value.value
        elif isinstance(node.value, ast.Name):
            operand = node.value.id
        elif isinstance(node.value, ast.Attribute):
            operand = ast.unparse(node.value)
        else:
            operand = ast.unparse(node.value)

        return (target, op, operand)

    elif isinstance(node, ast.Assign):
        target = ast.unparse(node.targets[0])
        value = node.value

        # Handle "self.x = self.x + 1" form
        if isinstance(value, ast.BinOp):
            if isinstance(value.op, ast.Add):
                op = "add"
            elif isinstance(value.op, ast.Sub):
                op = "sub"
            else:
                op = "other"

            # Get operand (right side of binop)
            if isinstance(value.right, ast.Constant):
                operand = value.right.value
            elif isinstance(value.right, ast.Name):
                operand = value.right.id
            elif isinstance(value.right, ast.Attribute):
                operand = ast.unparse(value.right)
            else:
                operand = ast.unparse(value.right)

            return (target, op, operand)

        # Simple assignment
        return (target, "assign", ast.unparse(value))

    raise ValueError(f"Cannot parse statement: {stmt}")


def parse_property_bound(
    formula: str,
    spec: "ProblemSpec | None" = None
) -> tuple[str, str, Any]:
    """
    Parse property formula to extract variable, bound type, and bound value.

    If spec is provided, symbolic bounds are resolved to actual numeric values
    using state variable bounds.

    Returns: (var_name, bound_type, bound_value)
    - var_name: "votes_yes", "tokens", etc.
    - bound_type: "upper" (<=, <) or "lower" (>=, >)
    - bound_value: numeric (resolved from state variable bounds if symbolic)

    Examples:
    - "□(votes_yes <= required)" → ("votes_yes", "upper", 3) if required=3
    - "□(tokens >= 0)" → ("tokens", "lower", 0)
    - "□(votes <= max_votes)" → ("votes", "upper", 5) if votes bounds=(0,5)
    """
    # Remove temporal operators and whitespace
    cleaned = formula.replace("□", "").replace("◇", "").strip()

    # Remove outer parentheses
    while cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = cleaned[1:-1].strip()

    # Try patterns for upper bounds: var <= bound, var < bound
    upper_patterns = [
        r'(\w+)\s*<=\s*(\w+)',
        r'(\w+)\s*<\s*(\w+)',
    ]

    for pattern in upper_patterns:
        match = re.search(pattern, cleaned)
        if match:
            var_name = match.group(1)
            bound_str = match.group(2)
            bound_value = _parse_bound_value(bound_str)

            # If bound is symbolic and we have a spec, resolve it
            if isinstance(bound_value, str) and spec is not None:
                resolved = _resolve_symbolic_bound(var_name, bound_value, "upper", spec)
                if resolved is not None:
                    bound_value = resolved

            return (var_name, "upper", bound_value)

    # Try patterns for lower bounds: var >= bound, var > bound
    lower_patterns = [
        r'(\w+)\s*>=\s*(\w+)',
        r'(\w+)\s*>\s*(\w+)',
    ]

    for pattern in lower_patterns:
        match = re.search(pattern, cleaned)
        if match:
            var_name = match.group(1)
            bound_str = match.group(2)
            bound_value = _parse_bound_value(bound_str)

            # If bound is symbolic and we have a spec, resolve it
            if isinstance(bound_value, str) and spec is not None:
                resolved = _resolve_symbolic_bound(var_name, bound_value, "lower", spec)
                if resolved is not None:
                    bound_value = resolved

            return (var_name, "lower", bound_value)

    raise ValueError(f"Cannot parse property formula: {formula}")


def _parse_bound_value(bound_str: str) -> Any:
    """Parse bound value as numeric or symbolic."""
    try:
        # Try integer first
        return int(bound_str)
    except ValueError:
        pass

    try:
        # Try float
        return float(bound_str)
    except ValueError:
        pass

    # Symbolic bound (e.g., "required", "capacity", "limit")
    return bound_str


def _resolve_symbolic_bound(
    var_name: str,
    bound_name: str,
    bound_type: str,
    spec: "ProblemSpec"
) -> int | float | None:
    """
    Resolve symbolic bound name to actual value from state variable bounds.

    For var "votes" with bounds (0, 5) and bound_type "upper":
    - "max_votes" resolves to 5 (upper bound)

    For var "tokens" with bounds (0, 100) and bound_type "lower":
    - "min_tokens" resolves to 0 (lower bound)

    Args:
        var_name: Name of the variable in the property (e.g., "votes")
        bound_name: Symbolic bound name (e.g., "max_votes")
        bound_type: "upper" or "lower"
        spec: Problem specification with state variable definitions

    Returns:
        Resolved numeric bound, or None if cannot resolve
    """
    # Find the state variable
    for sv in spec.state_variables:
        if sv.name == var_name:
            if sv.bounds:
                lower, upper = sv.bounds

                if bound_type == "upper" and upper is not None:
                    return upper
                elif bound_type == "lower" and lower is not None:
                    return lower

    # Could not resolve - return None to keep symbolic name
    return None


def generate_guard(
    target_var: str,
    op: str,
    operand: Any,
    bound_type: str,
    bound_value: Any
) -> str | None:
    """
    Generate guard condition based on operation and bound type.

    For increment (x += n) with upper bound (x <= B):
    - Post: x + n <= B
    - Pre (guard): x <= B - n, or x < B if n=1

    For decrement (x -= n) with lower bound (x >= B):
    - Post: x - n >= B
    - Pre (guard): x >= B + n

    Args:
        target_var: "self.votes_yes"
        op: "add" or "sub"
        operand: 1 or "delta"
        bound_type: "upper" or "lower"
        bound_value: 3 or "required"
    """
    # Format the bound for Python code
    # Note: Don't add self. for symbolic bounds - they might be constants
    # The LLM should interpret them from the problem description
    if isinstance(bound_value, str):
        # Keep symbolic bounds as-is (e.g., "required" -> "required")
        # This lets the LLM resolve whether it's a constant or needs self.
        bound_python = bound_value
    else:
        bound_python = str(bound_value)

    # Format the operand for Python code
    if isinstance(operand, str) and not operand.startswith("self."):
        if operand.isidentifier():
            operand_python = f"self.{operand}"
        else:
            operand_python = operand
    else:
        operand_python = str(operand)

    if op == "add" and bound_type == "upper":
        # x += n with x <= B → guard: x + n <= B, i.e., x <= B - n
        # For n=1: x < B (simpler form)
        if operand == 1:
            return f"{target_var} < {bound_python}"
        elif isinstance(operand, (int, float)):
            if isinstance(bound_value, (int, float)):
                # Both numeric: compute directly
                return f"{target_var} <= {bound_value - operand}"
            else:
                # Symbolic bound
                return f"{target_var} <= {bound_python} - {operand}"
        else:
            # Symbolic operand
            return f"{target_var} + {operand_python} <= {bound_python}"

    elif op == "sub" and bound_type == "lower":
        # x -= n with x >= B → guard: x - n >= B, i.e., x >= B + n
        if isinstance(bound_value, (int, float)) and bound_value == 0:
            # Special case: x >= 0 → guard: x >= n
            if isinstance(operand, (int, float)):
                return f"{target_var} >= {operand}"
            else:
                return f"{target_var} >= {operand_python}"
        elif isinstance(operand, (int, float)):
            if isinstance(bound_value, (int, float)):
                return f"{target_var} >= {bound_value + operand}"
            else:
                return f"{target_var} >= {bound_python} + {operand}"
        else:
            return f"{target_var} - {operand_python} >= {bound_python}"

    elif op == "sub" and bound_type == "upper":
        # x -= n with x <= B → usually safe (decreasing toward bound)
        # But could underflow if there's also a lower bound
        return None  # No guard needed for this case

    elif op == "add" and bound_type == "lower":
        # x += n with x >= B → usually safe (increasing away from bound)
        return None  # No guard needed for this case

    elif op == "assign":
        # Direct assignment - check if new value satisfies bound
        return None  # Complex case, skip

    return None


def _fallback_suggestion(fault_line: int, fault_statement: str) -> RepairSuggestion:
    """Generate fallback suggestion when analysis fails."""
    return RepairSuggestion(
        guard_condition=f"# TODO: Add guard before: {fault_statement}",
        insert_before_line=fault_line,
        action_if_false="pass"
    )
