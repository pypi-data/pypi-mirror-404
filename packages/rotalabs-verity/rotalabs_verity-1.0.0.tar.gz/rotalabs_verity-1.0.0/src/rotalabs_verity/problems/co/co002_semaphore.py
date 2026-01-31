"""
CO-002: Semaphore

A counting semaphore for resource coordination.
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

PROBLEM_ID = "CO-002"
NAME = "Semaphore"
CATEGORY = "coordination"
DIFFICULTY = "easy"

DESCRIPTION = """
Implement a Counting Semaphore.

A semaphore controls access to a limited number of resources. It maintains a count
of available permits.

acquire():
- If permits > 0: decrement permits, return True
- Otherwise: return False (would block in real impl)

release():
- Increment permits (up to max_permits)
- Return new permit count

Constants: self.max_permits = 5
"""

METHOD_SIGNATURE = "def acquire(self) -> bool"

STATE_VARIABLES = [
    StateVariable(
        name="permits",
        var_type="int",
        description="Number of available permits",
        bounds=(0, 5),
        initial_value=5
    ),
]

INPUT_VARIABLES = []

OUTPUT_TYPE = "bool"


# =============================================================================
# PROPERTIES
# =============================================================================

def _prop_permits_non_negative(pre, post, inputs, output):
    """Permits must never go negative."""
    return post["permits"] >= 0


def _prop_permits_bounded(pre, post, inputs, output):
    """Permits must not exceed max."""
    return post["permits"] <= 5


PROPERTIES = [
    Property(
        name="permits_non_negative",
        description="Permit count must never go negative",
        formula="□(permits >= 0)",
        encode=_prop_permits_non_negative
    ),
    Property(
        name="permits_bounded",
        description="Permit count must not exceed max_permits",
        formula="□(permits <= max_permits)",
        encode=_prop_permits_bounded
    ),
]


# =============================================================================
# EXAMPLES
# =============================================================================

EXAMPLES = [
    Example(
        name="acquire_success",
        description="Acquire when permits available",
        pre_state={"permits": 3},
        inputs={},
        expected_output=True,
        expected_post_state={"permits": 2}
    ),
    Example(
        name="acquire_fail",
        description="Acquire fails when no permits",
        pre_state={"permits": 0},
        inputs={},
        expected_output=False,
        expected_post_state={"permits": 0}
    ),
]


# =============================================================================
# REFERENCE IMPLEMENTATIONS
# =============================================================================

BUGGY_CODE = """
def acquire(self) -> bool:
    # BUG: Always decrements without checking
    self.permits = self.permits - 1
    return True
"""

CORRECT_CODE = """
def acquire(self) -> bool:
    if self.permits > 0:
        self.permits = self.permits - 1
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
        tags=["coordination", "semaphore", "concurrency"]
    )
