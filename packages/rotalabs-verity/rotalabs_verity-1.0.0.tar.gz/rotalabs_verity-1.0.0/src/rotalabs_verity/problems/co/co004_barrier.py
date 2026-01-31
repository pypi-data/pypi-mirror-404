"""
CO-004: Barrier

Wait for N parties before proceeding.
"""

from rotalabs_verity.core import (
    Example,
    ProblemSpec,
    Property,
    StateVariable,
)

PROBLEM_ID = "CO-004"
NAME = "Barrier"
CATEGORY = "coordination"
DIFFICULTY = "medium"

DESCRIPTION = """
Implement a Barrier.

arrive():
1. If arrived < parties:
   - arrived += 1
   - If arrived == parties:
     - return True (barrier released)
   - return False (still waiting)
2. return False

Constants: parties = 3
"""

METHOD_SIGNATURE = "def arrive(self) -> bool"

STATE_VARIABLES = [
    StateVariable(
        name="arrived",
        var_type="int",
        description="Number of parties that have arrived",
        bounds=(0, 3),
        initial_value=0
    ),
]

INPUT_VARIABLES = []

OUTPUT_TYPE = "bool"


def _prop_arrived_non_negative(pre, post, inputs, output):
    """arrived must be non-negative."""
    return post["arrived"] >= 0


def _prop_arrived_bounded(pre, post, inputs, output):
    """arrived must not exceed parties."""
    return post["arrived"] <= 3


PROPERTIES = [
    Property(
        name="arrived_non_negative",
        description="arrived must be non-negative",
        formula="□(arrived >= 0)",
        encode=_prop_arrived_non_negative
    ),
    Property(
        name="arrived_bounded",
        description="arrived must not exceed parties",
        formula="□(arrived <= parties)",
        encode=_prop_arrived_bounded
    ),
]


EXAMPLES = [
    Example(
        name="arrive_waiting",
        description="Arrive but still waiting",
        pre_state={"arrived": 1},
        inputs={},
        expected_output=False,
        expected_post_state={"arrived": 2}
    ),
    Example(
        name="arrive_released",
        description="Final arrival releases barrier",
        pre_state={"arrived": 2},
        inputs={},
        expected_output=True,
        expected_post_state={"arrived": 3}
    ),
]


BUGGY_CODE = """
def arrive(self) -> bool:
    # BUG: No upper bound check
    self.arrived = self.arrived + 1
    if self.arrived == 3:
        return True
    return False
"""

CORRECT_CODE = """
def arrive(self) -> bool:
    if self.arrived < 3:
        self.arrived = self.arrived + 1
        if self.arrived == 3:
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
        tags=["coordination", "barrier"]
    )
