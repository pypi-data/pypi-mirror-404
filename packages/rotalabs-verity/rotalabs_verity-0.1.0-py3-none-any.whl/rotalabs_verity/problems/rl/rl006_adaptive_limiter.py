"""
RL-006: Adaptive Rate Limiter

A rate limiter that adjusts its limit based on success/failure feedback.
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

PROBLEM_ID = "RL-006"
NAME = "Adaptive Rate Limiter"
CATEGORY = "rate_limiting"
DIFFICULTY = "hard"

DESCRIPTION = """
Implement an Adaptive Rate Limiter.

The adaptive limiter adjusts its rate limit based on success/failure feedback.

record_outcome(success):
1. If success:
   - If current_limit < max_limit:
     - current_limit += 1
   - consecutive_failures = 0
2. If not success:
   - consecutive_failures += 1
   - If consecutive_failures >= failure_threshold:
     - current_limit = max(min_limit, current_limit // 2)
     - consecutive_failures = 0
3. Return current_limit

Constants: min_limit = 1, max_limit = 100, failure_threshold = 3
"""

METHOD_SIGNATURE = "def record_outcome(self, success: bool) -> int"

STATE_VARIABLES = [
    StateVariable(
        name="current_limit",
        var_type="int",
        description="Current rate limit",
        bounds=(1, 100),
        initial_value=50
    ),
    StateVariable(
        name="consecutive_failures",
        var_type="int",
        description="Consecutive failure count",
        bounds=(0, 10),
        initial_value=0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="success",
        var_type="bool",
        description="Whether the request succeeded"
    ),
]

OUTPUT_TYPE = "int"


# =============================================================================
# PROPERTIES
# =============================================================================

def _prop_limit_in_bounds(pre, post, inputs, output):
    """Limit must stay within min and max bounds."""
    import z3
    return z3.And(post["current_limit"] >= 1, post["current_limit"] <= 100)


def _prop_failures_non_negative(pre, post, inputs, output):
    """Failure count must be non-negative."""
    return post["consecutive_failures"] >= 0


PROPERTIES = [
    Property(
        name="limit_in_bounds",
        description="Limit must stay within [min_limit, max_limit]",
        formula="□(min_limit <= current_limit <= max_limit)",
        encode=_prop_limit_in_bounds
    ),
    Property(
        name="failures_non_negative",
        description="Consecutive failures must be non-negative",
        formula="□(consecutive_failures >= 0)",
        encode=_prop_failures_non_negative
    ),
]


# =============================================================================
# EXAMPLES
# =============================================================================

EXAMPLES = [
    Example(
        name="success_increases",
        description="Success increases limit",
        pre_state={"current_limit": 50, "consecutive_failures": 0},
        inputs={"success": True},
        expected_output=51,
        expected_post_state={"current_limit": 51, "consecutive_failures": 0}
    ),
    Example(
        name="failure_threshold",
        description="Third failure halves limit",
        pre_state={"current_limit": 50, "consecutive_failures": 2},
        inputs={"success": False},
        expected_output=25,
        expected_post_state={"current_limit": 25, "consecutive_failures": 0}
    ),
]


# =============================================================================
# REFERENCE IMPLEMENTATIONS
# =============================================================================

BUGGY_CODE = """
def record_outcome(self, success: bool) -> int:
    if success:
        # BUG: No upper bound check
        self.current_limit = self.current_limit + 1
        self.consecutive_failures = 0
    else:
        self.consecutive_failures = self.consecutive_failures + 1
        if self.consecutive_failures >= 3:
            self.current_limit = self.current_limit // 2
            self.consecutive_failures = 0
    return self.current_limit
"""

CORRECT_CODE = """
def record_outcome(self, success: bool) -> int:
    if success:
        if self.current_limit < 100:
            self.current_limit = self.current_limit + 1
        self.consecutive_failures = 0
    else:
        self.consecutive_failures = self.consecutive_failures + 1
        if self.consecutive_failures >= 3:
            new_limit = self.current_limit // 2
            if new_limit < 1:
                self.current_limit = 1
            else:
                self.current_limit = new_limit
            self.consecutive_failures = 0
    return self.current_limit
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
        tags=["rate-limiting", "adaptive"]
    )
