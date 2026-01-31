"""
CB-007: Fallback Handler

Returns fallback values on failure.
"""

from rotalabs_verity.core import (
    Example,
    InputVariable,
    ProblemSpec,
    Property,
    StateVariable,
)

# =============================================================================
# PROBLEM SPECIFICATION
# =============================================================================

PROBLEM_ID = "CB-007"
NAME = "Fallback Handler"
CATEGORY = "circuit_breaker"
DIFFICULTY = "easy"

DESCRIPTION = """
Implement a Fallback Handler.

Track whether the primary service is available and return appropriate values.

record_result(success):
1. If success:
   - consecutive_failures = 0
   - using_fallback = 0
2. If not success:
   - consecutive_failures += 1
   - If consecutive_failures >= fallback_threshold:
     - using_fallback = 1
3. Return using_fallback

Constants: fallback_threshold = 3
"""

METHOD_SIGNATURE = "def record_result(self, success: bool) -> int"

STATE_VARIABLES = [
    StateVariable(
        name="consecutive_failures",
        var_type="int",
        description="Number of consecutive failures",
        bounds=(0, 10),
        initial_value=0
    ),
    StateVariable(
        name="using_fallback",
        var_type="int",
        description="Whether using fallback (0 or 1)",
        bounds=(0, 1),
        initial_value=0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="success",
        var_type="bool",
        description="Whether the primary call succeeded"
    ),
]

OUTPUT_TYPE = "int"


# =============================================================================
# PROPERTIES
# =============================================================================

def _prop_failures_non_negative(pre, post, inputs, output):
    """Failure count must be non-negative."""
    return post["consecutive_failures"] >= 0


def _prop_fallback_valid(pre, post, inputs, output):
    """using_fallback must be 0 or 1."""
    import z3
    return z3.And(post["using_fallback"] >= 0, post["using_fallback"] <= 1)


PROPERTIES = [
    Property(
        name="failures_non_negative",
        description="Failure count must be non-negative",
        formula="□(consecutive_failures >= 0)",
        encode=_prop_failures_non_negative
    ),
    Property(
        name="fallback_valid",
        description="using_fallback must be 0 or 1",
        formula="□(0 <= using_fallback <= 1)",
        encode=_prop_fallback_valid
    ),
]


# =============================================================================
# EXAMPLES
# =============================================================================

EXAMPLES = [
    Example(
        name="success_resets",
        description="Success resets to primary",
        pre_state={"consecutive_failures": 2, "using_fallback": 0},
        inputs={"success": True},
        expected_output=0,
        expected_post_state={"consecutive_failures": 0, "using_fallback": 0}
    ),
    Example(
        name="third_failure",
        description="Third failure triggers fallback",
        pre_state={"consecutive_failures": 2, "using_fallback": 0},
        inputs={"success": False},
        expected_output=1,
        expected_post_state={"consecutive_failures": 3, "using_fallback": 1}
    ),
]


# =============================================================================
# REFERENCE IMPLEMENTATIONS
# =============================================================================

BUGGY_CODE = """
def record_result(self, success: bool) -> int:
    if success:
        # BUG: Decrements without checking bounds
        self.consecutive_failures = self.consecutive_failures - 1
        self.using_fallback = 0
    else:
        self.consecutive_failures = self.consecutive_failures + 1
        if self.consecutive_failures >= 3:
            self.using_fallback = 1
    return self.using_fallback
"""

CORRECT_CODE = """
def record_result(self, success: bool) -> int:
    if success:
        self.consecutive_failures = 0
        self.using_fallback = 0
    else:
        self.consecutive_failures = self.consecutive_failures + 1
        if self.consecutive_failures >= 3:
            self.using_fallback = 1
    return self.using_fallback
"""


# =============================================================================
# BUILD SPEC
# =============================================================================

def get_spec() -> ProblemSpec:
    """Get the complete problem specification."""
    return ProblemSpec(
        problem_id=PROBLEM_ID,
        name=NAME,
        category=CATEGORY,
        difficulty=DIFFICULTY,
        description=DESCRIPTION,
        method_signature=METHOD_SIGNATURE,
        state_variables=STATE_VARIABLES,
        input_variables=INPUT_VARIABLES,
        output_type=OUTPUT_TYPE,
        properties=PROPERTIES,
        examples=EXAMPLES,
        buggy_code=BUGGY_CODE,
        correct_code=CORRECT_CODE,
        tags=["circuit-breaker", "fallback"]
    )
