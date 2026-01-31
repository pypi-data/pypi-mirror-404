"""
Problem specification types.

A Problem defines:
- Natural language description
- State variables
- Properties to verify
- Method signature
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Literal

import z3


@dataclass(frozen=True)
class StateVariable:
    """A state variable in the system."""
    name: str                                    # e.g., "tokens"
    var_type: Literal["bool", "int", "real"]    # Z3 type
    description: str                             # For prompts
    bounds: tuple[float | None, float | None] | None = None  # Optional (min, max)
    initial_value: Any = None                    # Optional default


@dataclass(frozen=True)
class InputVariable:
    """An input parameter to the method."""
    name: str
    var_type: Literal["bool", "int", "real"]
    description: str
    bounds: tuple[float | None, float | None] | None = None


@dataclass
class Property:
    """
    A property that must hold.

    The encode() method returns a Z3 formula that is TRUE when
    the property HOLDS. The verifier will check NOT(encode(...))
    to find violations.
    """
    name: str
    description: str
    formula: str  # Human-readable LTL (for prompts)

    # The encode function takes Z3 variables and returns Z3 formula
    # Signature: (pre_state, post_state, inputs, output) -> z3.BoolRef
    encode: Callable[
        [dict[str, z3.ExprRef], dict[str, z3.ExprRef],
         dict[str, z3.ExprRef], z3.ExprRef],
        z3.BoolRef
    ] = field(repr=False)


@dataclass
class Example:
    """Input/output example for few-shot prompting."""
    name: str
    description: str
    pre_state: dict[str, Any]
    inputs: dict[str, Any]
    expected_output: Any
    expected_post_state: dict[str, Any]


@dataclass
class ProblemSpec:
    """
    Complete specification for a synthesis problem.

    This is the PRIMARY interface for defining problems.
    """
    # Identification
    problem_id: str              # e.g., "RL-001"
    name: str                    # e.g., "Token Bucket Rate Limiter"
    category: str                # e.g., "rate_limiting"
    difficulty: Literal["easy", "medium", "hard"]

    # Natural language (for LLM)
    description: str             # Full description of what to implement
    method_signature: str        # e.g., "def allow(self, timestamp: float) -> bool"

    # Formal specification
    state_variables: list[StateVariable]
    input_variables: list[InputVariable]
    output_type: Literal["bool", "int", "real", "none"]
    properties: list[Property]

    # Examples (for few-shot prompting)
    examples: list[Example] = field(default_factory=list)

    # Reference implementations (for testing framework)
    buggy_code: str = ""
    correct_code: str = ""

    # Metadata
    tags: list[str] = field(default_factory=list)

    def get_property(self, name: str) -> Property | None:
        """Get property by name."""
        for p in self.properties:
            if p.name == name:
                return p
        return None

    def create_z3_variables(self) -> tuple[
        dict[str, z3.ExprRef],  # pre_state
        dict[str, z3.ExprRef],  # post_state
        dict[str, z3.ExprRef],  # inputs
        z3.ExprRef              # output
    ]:
        """Create Z3 variables for verification."""
        def make_var(name: str, var_type: str) -> z3.ExprRef:
            if var_type == "bool":
                return z3.Bool(name)
            elif var_type == "int":
                return z3.Int(name)
            else:  # real
                return z3.Real(name)

        pre_state = {
            sv.name: make_var(f"{sv.name}_pre", sv.var_type)
            for sv in self.state_variables
        }
        post_state = {
            sv.name: make_var(f"{sv.name}_post", sv.var_type)
            for sv in self.state_variables
        }
        inputs = {
            iv.name: make_var(iv.name, iv.var_type)
            for iv in self.input_variables
        }
        output = make_var("output", self.output_type if self.output_type != "none" else "bool")

        return pre_state, post_state, inputs, output
