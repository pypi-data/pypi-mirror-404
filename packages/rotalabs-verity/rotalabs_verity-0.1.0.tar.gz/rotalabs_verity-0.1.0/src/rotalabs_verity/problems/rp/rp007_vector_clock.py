"""
RP-007: Vector Clock

Causality tracking with vector clocks.
"""

from rotalabs_verity.core import (
    Example,
    InputVariable,
    ProblemSpec,
    Property,
    StateVariable,
)

PROBLEM_ID = "RP-007"
NAME = "Vector Clock"
CATEGORY = "replication"
DIFFICULTY = "hard"

DESCRIPTION = """
Implement Vector Clock update (simplified to 2 nodes).

update_clock(other_clock_0, other_clock_1):
1. clock_0 = max(clock_0, other_clock_0)
2. clock_1 = max(clock_1, other_clock_1)
3. clock_self = clock_self + 1 (increment own component)
4. return clock_self

Uses clock_0, clock_1 for two nodes, clock_self for self.
my_index indicates which component is self (0 or 1).
"""

METHOD_SIGNATURE = "def update_clock(self, other_clock_0: int, other_clock_1: int) -> int"

STATE_VARIABLES = [
    StateVariable(
        name="clock_0",
        var_type="int",
        description="Clock component for node 0",
        bounds=(0, 100),
        initial_value=0
    ),
    StateVariable(
        name="clock_1",
        var_type="int",
        description="Clock component for node 1",
        bounds=(0, 100),
        initial_value=0
    ),
    StateVariable(
        name="my_index",
        var_type="int",
        description="Which node I am (0 or 1)",
        bounds=(0, 1),
        initial_value=0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="other_clock_0",
        var_type="int",
        description="Other's clock component 0",
        bounds=(0, 100)
    ),
    InputVariable(
        name="other_clock_1",
        var_type="int",
        description="Other's clock component 1",
        bounds=(0, 100)
    ),
]

OUTPUT_TYPE = "int"


def _prop_clock_0_monotonic(pre, post, inputs, output):
    """clock_0 must not decrease."""
    return post["clock_0"] >= pre["clock_0"]


def _prop_clock_1_monotonic(pre, post, inputs, output):
    """clock_1 must not decrease."""
    return post["clock_1"] >= pre["clock_1"]


PROPERTIES = [
    Property(
        name="clock_0_monotonic",
        description="clock_0 must not decrease",
        formula="□(clock_0' >= clock_0)",
        encode=_prop_clock_0_monotonic
    ),
    Property(
        name="clock_1_monotonic",
        description="clock_1 must not decrease",
        formula="□(clock_1' >= clock_1)",
        encode=_prop_clock_1_monotonic
    ),
]


EXAMPLES = [
    Example(
        name="merge_clocks",
        description="Merge with other clock",
        pre_state={"clock_0": 2, "clock_1": 1, "my_index": 0},
        inputs={"other_clock_0": 1, "other_clock_1": 3},
        expected_output=3,
        expected_post_state={"clock_0": 3, "clock_1": 3, "my_index": 0}
    ),
]


BUGGY_CODE = """
def update_clock(self, other_clock_0: int, other_clock_1: int) -> int:
    # BUG: Sets to other instead of max
    self.clock_0 = other_clock_0
    self.clock_1 = other_clock_1
    if self.my_index == 0:
        self.clock_0 = self.clock_0 + 1
        return self.clock_0
    else:
        self.clock_1 = self.clock_1 + 1
        return self.clock_1
"""

CORRECT_CODE = """
def update_clock(self, other_clock_0: int, other_clock_1: int) -> int:
    if other_clock_0 > self.clock_0:
        self.clock_0 = other_clock_0
    if other_clock_1 > self.clock_1:
        self.clock_1 = other_clock_1
    if self.my_index == 0:
        self.clock_0 = self.clock_0 + 1
        return self.clock_0
    else:
        self.clock_1 = self.clock_1 + 1
        return self.clock_1
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
        tags=["replication", "vector-clock"]
    )
