"""
RL-008: Quota Limiter

A rate limiter that enforces daily/hourly quotas.
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

PROBLEM_ID = "RL-008"
NAME = "Quota Limiter"
CATEGORY = "rate_limiting"
DIFFICULTY = "medium"

DESCRIPTION = """
Implement a Quota Limiter.

The quota limiter enforces a maximum number of requests per period.

use_quota(period):
1. If period > current_period:
   - current_period = period
   - used = 0
2. If used < quota:
   - used += 1
   - return True
3. return False

Constants: quota = 1000
"""

METHOD_SIGNATURE = "def use_quota(self, period: int) -> bool"

STATE_VARIABLES = [
    StateVariable(
        name="used",
        var_type="int",
        description="Quota used in current period",
        bounds=(0, 1000),
        initial_value=0
    ),
    StateVariable(
        name="current_period",
        var_type="int",
        description="Current period number",
        bounds=(0, 1000),
        initial_value=0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="period",
        var_type="int",
        description="Period number for this request",
        bounds=(0, 1000)
    ),
]

OUTPUT_TYPE = "bool"


# =============================================================================
# PROPERTIES
# =============================================================================

def _prop_used_non_negative(pre, post, inputs, output):
    """Used quota must never go negative."""
    return post["used"] >= 0


def _prop_used_bounded(pre, post, inputs, output):
    """Used quota must not exceed quota limit."""
    return post["used"] <= 1000


PROPERTIES = [
    Property(
        name="used_non_negative",
        description="Used quota must never go negative",
        formula="□(used >= 0)",
        encode=_prop_used_non_negative
    ),
    Property(
        name="used_bounded",
        description="Used quota must not exceed quota",
        formula="□(used <= quota)",
        encode=_prop_used_bounded
    ),
]


# =============================================================================
# EXAMPLES
# =============================================================================

EXAMPLES = [
    Example(
        name="use_quota",
        description="Use quota in current period",
        pre_state={"used": 500, "current_period": 1},
        inputs={"period": 1},
        expected_output=True,
        expected_post_state={"used": 501, "current_period": 1}
    ),
    Example(
        name="new_period",
        description="Reset quota in new period",
        pre_state={"used": 1000, "current_period": 1},
        inputs={"period": 2},
        expected_output=True,
        expected_post_state={"used": 1, "current_period": 2}
    ),
]


# =============================================================================
# REFERENCE IMPLEMENTATIONS
# =============================================================================

BUGGY_CODE = """
def use_quota(self, period: int) -> bool:
    if period > self.current_period:
        self.current_period = period
        self.used = 0
    # BUG: Uses <= instead of <, allows one over quota
    if self.used <= 1000:
        self.used = self.used + 1
        return True
    return False
"""

CORRECT_CODE = """
def use_quota(self, period: int) -> bool:
    if period > self.current_period:
        self.current_period = period
        self.used = 0
    if self.used < 1000:
        self.used = self.used + 1
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
        tags=["rate-limiting", "quota"]
    )
