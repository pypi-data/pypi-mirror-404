"""
RL-003: Leaky Bucket Rate Limiter

A simpler rate limiter using the leaky bucket algorithm.
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

PROBLEM_ID = "RL-003"
NAME = "Leaky Bucket Rate Limiter"
CATEGORY = "rate_limiting"
DIFFICULTY = "easy"

DESCRIPTION = """
Implement a Leaky Bucket Rate Limiter.

The leaky bucket algorithm controls request rate by maintaining a bucket with a fixed
leak rate. Requests add water to the bucket, and if the bucket overflows, the request
is denied.

When a request arrives:
1. Calculate how much has leaked: leaked = elapsed_time * leak_rate
2. Update water level: water = max(0, water - leaked)
3. If water + 1 <= capacity: add water, allow request
4. Otherwise: deny request

Constants: self.leak_rate = 1.0, self.capacity = 10.0
"""

METHOD_SIGNATURE = "def allow(self, timestamp: float) -> bool"

STATE_VARIABLES = [
    StateVariable(
        name="water",
        var_type="real",
        description="Current water level in bucket",
        bounds=(0.0, 10.0),
        initial_value=0.0
    ),
    StateVariable(
        name="last_update",
        var_type="real",
        description="Timestamp of last update",
        bounds=(0.0, 1000.0),
        initial_value=0.0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="timestamp",
        var_type="real",
        description="Current request timestamp",
        bounds=(0.0, 1000.0)
    ),
]

OUTPUT_TYPE = "bool"


# =============================================================================
# PROPERTIES
# =============================================================================

def _prop_water_non_negative(pre, post, inputs, output):
    """Water level must never go negative."""
    return post["water"] >= 0


def _prop_water_bounded(pre, post, inputs, output):
    """Water level must not exceed capacity."""
    return post["water"] <= 10


PROPERTIES = [
    Property(
        name="water_non_negative",
        description="Water level must never go negative",
        formula="□(water >= 0)",
        encode=_prop_water_non_negative
    ),
    Property(
        name="water_bounded",
        description="Water level must not exceed capacity",
        formula="□(water <= capacity)",
        encode=_prop_water_bounded
    ),
]


# =============================================================================
# EXAMPLES
# =============================================================================

EXAMPLES = [
    Example(
        name="allow_empty",
        description="Allow request when bucket is empty",
        pre_state={"water": 0.0, "last_update": 0.0},
        inputs={"timestamp": 0.0},
        expected_output=True,
        expected_post_state={"water": 1.0, "last_update": 0.0}
    ),
    Example(
        name="deny_full",
        description="Deny request when bucket is full",
        pre_state={"water": 10.0, "last_update": 0.0},
        inputs={"timestamp": 0.0},
        expected_output=False,
        expected_post_state={"water": 10.0, "last_update": 0.0}
    ),
]


# =============================================================================
# REFERENCE IMPLEMENTATIONS
# =============================================================================

BUGGY_CODE = """
def allow(self, timestamp: float) -> bool:
    elapsed = timestamp - self.last_update
    leaked = elapsed * 1
    self.water = self.water - leaked
    self.last_update = timestamp
    # BUG: Always adds water without checking capacity
    self.water = self.water + 1
    return True
"""

CORRECT_CODE = """
def allow(self, timestamp: float) -> bool:
    elapsed = timestamp - self.last_update
    if elapsed > 0:
        leaked = elapsed * 1
        self.water = max(0, self.water - leaked)
        self.last_update = timestamp
    if self.water + 1 <= 10:
        self.water = self.water + 1
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
        tags=["rate-limiting", "leaky-bucket"]
    )
