"""
RL-004: Fixed Window Rate Limiter

A simple rate limiter using fixed time windows.
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

PROBLEM_ID = "RL-004"
NAME = "Fixed Window Rate Limiter"
CATEGORY = "rate_limiting"
DIFFICULTY = "easy"

DESCRIPTION = """
Implement a Fixed Window Rate Limiter.

The fixed window algorithm resets the counter at the start of each window.

allow(timestamp):
1. Calculate window: window = floor(timestamp / window_size)
2. If window > current_window:
   - current_window = window
   - count = 0
3. If count < max_requests:
   - count += 1
   - return True
4. return False

Constants: window_size = 60, max_requests = 10
"""

METHOD_SIGNATURE = "def allow(self, timestamp: int) -> bool"

STATE_VARIABLES = [
    StateVariable(
        name="count",
        var_type="int",
        description="Requests in current window",
        bounds=(0, 10),
        initial_value=0
    ),
    StateVariable(
        name="current_window",
        var_type="int",
        description="Current window number",
        bounds=(0, 1000),
        initial_value=0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="timestamp",
        var_type="int",
        description="Current request timestamp",
        bounds=(0, 10000)
    ),
]

OUTPUT_TYPE = "bool"


# =============================================================================
# PROPERTIES
# =============================================================================

def _prop_count_non_negative(pre, post, inputs, output):
    """Count must never go negative."""
    return post["count"] >= 0


def _prop_count_bounded(pre, post, inputs, output):
    """Count must not exceed max_requests."""
    return post["count"] <= 10


PROPERTIES = [
    Property(
        name="count_non_negative",
        description="Count must never go negative",
        formula="□(count >= 0)",
        encode=_prop_count_non_negative
    ),
    Property(
        name="count_bounded",
        description="Count must not exceed max_requests",
        formula="□(count <= max_requests)",
        encode=_prop_count_bounded
    ),
]


# =============================================================================
# EXAMPLES
# =============================================================================

EXAMPLES = [
    Example(
        name="allow_first",
        description="Allow first request",
        pre_state={"count": 0, "current_window": 0},
        inputs={"timestamp": 0},
        expected_output=True,
        expected_post_state={"count": 1, "current_window": 0}
    ),
    Example(
        name="deny_at_limit",
        description="Deny when at limit",
        pre_state={"count": 10, "current_window": 0},
        inputs={"timestamp": 30},
        expected_output=False,
        expected_post_state={"count": 10, "current_window": 0}
    ),
]


# =============================================================================
# REFERENCE IMPLEMENTATIONS
# =============================================================================

BUGGY_CODE = """
def allow(self, timestamp: int) -> bool:
    window = timestamp // 60
    if window > self.current_window:
        self.current_window = window
        self.count = 0
    # BUG: Uses > instead of <, always allows when at limit
    if self.count > 10:
        return False
    self.count = self.count + 1
    return True
"""

CORRECT_CODE = """
def allow(self, timestamp: int) -> bool:
    window = timestamp // 60
    if window > self.current_window:
        self.current_window = window
        self.count = 0
    if self.count < 10:
        self.count = self.count + 1
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
        tags=["rate-limiting", "fixed-window"]
    )
