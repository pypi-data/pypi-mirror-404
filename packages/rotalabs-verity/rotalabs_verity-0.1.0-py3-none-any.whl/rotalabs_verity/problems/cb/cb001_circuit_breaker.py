"""
CB-001: Circuit Breaker

A circuit breaker that protects against cascading failures.
"""

import z3

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

PROBLEM_ID = "CB-001"
NAME = "Circuit Breaker"
CATEGORY = "circuit_breaker"
DIFFICULTY = "medium"

DESCRIPTION = """
Implement a Circuit Breaker.

The circuit breaker has three states:
- CLOSED (0): Normal operation, requests pass through
- OPEN (1): Circuit is broken, requests are rejected
- HALF_OPEN (2): Testing if service recovered

State transitions:
- CLOSED -> OPEN: When failure_count >= threshold (threshold=3)
- OPEN -> HALF_OPEN: After timeout period has passed
- HALF_OPEN -> CLOSED: On success
- HALF_OPEN -> OPEN: On failure

Method record_result(success, timestamp):
1. If OPEN and timeout passed: transition to HALF_OPEN
2. If success: reset failure_count, if HALF_OPEN go to CLOSED
3. If failure: increment failure_count, if >= threshold or HALF_OPEN go to OPEN
4. Return current state

Constants: self.threshold = 3, self.timeout = 10.0
"""

METHOD_SIGNATURE = "def record_result(self, success: bool, timestamp: float) -> int"

STATE_VARIABLES = [
    StateVariable(
        name="state",
        var_type="int",
        description="Circuit state: 0=CLOSED, 1=OPEN, 2=HALF_OPEN",
        bounds=(0, 2),
        initial_value=0
    ),
    StateVariable(
        name="failure_count",
        var_type="int",
        description="Number of consecutive failures",
        bounds=(0, 10),
        initial_value=0
    ),
    StateVariable(
        name="last_failure_time",
        var_type="real",
        description="Timestamp of last state change to OPEN",
        bounds=(0.0, 1000.0),
        initial_value=0.0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="success",
        var_type="bool",
        description="Whether the call succeeded"
    ),
    InputVariable(
        name="timestamp",
        var_type="real",
        description="Current timestamp",
        bounds=(0.0, 1000.0)
    ),
]

OUTPUT_TYPE = "int"


# =============================================================================
# PROPERTIES
# =============================================================================

def _prop_state_valid(pre, post, inputs, output):
    """State must be 0, 1, or 2."""
    return z3.And(post["state"] >= 0, post["state"] <= 2)


def _prop_failure_count_non_negative(pre, post, inputs, output):
    """Failure count must be non-negative."""
    return post["failure_count"] >= 0


PROPERTIES = [
    Property(
        name="state_valid",
        description="State must be CLOSED(0), OPEN(1), or HALF_OPEN(2)",
        formula="□(0 <= state <= 2)",
        encode=_prop_state_valid
    ),
    Property(
        name="failure_count_non_negative",
        description="Failure count must be non-negative",
        formula="□(failure_count >= 0)",
        encode=_prop_failure_count_non_negative
    ),
]


# =============================================================================
# EXAMPLES
# =============================================================================

EXAMPLES = [
    Example(
        name="record_success",
        description="Record success resets failure count",
        pre_state={"state": 0, "failure_count": 2, "last_failure_time": 0.0},
        inputs={"success": True, "timestamp": 1.0},
        expected_output=0,
        expected_post_state={"state": 0, "failure_count": 0, "last_failure_time": 0.0}
    ),
    Example(
        name="trip_breaker",
        description="Third failure trips the breaker",
        pre_state={"state": 0, "failure_count": 2, "last_failure_time": 0.0},
        inputs={"success": False, "timestamp": 1.0},
        expected_output=1,
        expected_post_state={"state": 1, "failure_count": 3, "last_failure_time": 1.0}
    ),
]


# =============================================================================
# REFERENCE IMPLEMENTATIONS
# =============================================================================

BUGGY_CODE = """
def record_result(self, success: bool, timestamp: float) -> int:
    if success:
        # BUG: Decrements failure_count without checking if it's > 0
        self.failure_count = self.failure_count - 1
        if self.state == 2:
            self.state = 0
    else:
        self.failure_count = self.failure_count + 1
        if self.failure_count >= 3:
            self.state = 1
            self.last_failure_time = timestamp
    return self.state
"""

CORRECT_CODE = """
def record_result(self, success: bool, timestamp: float) -> int:
    if success:
        self.failure_count = 0
        if self.state == 2:
            self.state = 0
    else:
        self.failure_count = self.failure_count + 1
        if self.failure_count >= 3:
            self.state = 1
            self.last_failure_time = timestamp
    return self.state
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
        tags=["circuit-breaker", "fault-tolerance"]
    )
