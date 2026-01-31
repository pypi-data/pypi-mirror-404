"""
CB-003: Retry with Backoff

Implements exponential backoff on failure.
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

PROBLEM_ID = "CB-003"
NAME = "Retry with Backoff"
CATEGORY = "circuit_breaker"
DIFFICULTY = "easy"

DESCRIPTION = """
Implement Retry with Exponential Backoff.

Track retry attempts and calculate backoff delay.

record_attempt(success):
1. If success:
   - attempts = 0
   - return 0 (no delay needed)
2. If not success:
   - If attempts < max_attempts:
     - delay = base_delay * (2 ^ attempts)
     - delay = min(delay, max_delay)
     - attempts += 1
     - return delay
   - Else: return -1 (give up)

Constants: base_delay = 100, max_delay = 3200, max_attempts = 5
"""

METHOD_SIGNATURE = "def record_attempt(self, success: bool) -> int"

STATE_VARIABLES = [
    StateVariable(
        name="attempts",
        var_type="int",
        description="Number of failed attempts",
        bounds=(0, 5),
        initial_value=0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="success",
        var_type="bool",
        description="Whether the attempt succeeded"
    ),
]

OUTPUT_TYPE = "int"


# =============================================================================
# PROPERTIES
# =============================================================================

def _prop_attempts_non_negative(pre, post, inputs, output):
    """Attempts must never go negative."""
    return post["attempts"] >= 0


def _prop_attempts_bounded(pre, post, inputs, output):
    """Attempts must not exceed max_attempts."""
    return post["attempts"] <= 5


PROPERTIES = [
    Property(
        name="attempts_non_negative",
        description="Attempts must never go negative",
        formula="□(attempts >= 0)",
        encode=_prop_attempts_non_negative
    ),
    Property(
        name="attempts_bounded",
        description="Attempts must not exceed max_attempts",
        formula="□(attempts <= max_attempts)",
        encode=_prop_attempts_bounded
    ),
]


# =============================================================================
# EXAMPLES
# =============================================================================

EXAMPLES = [
    Example(
        name="success_resets",
        description="Success resets attempts",
        pre_state={"attempts": 3},
        inputs={"success": True},
        expected_output=0,
        expected_post_state={"attempts": 0}
    ),
    Example(
        name="failure_increments",
        description="Failure increments attempts",
        pre_state={"attempts": 2},
        inputs={"success": False},
        expected_output=400,
        expected_post_state={"attempts": 3}
    ),
]


# =============================================================================
# REFERENCE IMPLEMENTATIONS
# =============================================================================

BUGGY_CODE = """
def record_attempt(self, success: bool) -> int:
    if success:
        self.attempts = 0
        return 0
    else:
        # BUG: No max_attempts check, increments forever
        delay = 100
        i = 0
        while i < self.attempts:
            delay = delay * 2
            i = i + 1
        if delay > 3200:
            delay = 3200
        self.attempts = self.attempts + 1
        return delay
"""

CORRECT_CODE = """
def record_attempt(self, success: bool) -> int:
    if success:
        self.attempts = 0
        return 0
    else:
        if self.attempts < 5:
            delay = 100
            i = 0
            while i < self.attempts:
                delay = delay * 2
                i = i + 1
            if delay > 3200:
                delay = 3200
            self.attempts = self.attempts + 1
            return delay
        else:
            return -1
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
        tags=["circuit-breaker", "retry", "backoff"]
    )
