"""
RL-007: Burst Limiter

Allow bursts up to a limit.
"""

from rotalabs_verity.core import (
    Example,
    InputVariable,
    ProblemSpec,
    Property,
    StateVariable,
)

PROBLEM_ID = "RL-007"
NAME = "Burst Limiter"
CATEGORY = "rate_limiting"
DIFFICULTY = "medium"

DESCRIPTION = """
Implement Burst Limiter.

allow_burst(burst_size):
1. If current_burst + burst_size <= max_burst:
   - current_burst = current_burst + burst_size
   - total_allowed = total_allowed + burst_size
   - return True
2. return False (would exceed burst limit)

Constants: max_burst = 10
"""

METHOD_SIGNATURE = "def allow_burst(self, burst_size: int) -> bool"

STATE_VARIABLES = [
    StateVariable(
        name="current_burst",
        var_type="int",
        description="Current burst usage",
        bounds=(0, 10),
        initial_value=0
    ),
    StateVariable(
        name="total_allowed",
        var_type="int",
        description="Total requests allowed",
        bounds=(0, 1000),
        initial_value=0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="burst_size",
        var_type="int",
        description="Size of requested burst",
        bounds=(1, 10)
    ),
]

OUTPUT_TYPE = "bool"


def _prop_burst_bounded(pre, post, inputs, output):
    """current_burst must not exceed max_burst."""
    return post["current_burst"] <= 10


def _prop_total_non_negative(pre, post, inputs, output):
    """total_allowed must be non-negative."""
    return post["total_allowed"] >= 0


PROPERTIES = [
    Property(
        name="burst_bounded",
        description="current_burst must not exceed max_burst",
        formula="□(current_burst <= max_burst)",
        encode=_prop_burst_bounded
    ),
    Property(
        name="total_non_negative",
        description="total_allowed must be non-negative",
        formula="□(total_allowed >= 0)",
        encode=_prop_total_non_negative
    ),
]


EXAMPLES = [
    Example(
        name="allow_burst",
        description="Allow burst within limit",
        pre_state={"current_burst": 3, "total_allowed": 10},
        inputs={"burst_size": 5},
        expected_output=True,
        expected_post_state={"current_burst": 8, "total_allowed": 15}
    ),
]


BUGGY_CODE = """
def allow_burst(self, burst_size: int) -> bool:
    # BUG: No check on burst limit
    self.current_burst = self.current_burst + burst_size
    self.total_allowed = self.total_allowed + burst_size
    return True
"""

CORRECT_CODE = """
def allow_burst(self, burst_size: int) -> bool:
    if self.current_burst + burst_size <= 10:
        self.current_burst = self.current_burst + burst_size
        self.total_allowed = self.total_allowed + burst_size
        return True
    return False
"""


def get_spec() -> ProblemSpec:
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
        tags=["rate_limiting", "burst"]
    )
