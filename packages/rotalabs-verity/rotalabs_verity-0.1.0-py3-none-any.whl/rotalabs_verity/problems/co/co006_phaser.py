"""
CO-006: Phaser

Multi-phase synchronization.
"""

from rotalabs_verity.core import (
    Example,
    ProblemSpec,
    Property,
    StateVariable,
)

PROBLEM_ID = "CO-006"
NAME = "Phaser"
CATEGORY = "coordination"
DIFFICULTY = "hard"

DESCRIPTION = """
Implement a Phaser for multi-phase synchronization.

arrive_and_advance():
1. arrived += 1
2. If arrived >= registered:
   - phase += 1
   - arrived = 0
   - return phase
3. return phase

Constants: registered = 3
"""

METHOD_SIGNATURE = "def arrive_and_advance(self) -> int"

STATE_VARIABLES = [
    StateVariable(
        name="arrived",
        var_type="int",
        description="Parties arrived in current phase",
        bounds=(0, 3),
        initial_value=0
    ),
    StateVariable(
        name="phase",
        var_type="int",
        description="Current phase number",
        bounds=(0, 100),
        initial_value=0
    ),
]

INPUT_VARIABLES = []

OUTPUT_TYPE = "int"


def _prop_arrived_bounded(pre, post, inputs, output):
    """arrived must not exceed registered."""
    return post["arrived"] <= 3


def _prop_arrived_non_negative(pre, post, inputs, output):
    """arrived must be non-negative."""
    return post["arrived"] >= 0


def _prop_phase_non_negative(pre, post, inputs, output):
    """phase must be non-negative."""
    return post["phase"] >= 0


PROPERTIES = [
    Property(
        name="arrived_bounded",
        description="arrived must not exceed registered",
        formula="□(arrived <= registered)",
        encode=_prop_arrived_bounded
    ),
    Property(
        name="arrived_non_negative",
        description="arrived must be non-negative",
        formula="□(arrived >= 0)",
        encode=_prop_arrived_non_negative
    ),
]


EXAMPLES = [
    Example(
        name="arrive_waiting",
        description="Arrive but phase not complete",
        pre_state={"arrived": 1, "phase": 0},
        inputs={},
        expected_output=0,
        expected_post_state={"arrived": 2, "phase": 0}
    ),
    Example(
        name="phase_advance",
        description="Final arrival advances phase",
        pre_state={"arrived": 2, "phase": 0},
        inputs={},
        expected_output=1,
        expected_post_state={"arrived": 0, "phase": 1}
    ),
]


BUGGY_CODE = """
def arrive_and_advance(self) -> int:
    # BUG: No upper bound check on arrived
    self.arrived = self.arrived + 1
    if self.arrived >= 3:
        self.phase = self.phase + 1
    return self.phase
"""

CORRECT_CODE = """
def arrive_and_advance(self) -> int:
    if self.arrived < 3:
        self.arrived = self.arrived + 1
    if self.arrived >= 3:
        self.phase = self.phase + 1
        self.arrived = 0
    return self.phase
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
        tags=["coordination", "phaser"]
    )
