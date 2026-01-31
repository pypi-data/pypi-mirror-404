"""
Z3 encoder - main entry point.

Encodes Python methods as Z3 transition relations.
"""

from dataclasses import dataclass

import z3

from rotalabs_verity.core import ProblemSpec
from rotalabs_verity.encoder.parser import parse_method
from rotalabs_verity.encoder.symbolic import SymbolicExecutor


@dataclass
class EncodingResult:
    """Result of encoding a method to Z3."""
    pre_state: dict[str, z3.ExprRef]      # Pre-state variables
    post_state: dict[str, z3.ExprRef]     # Post-state variables
    inputs: dict[str, z3.ExprRef]         # Input parameters
    output: z3.ExprRef                     # Return value
    transition: z3.BoolRef                 # Transition relation (constraints)


def encode_method(code: str, spec: ProblemSpec) -> EncodingResult:
    """
    Encode Python method as Z3 transition relation.

    This is the main entry point for the encoder.

    Args:
        code: Python source code for the method
        spec: Problem specification

    Returns:
        EncodingResult with Z3 variables and transition relation

    Raises:
        ParseError: If code cannot be parsed
        EncodingError: If code cannot be encoded
    """
    # Step 1: Parse the method
    method_info = parse_method(code)

    # Step 2: Create Z3 variables from spec
    pre_state, post_state, inputs, output = spec.create_z3_variables()

    # Step 3: Symbolically execute to get transition relation
    executor = SymbolicExecutor(spec)
    computed_post, computed_output, transition = executor.execute(
        method_info.body,
        pre_state,
        inputs
    )

    # Step 4: Build constraints linking computed values to post variables
    constraints = [transition]

    # Link computed post-state to post variables
    for name in post_state:
        if name in computed_post:
            constraints.append(post_state[name] == computed_post[name])

    # Link computed output to output variable
    constraints.append(output == computed_output)

    # Combine all constraints
    full_transition = z3.And(*constraints) if len(constraints) > 1 else constraints[0]

    return EncodingResult(
        pre_state=pre_state,
        post_state=post_state,
        inputs=inputs,
        output=output,
        transition=full_transition
    )


def encode_with_bounds(code: str, spec: ProblemSpec) -> EncodingResult:
    """
    Encode method with variable bounds from spec.

    Same as encode_method but adds bounds constraints.

    Args:
        code: Python source code
        spec: Problem specification

    Returns:
        EncodingResult with bounds included in transition
    """
    result = encode_method(code, spec)

    bounds_constraints = []

    # Add bounds for state variables
    for sv in spec.state_variables:
        if sv.bounds:
            low, high = sv.bounds
            pre_var = result.pre_state[sv.name]
            result.post_state[sv.name]

            if low is not None:
                bounds_constraints.append(pre_var >= low)
            if high is not None:
                bounds_constraints.append(pre_var <= high)

    # Add bounds for input variables
    for iv in spec.input_variables:
        if iv.bounds:
            low, high = iv.bounds
            input_var = result.inputs[iv.name]

            if low is not None:
                bounds_constraints.append(input_var >= low)
            if high is not None:
                bounds_constraints.append(input_var <= high)

    if bounds_constraints:
        result.transition = z3.And(result.transition, *bounds_constraints)

    return result
