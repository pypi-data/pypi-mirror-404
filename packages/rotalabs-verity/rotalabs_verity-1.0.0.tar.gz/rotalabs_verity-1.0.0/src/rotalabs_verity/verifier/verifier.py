"""
Verifier module.

Uses Z3 to check encoded programs against properties.
"""

import time
from typing import Any

import z3

from rotalabs_verity.core import (
    Counterexample,
    ProblemSpec,
    Property,
    PropertyViolation,
    VerificationResult,
    VerificationStatus,
)
from rotalabs_verity.encoder import EncodingError, EncodingResult, ParseError, encode_method


def verify(
    code: str,
    spec: ProblemSpec,
    timeout_ms: int = 30000
) -> VerificationResult:
    """
    Verify code against all properties in spec.

    Args:
        code: Python source code
        spec: Problem specification with properties
        timeout_ms: Z3 solver timeout in milliseconds

    Returns:
        VerificationResult with status and counterexample if found
    """
    start_time = time.time()

    # Step 1: Encode the code
    try:
        encoding = encode_method(code, spec)
    except ParseError as e:
        return VerificationResult(
            status=VerificationStatus.PARSE_ERROR,
            error_message=str(e),
            verification_time_ms=(time.time() - start_time) * 1000
        )
    except EncodingError as e:
        return VerificationResult(
            status=VerificationStatus.ENCODING_ERROR,
            error_message=str(e),
            verification_time_ms=(time.time() - start_time) * 1000
        )
    except Exception as e:
        return VerificationResult(
            status=VerificationStatus.ENCODING_ERROR,
            error_message=f"Unexpected encoding error: {e}",
            verification_time_ms=(time.time() - start_time) * 1000
        )

    # Step 2: Check each property
    for prop in spec.properties:
        result = _check_property(encoding, prop, spec, timeout_ms)

        if result.status != VerificationStatus.VERIFIED:
            result.verification_time_ms = (time.time() - start_time) * 1000
            return result

    # All properties verified
    return VerificationResult(
        status=VerificationStatus.VERIFIED,
        verification_time_ms=(time.time() - start_time) * 1000
    )


def _check_property(
    encoding: EncodingResult,
    prop: Property,
    spec: ProblemSpec,
    timeout_ms: int
) -> VerificationResult:
    """
    Check a single property.

    We check: ∃ pre, inputs. transition ∧ ¬property

    If SAT, we have a counterexample.
    If UNSAT, the property holds.
    """
    solver = z3.Solver()
    solver.set("timeout", timeout_ms)

    # Add transition relation
    solver.add(encoding.transition)

    # Add bounds constraints for pre-state
    for sv in spec.state_variables:
        if sv.bounds:
            low, high = sv.bounds
            pre_var = encoding.pre_state[sv.name]
            if low is not None:
                solver.add(pre_var >= low)
            if high is not None:
                solver.add(pre_var <= high)

    # Add bounds constraints for inputs
    for iv in spec.input_variables:
        if iv.bounds:
            low, high = iv.bounds
            input_var = encoding.inputs[iv.name]
            if low is not None:
                solver.add(input_var >= low)
            if high is not None:
                solver.add(input_var <= high)

    # Get property formula
    property_holds = prop.encode(
        encoding.pre_state,
        encoding.post_state,
        encoding.inputs,
        encoding.output
    )

    # Check negation of property
    solver.add(z3.Not(property_holds))

    result = solver.check()

    if result == z3.unsat:
        # Property holds for all inputs
        return VerificationResult(status=VerificationStatus.VERIFIED)

    elif result == z3.sat:
        # Found counterexample
        model = solver.model()
        counterexample = _extract_counterexample(model, encoding, spec)

        return VerificationResult(
            status=VerificationStatus.COUNTEREXAMPLE,
            property_violated=PropertyViolation(
                property_name=prop.name,
                property_description=prop.description,
                property_formula=prop.formula
            ),
            counterexample=counterexample
        )

    else:
        # Unknown (timeout or other)
        return VerificationResult(
            status=VerificationStatus.UNKNOWN,
            error_message="Solver returned unknown (possible timeout)"
        )


def _extract_counterexample(
    model: z3.ModelRef,
    encoding: EncodingResult,
    spec: ProblemSpec
) -> Counterexample:
    """
    Extract concrete counterexample from Z3 model.
    """
    pre_state = {}
    post_state = {}
    inputs = {}

    # Extract pre-state values
    for name, var in encoding.pre_state.items():
        pre_state[name] = _extract_value(model, var, _get_var_type(name, spec, "state"))

    # Extract post-state values
    for name, var in encoding.post_state.items():
        post_state[name] = _extract_value(model, var, _get_var_type(name, spec, "state"))

    # Extract input values
    for name, var in encoding.inputs.items():
        inputs[name] = _extract_value(model, var, _get_var_type(name, spec, "input"))

    # Extract output value
    output = _extract_value(model, encoding.output, spec.output_type)

    return Counterexample(
        pre_state=pre_state,
        inputs=inputs,
        post_state=post_state,
        output=output
    )


def _extract_value(model: z3.ModelRef, var: z3.ExprRef, var_type: str) -> Any:
    """
    Extract Python value from Z3 model.
    """
    val = model.eval(var, model_completion=True)

    if val is None:
        return None

    # Handle different Z3 types
    if z3.is_bool(var):
        return bool(val)

    elif z3.is_int(var):
        if z3.is_int_value(val):
            return val.as_long()
        return 0  # Default for unconstrained

    elif z3.is_real(var):
        if z3.is_rational_value(val):
            return float(val.as_fraction())
        elif z3.is_int_value(val):
            return float(val.as_long())
        return 0.0  # Default for unconstrained

    # Try to convert based on declared type
    if var_type == "bool":
        return bool(val)
    elif var_type == "int":
        try:
            return val.as_long()
        except Exception:
            return 0
    elif var_type == "real":
        try:
            return float(val.as_fraction())
        except Exception:
            try:
                return float(val.as_long())
            except Exception:
                return 0.0

    # Fallback
    return str(val)


def _get_var_type(name: str, spec: ProblemSpec, kind: str) -> str:
    """Get variable type from spec."""
    if kind == "state":
        for sv in spec.state_variables:
            if sv.name == name:
                return sv.var_type
    elif kind == "input":
        for iv in spec.input_variables:
            if iv.name == name:
                return iv.var_type
    return "real"  # Default


def verify_with_trace(
    code: str,
    spec: ProblemSpec,
    timeout_ms: int = 30000
) -> tuple[VerificationResult, list[str]]:
    """
    Verify with solver trace for debugging.

    Returns result and list of trace messages.
    """
    trace = []

    trace.append(f"Verifying code against {len(spec.properties)} properties")

    result = verify(code, spec, timeout_ms)

    trace.append(f"Result: {result.status.value}")

    if result.counterexample:
        trace.append(f"Counterexample: {result.counterexample.to_dict()}")

    if result.property_violated:
        trace.append(f"Property violated: {result.property_violated.property_name}")

    return result, trace
