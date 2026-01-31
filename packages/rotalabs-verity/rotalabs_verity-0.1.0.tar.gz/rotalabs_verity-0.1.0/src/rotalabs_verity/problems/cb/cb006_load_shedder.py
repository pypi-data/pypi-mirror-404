"""
CB-006: Load Shedder

Drops requests under high load to protect the system.
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

PROBLEM_ID = "CB-006"
NAME = "Load Shedder"
CATEGORY = "circuit_breaker"
DIFFICULTY = "hard"

DESCRIPTION = """
Implement a Load Shedder.

The load shedder tracks current load and drops requests when overloaded.

should_shed(priority):
1. If current_load >= critical_threshold:
   - return True (shed all)
2. If current_load >= high_threshold and priority < 5:
   - return True (shed low priority)
3. return False

record_load(delta):
1. current_load = max(0, min(100, current_load + delta))
2. return current_load

Constants: high_threshold = 70, critical_threshold = 90
"""

METHOD_SIGNATURE = "def record_load(self, delta: int) -> int"

STATE_VARIABLES = [
    StateVariable(
        name="current_load",
        var_type="int",
        description="Current system load (0-100)",
        bounds=(0, 100),
        initial_value=0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="delta",
        var_type="int",
        description="Load change (positive or negative)",
        bounds=(-50, 50)
    ),
]

OUTPUT_TYPE = "int"


# =============================================================================
# PROPERTIES
# =============================================================================

def _prop_load_non_negative(pre, post, inputs, output):
    """Load must never go negative."""
    return post["current_load"] >= 0


def _prop_load_bounded(pre, post, inputs, output):
    """Load must not exceed 100."""
    return post["current_load"] <= 100


PROPERTIES = [
    Property(
        name="load_non_negative",
        description="Load must never go negative",
        formula="□(current_load >= 0)",
        encode=_prop_load_non_negative
    ),
    Property(
        name="load_bounded",
        description="Load must not exceed 100",
        formula="□(current_load <= 100)",
        encode=_prop_load_bounded
    ),
]


# =============================================================================
# EXAMPLES
# =============================================================================

EXAMPLES = [
    Example(
        name="increase_load",
        description="Increase load within bounds",
        pre_state={"current_load": 50},
        inputs={"delta": 30},
        expected_output=80,
        expected_post_state={"current_load": 80}
    ),
    Example(
        name="decrease_load",
        description="Decrease load",
        pre_state={"current_load": 50},
        inputs={"delta": -30},
        expected_output=20,
        expected_post_state={"current_load": 20}
    ),
]


# =============================================================================
# REFERENCE IMPLEMENTATIONS
# =============================================================================

BUGGY_CODE = """
def record_load(self, delta: int) -> int:
    # BUG: No bounds checking
    self.current_load = self.current_load + delta
    return self.current_load
"""

CORRECT_CODE = """
def record_load(self, delta: int) -> int:
    new_load = self.current_load + delta
    if new_load < 0:
        self.current_load = 0
    else:
        if new_load > 100:
            self.current_load = 100
        else:
            self.current_load = new_load
    return self.current_load
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
        tags=["circuit-breaker", "load-shedding"]
    )
