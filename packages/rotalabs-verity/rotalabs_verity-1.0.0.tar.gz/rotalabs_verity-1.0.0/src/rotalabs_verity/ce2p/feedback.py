"""
Generate structured feedback from CE2P components.
"""

from typing import TYPE_CHECKING

from rotalabs_verity.ce2p.abducer import synthesize_repair
from rotalabs_verity.ce2p.executor import execute_on_counterexample
from rotalabs_verity.ce2p.localizer import localize_fault
from rotalabs_verity.core import (
    StructuredFeedback,
    VerificationResult,
)

if TYPE_CHECKING:
    from rotalabs_verity.core import ProblemSpec


def generate_feedback(
    code: str,
    result: VerificationResult,
    spec: "ProblemSpec | None" = None
) -> StructuredFeedback | None:
    """
    Generate structured feedback from verification result.

    This is the main CE2P entry point.

    Args:
        code: The code being verified
        result: Verification result with counterexample
        spec: Problem specification (used to resolve symbolic bounds in repairs)
    """
    if result.counterexample is None or result.property_violated is None:
        return None

    cx = result.counterexample
    prop = result.property_violated

    # Step 1: Execute to get trace
    trace = execute_on_counterexample(code, cx)

    # Step 2: Localize fault
    faults = localize_fault(trace.steps, prop, cx)

    if not faults:
        # Fallback if no fault found
        return _fallback_feedback(code, result)

    primary_fault = faults[0]

    # Mark fault in trace
    for step in trace.steps:
        if step.line_number == primary_fault.line_number:
            step.is_fault = True

    # Step 3: Synthesize repair (pass spec to resolve symbolic bounds)
    repair = synthesize_repair(
        primary_fault.line_number,
        primary_fault.statement,
        prop.property_formula,
        cx,
        spec=spec
    )

    # Step 4: Generate natural language explanations
    root_cause = generate_root_cause(primary_fault, prop, cx)
    suggested_fix = generate_fix_suggestion(repair, primary_fault)

    return StructuredFeedback(
        property_violated=prop,
        counterexample=cx,
        execution_trace=trace.steps,
        fault_line=primary_fault.line_number,
        root_cause=root_cause,
        suggested_fix=suggested_fix,
        repair_guard=repair.guard_condition if repair else ""
    )


def generate_root_cause(fault, prop, cx) -> str:
    """Generate root cause explanation."""
    return (
        f"Property '{prop.property_name}' was violated.\n"
        f"\n"
        f"At line {fault.line_number}: `{fault.statement}`\n"
        f"  - Variable '{fault.variable_written}' changed from "
        f"{_fmt(fault.value_before)} to {_fmt(fault.value_after)}\n"
        f"\n"
        f"This violates the constraint: {prop.property_formula}\n"
        f"\n"
        f"The statement executed without checking the precondition."
    )


def generate_fix_suggestion(repair, fault) -> str:
    """Generate fix suggestion."""
    if repair and repair.guard_condition:
        return (
            f"Add a guard before line {fault.line_number}:\n"
            f"\n"
            f"```python\n"
            f"if {repair.guard_condition}:\n"
            f"    {fault.statement}\n"
            f"else:\n"
            f"    {repair.action_if_false}\n"
            f"```"
        )
    else:
        return (
            f"Check the precondition before line {fault.line_number}:\n"
            f"`{fault.statement}`"
        )


def _fallback_feedback(code: str, result: VerificationResult) -> StructuredFeedback:
    """Fallback when full analysis fails."""
    return StructuredFeedback(
        property_violated=result.property_violated,
        counterexample=result.counterexample,
        execution_trace=[],
        fault_line=0,
        root_cause=f"Property '{result.property_violated.property_name}' violated. "
                   f"Counterexample: {result.counterexample.to_dict()}",
        suggested_fix="Review the implementation logic.",
        repair_guard=""
    )


def _fmt(value) -> str:
    """Format value for display."""
    if value is None:
        return "None"
    if isinstance(value, float):
        if value == int(value):
            return str(int(value))
        return f"{value:.4f}"
    return str(value)
