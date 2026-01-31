"""
RL-005: Concurrent Request Limiter

Limits the number of simultaneous in-flight requests.
"""

from rotalabs_verity.core import (
    Example,
    ProblemSpec,
    Property,
    StateVariable,
)

# =============================================================================
# PROBLEM SPECIFICATION
# =============================================================================

PROBLEM_ID = "RL-005"
NAME = "Concurrent Request Limiter"
CATEGORY = "rate_limiting"
DIFFICULTY = "medium"

DESCRIPTION = """
Implement a Concurrent Request Limiter.

This limiter tracks in-flight requests and prevents too many simultaneous requests.

acquire():
1. If in_flight < max_concurrent:
   - in_flight += 1
   - return True
2. return False

release():
1. If in_flight > 0:
   - in_flight -= 1
   - return True
2. return False

Constants: max_concurrent = 10
"""

METHOD_SIGNATURE = "def acquire(self) -> bool"

STATE_VARIABLES = [
    StateVariable(
        name="in_flight",
        var_type="int",
        description="Number of in-flight requests",
        bounds=(0, 10),
        initial_value=0
    ),
]

INPUT_VARIABLES = []

OUTPUT_TYPE = "bool"


# =============================================================================
# PROPERTIES
# =============================================================================

def _prop_in_flight_non_negative(pre, post, inputs, output):
    """In-flight count must never go negative."""
    return post["in_flight"] >= 0


def _prop_in_flight_bounded(pre, post, inputs, output):
    """In-flight count must not exceed max_concurrent."""
    return post["in_flight"] <= 10


PROPERTIES = [
    Property(
        name="in_flight_non_negative",
        description="In-flight count must never go negative",
        formula="□(in_flight >= 0)",
        encode=_prop_in_flight_non_negative
    ),
    Property(
        name="in_flight_bounded",
        description="In-flight count must not exceed max_concurrent",
        formula="□(in_flight <= max_concurrent)",
        encode=_prop_in_flight_bounded
    ),
]


# =============================================================================
# EXAMPLES
# =============================================================================

EXAMPLES = [
    Example(
        name="acquire_success",
        description="Acquire when under limit",
        pre_state={"in_flight": 5},
        inputs={},
        expected_output=True,
        expected_post_state={"in_flight": 6}
    ),
    Example(
        name="acquire_fail",
        description="Deny when at limit",
        pre_state={"in_flight": 10},
        inputs={},
        expected_output=False,
        expected_post_state={"in_flight": 10}
    ),
]


# =============================================================================
# REFERENCE IMPLEMENTATIONS
# =============================================================================

BUGGY_CODE = """
def acquire(self) -> bool:
    # BUG: Uses <= instead of <, allows one over limit
    if self.in_flight <= 10:
        self.in_flight = self.in_flight + 1
        return True
    return False
"""

CORRECT_CODE = """
def acquire(self) -> bool:
    if self.in_flight < 10:
        self.in_flight = self.in_flight + 1
        return True
    return False
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
        tags=["rate-limiting", "concurrency"]
    )
