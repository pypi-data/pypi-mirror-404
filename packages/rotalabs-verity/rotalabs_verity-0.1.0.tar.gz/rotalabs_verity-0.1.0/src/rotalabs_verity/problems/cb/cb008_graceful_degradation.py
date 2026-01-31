"""
CB-008: Graceful Degradation

Progressive feature disabling under load.
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

PROBLEM_ID = "CB-008"
NAME = "Graceful Degradation"
CATEGORY = "circuit_breaker"
DIFFICULTY = "hard"

DESCRIPTION = """
Implement Graceful Degradation.

Track system load and progressively disable features.

update_degradation(load):
1. If load >= critical_load:
   - degradation_level = 3 (minimal features)
2. Else if load >= high_load:
   - degradation_level = 2 (reduced features)
3. Else if load >= medium_load:
   - degradation_level = 1 (some features disabled)
4. Else:
   - degradation_level = 0 (full features)
5. Return degradation_level

Constants: medium_load = 50, high_load = 75, critical_load = 90
"""

METHOD_SIGNATURE = "def update_degradation(self, load: int) -> int"

STATE_VARIABLES = [
    StateVariable(
        name="degradation_level",
        var_type="int",
        description="Current degradation level (0-3)",
        bounds=(0, 3),
        initial_value=0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="load",
        var_type="int",
        description="Current system load (0-100)",
        bounds=(0, 100)
    ),
]

OUTPUT_TYPE = "int"


# =============================================================================
# PROPERTIES
# =============================================================================

def _prop_level_non_negative(pre, post, inputs, output):
    """Degradation level must be non-negative."""
    return post["degradation_level"] >= 0


def _prop_level_bounded(pre, post, inputs, output):
    """Degradation level must not exceed 3."""
    return post["degradation_level"] <= 3


PROPERTIES = [
    Property(
        name="level_non_negative",
        description="Degradation level must be non-negative",
        formula="□(degradation_level >= 0)",
        encode=_prop_level_non_negative
    ),
    Property(
        name="level_bounded",
        description="Degradation level must not exceed 3",
        formula="□(degradation_level <= 3)",
        encode=_prop_level_bounded
    ),
]


# =============================================================================
# EXAMPLES
# =============================================================================

EXAMPLES = [
    Example(
        name="low_load",
        description="Low load means full features",
        pre_state={"degradation_level": 2},
        inputs={"load": 30},
        expected_output=0,
        expected_post_state={"degradation_level": 0}
    ),
    Example(
        name="critical_load",
        description="Critical load means minimal features",
        pre_state={"degradation_level": 0},
        inputs={"load": 95},
        expected_output=3,
        expected_post_state={"degradation_level": 3}
    ),
]


# =============================================================================
# REFERENCE IMPLEMENTATIONS
# =============================================================================

BUGGY_CODE = """
def update_degradation(self, load: int) -> int:
    # BUG: Wrong threshold comparisons, allows level 4
    if load > 90:
        self.degradation_level = 4
    else:
        if load > 75:
            self.degradation_level = 2
        else:
            if load > 50:
                self.degradation_level = 1
            else:
                self.degradation_level = 0
    return self.degradation_level
"""

CORRECT_CODE = """
def update_degradation(self, load: int) -> int:
    if load >= 90:
        self.degradation_level = 3
    else:
        if load >= 75:
            self.degradation_level = 2
        else:
            if load >= 50:
                self.degradation_level = 1
            else:
                self.degradation_level = 0
    return self.degradation_level
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
        tags=["circuit-breaker", "graceful-degradation"]
    )
