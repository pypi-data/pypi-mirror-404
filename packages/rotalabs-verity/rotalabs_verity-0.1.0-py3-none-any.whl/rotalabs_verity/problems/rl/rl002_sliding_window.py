"""
RL-002: Sliding Window Rate Limiter

A rate limiter using sliding window algorithm.
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

PROBLEM_ID = "RL-002"
NAME = "Sliding Window Rate Limiter"
CATEGORY = "rate_limiting"
DIFFICULTY = "medium"

DESCRIPTION = """
Implement a Sliding Window Rate Limiter.

The sliding window algorithm tracks requests in the current and previous windows,
using a weighted average to smoothly limit requests.

record_request(timestamp):
1. Calculate current window: window = floor(timestamp / window_size)
2. If window > current_window:
   - prev_count = current_count
   - current_count = 0
   - current_window = window
3. Calculate weight: weight = (timestamp % window_size) / window_size
4. Calculate effective: effective = prev_count * (1 - weight) + current_count
5. If effective + 1 <= max_requests:
   - current_count += 1
   - return True
6. return False

Constants: window_size = 10, max_requests = 5
"""

METHOD_SIGNATURE = "def record_request(self, timestamp: int) -> bool"

STATE_VARIABLES = [
    StateVariable(
        name="current_count",
        var_type="int",
        description="Requests in current window",
        bounds=(0, 5),
        initial_value=0
    ),
    StateVariable(
        name="prev_count",
        var_type="int",
        description="Requests in previous window",
        bounds=(0, 5),
        initial_value=0
    ),
    StateVariable(
        name="current_window",
        var_type="int",
        description="Current window number",
        bounds=(0, 100),
        initial_value=0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="timestamp",
        var_type="int",
        description="Current request timestamp",
        bounds=(0, 1000)
    ),
]

OUTPUT_TYPE = "bool"


# =============================================================================
# PROPERTIES
# =============================================================================

def _prop_count_non_negative(pre, post, inputs, output):
    """Request counts must never go negative."""
    import z3
    return z3.And(post["current_count"] >= 0, post["prev_count"] >= 0)


def _prop_count_bounded(pre, post, inputs, output):
    """Request count must not exceed max_requests."""
    return post["current_count"] <= 5


PROPERTIES = [
    Property(
        name="count_non_negative",
        description="Request counts must never go negative",
        formula="□(current_count >= 0 ∧ prev_count >= 0)",
        encode=_prop_count_non_negative
    ),
    Property(
        name="count_bounded",
        description="Current count must not exceed max_requests",
        formula="□(current_count <= max_requests)",
        encode=_prop_count_bounded
    ),
]


# =============================================================================
# EXAMPLES
# =============================================================================

EXAMPLES = [
    Example(
        name="first_request",
        description="First request in empty window",
        pre_state={"current_count": 0, "prev_count": 0, "current_window": 0},
        inputs={"timestamp": 0},
        expected_output=True,
        expected_post_state={"current_count": 1, "prev_count": 0, "current_window": 0}
    ),
    Example(
        name="window_change",
        description="Request in new window",
        pre_state={"current_count": 3, "prev_count": 0, "current_window": 0},
        inputs={"timestamp": 10},
        expected_output=True,
        expected_post_state={"current_count": 1, "prev_count": 3, "current_window": 1}
    ),
]


# =============================================================================
# REFERENCE IMPLEMENTATIONS
# =============================================================================

BUGGY_CODE = """
def record_request(self, timestamp: int) -> bool:
    window = timestamp // 10
    if window > self.current_window:
        self.prev_count = self.current_count
        self.current_count = 0
        self.current_window = window
    # BUG: Always increments without checking limit
    self.current_count = self.current_count + 1
    return True
"""

CORRECT_CODE = """
def record_request(self, timestamp: int) -> bool:
    window = timestamp // 10
    if window > self.current_window:
        self.prev_count = self.current_count
        self.current_count = 0
        self.current_window = window
    if self.current_count + 1 <= 5:
        self.current_count = self.current_count + 1
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
        tags=["rate-limiting", "sliding-window"]
    )
