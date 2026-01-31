"""
CB-004: Timeout Handler

Enforces operation timeouts.
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

PROBLEM_ID = "CB-004"
NAME = "Timeout Handler"
CATEGORY = "circuit_breaker"
DIFFICULTY = "easy"

DESCRIPTION = """
Implement a Timeout Handler.

Track operation start time and check for timeout.

start_operation(timestamp):
1. If not in_progress:
   - start_time = timestamp
   - in_progress = 1
   - return True
2. return False

check_timeout(timestamp):
1. If in_progress:
   - If timestamp - start_time > timeout:
     - in_progress = 0
     - return True (timed out)
2. return False

Constants: timeout = 30
"""

METHOD_SIGNATURE = "def start_operation(self, timestamp: int) -> bool"

STATE_VARIABLES = [
    StateVariable(
        name="in_progress",
        var_type="int",
        description="Whether an operation is in progress (0 or 1)",
        bounds=(0, 1),
        initial_value=0
    ),
    StateVariable(
        name="start_time",
        var_type="int",
        description="Start time of current operation",
        bounds=(0, 1000),
        initial_value=0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="timestamp",
        var_type="int",
        description="Current timestamp",
        bounds=(0, 1000)
    ),
]

OUTPUT_TYPE = "bool"


# =============================================================================
# PROPERTIES
# =============================================================================

def _prop_in_progress_valid(pre, post, inputs, output):
    """in_progress must be 0 or 1."""
    import z3
    return z3.And(post["in_progress"] >= 0, post["in_progress"] <= 1)


def _prop_start_time_non_negative(pre, post, inputs, output):
    """Start time must be non-negative."""
    return post["start_time"] >= 0


PROPERTIES = [
    Property(
        name="in_progress_valid",
        description="in_progress must be 0 or 1",
        formula="□(0 <= in_progress <= 1)",
        encode=_prop_in_progress_valid
    ),
    Property(
        name="start_time_non_negative",
        description="Start time must be non-negative",
        formula="□(start_time >= 0)",
        encode=_prop_start_time_non_negative
    ),
]


# =============================================================================
# EXAMPLES
# =============================================================================

EXAMPLES = [
    Example(
        name="start_success",
        description="Start operation when idle",
        pre_state={"in_progress": 0, "start_time": 0},
        inputs={"timestamp": 10},
        expected_output=True,
        expected_post_state={"in_progress": 1, "start_time": 10}
    ),
    Example(
        name="start_fail",
        description="Cannot start when already in progress",
        pre_state={"in_progress": 1, "start_time": 5},
        inputs={"timestamp": 10},
        expected_output=False,
        expected_post_state={"in_progress": 1, "start_time": 5}
    ),
]


# =============================================================================
# REFERENCE IMPLEMENTATIONS
# =============================================================================

BUGGY_CODE = """
def start_operation(self, timestamp: int) -> bool:
    # BUG: Sets in_progress to 2 instead of 1
    self.start_time = timestamp
    self.in_progress = 2
    return True
"""

CORRECT_CODE = """
def start_operation(self, timestamp: int) -> bool:
    if self.in_progress == 0:
        self.start_time = timestamp
        self.in_progress = 1
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
        tags=["circuit-breaker", "timeout"]
    )
