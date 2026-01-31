"""
CB-005: Health Check

Tracks service health score based on success/failure.
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

PROBLEM_ID = "CB-005"
NAME = "Health Check"
CATEGORY = "circuit_breaker"
DIFFICULTY = "medium"

DESCRIPTION = """
Implement a Health Check tracker.

Track service health score based on recent success/failure outcomes.

record_health(success):
1. If success:
   - health_score = min(100, health_score + recovery_rate)
2. If not success:
   - health_score = max(0, health_score - penalty)
3. Return health_score >= healthy_threshold

Constants: recovery_rate = 10, penalty = 25, healthy_threshold = 50
"""

METHOD_SIGNATURE = "def record_health(self, success: bool) -> bool"

STATE_VARIABLES = [
    StateVariable(
        name="health_score",
        var_type="int",
        description="Current health score (0-100)",
        bounds=(0, 100),
        initial_value=100
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="success",
        var_type="bool",
        description="Whether the health check passed"
    ),
]

OUTPUT_TYPE = "bool"


# =============================================================================
# PROPERTIES
# =============================================================================

def _prop_health_non_negative(pre, post, inputs, output):
    """Health score must never go negative."""
    return post["health_score"] >= 0


def _prop_health_bounded(pre, post, inputs, output):
    """Health score must not exceed 100."""
    return post["health_score"] <= 100


PROPERTIES = [
    Property(
        name="health_non_negative",
        description="Health score must never go negative",
        formula="□(health_score >= 0)",
        encode=_prop_health_non_negative
    ),
    Property(
        name="health_bounded",
        description="Health score must not exceed 100",
        formula="□(health_score <= 100)",
        encode=_prop_health_bounded
    ),
]


# =============================================================================
# EXAMPLES
# =============================================================================

EXAMPLES = [
    Example(
        name="success_improves",
        description="Success improves health",
        pre_state={"health_score": 60},
        inputs={"success": True},
        expected_output=True,
        expected_post_state={"health_score": 70}
    ),
    Example(
        name="failure_reduces",
        description="Failure reduces health",
        pre_state={"health_score": 60},
        inputs={"success": False},
        expected_output=False,
        expected_post_state={"health_score": 35}
    ),
]


# =============================================================================
# REFERENCE IMPLEMENTATIONS
# =============================================================================

BUGGY_CODE = """
def record_health(self, success: bool) -> bool:
    if success:
        # BUG: No upper bound check
        self.health_score = self.health_score + 10
    else:
        self.health_score = self.health_score - 25
        if self.health_score < 0:
            self.health_score = 0
    if self.health_score >= 50:
        return True
    return False
"""

CORRECT_CODE = """
def record_health(self, success: bool) -> bool:
    if success:
        new_score = self.health_score + 10
        if new_score > 100:
            self.health_score = 100
        else:
            self.health_score = new_score
    else:
        new_score = self.health_score - 25
        if new_score < 0:
            self.health_score = 0
        else:
            self.health_score = new_score
    if self.health_score >= 50:
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
        tags=["circuit-breaker", "health-check"]
    )
