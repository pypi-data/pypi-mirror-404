"""
Fault localization using counterexample and trace.
"""

import re
from dataclasses import dataclass
from typing import Any

from rotalabs_verity.core import Counterexample, PropertyViolation, TraceStep


@dataclass
class FaultLocation:
    """Identified fault location."""
    line_number: int
    statement: str
    variable_written: str
    value_before: Any
    value_after: Any
    confidence: float  # 0-1, higher = more likely


def localize_fault(
    trace: list[TraceStep],
    property_violated: PropertyViolation,
    counterexample: Counterexample
) -> list[FaultLocation]:
    """
    Find which trace steps are responsible for the violation.

    Algorithm:
    1. Parse property to find referenced variables
    2. Find trace steps that write to those variables
    3. Rank by proximity to violation (later = more likely)
    """
    if not trace:
        return []

    # Extract variables from property formula
    violated_vars = extract_property_variables(property_violated.property_formula)

    # Map to state variable names (handle _pre/_post suffixes)
    state_vars = set()
    for var in violated_vars:
        if var.endswith("_post"):
            state_vars.add(var[:-5])
        elif var.endswith("_pre"):
            state_vars.add(var[:-4])
        else:
            state_vars.add(var)

    # Find steps that write to these variables
    faults = []
    for i, step in enumerate(trace):
        # Check what variable changed
        for var_name in state_vars:
            before = step.state_before.get(var_name)
            after = step.state_after.get(var_name)

            if before != after:
                # This step modified a relevant variable
                confidence = (i + 1) / len(trace)  # Later = higher confidence

                faults.append(FaultLocation(
                    line_number=step.line_number,
                    statement=step.source_code,
                    variable_written=var_name,
                    value_before=before,
                    value_after=after,
                    confidence=confidence
                ))

    # Sort by confidence (highest first)
    faults.sort(key=lambda f: -f.confidence)

    # Mark the highest confidence as the primary fault
    if faults:
        # Check if the last write produced a violating value
        for fault in faults:
            if is_violating_value(fault.variable_written, fault.value_after, counterexample):
                fault.confidence = 1.0
                break

    return faults


def extract_property_variables(formula: str) -> set[str]:
    """
    Extract variable names from property formula string.

    Examples:
        "□(x >= 0)" -> {"x"}
        "□(count <= max)" -> {"count", "max"}
    """
    # Remove temporal operators
    cleaned = formula.replace("□", "").replace("◇", "")

    # Find all identifiers
    identifiers = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', cleaned)

    # Filter out operators and keywords
    keywords = {"and", "or", "not", "True", "False", "if", "else"}

    return {id for id in identifiers if id not in keywords}


def is_violating_value(var_name: str, value: Any, cx: Counterexample) -> bool:
    """Check if this value is the violating one in the counterexample."""
    # Check post_state
    post_val = cx.post_state.get(var_name)
    return post_val == value
