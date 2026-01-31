"""
CN-007: View Change

Leader replacement protocol.
"""

from rotalabs_verity.core import (
    Example,
    InputVariable,
    ProblemSpec,
    Property,
    StateVariable,
)

PROBLEM_ID = "CN-007"
NAME = "View Change"
CATEGORY = "consensus"
DIFFICULTY = "hard"

DESCRIPTION = """
Implement View Change protocol.

start_view_change(new_view):
1. If new_view > current_view:
   - current_view = new_view
   - leader = new_view % num_nodes
   - in_view_change = 1
   - return True
2. return False (stale view)

Constants: num_nodes = 3
"""

METHOD_SIGNATURE = "def start_view_change(self, new_view: int) -> bool"

STATE_VARIABLES = [
    StateVariable(
        name="current_view",
        var_type="int",
        description="Current view number",
        bounds=(0, 100),
        initial_value=0
    ),
    StateVariable(
        name="leader",
        var_type="int",
        description="Current leader (view % num_nodes)",
        bounds=(0, 2),
        initial_value=0
    ),
    StateVariable(
        name="in_view_change",
        var_type="int",
        description="Whether view change in progress (0 or 1)",
        bounds=(0, 1),
        initial_value=0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="new_view",
        var_type="int",
        description="New view number",
        bounds=(1, 100)
    ),
]

OUTPUT_TYPE = "bool"


def _prop_view_monotonic(pre, post, inputs, output):
    """current_view must not decrease."""
    return post["current_view"] >= pre["current_view"]


def _prop_in_view_change_valid(pre, post, inputs, output):
    """in_view_change must be 0 or 1."""
    import z3
    return z3.And(post["in_view_change"] >= 0, post["in_view_change"] <= 1)


PROPERTIES = [
    Property(
        name="view_monotonic",
        description="current_view must not decrease",
        formula="□(current_view' >= current_view)",
        encode=_prop_view_monotonic
    ),
    Property(
        name="in_view_change_valid",
        description="in_view_change must be 0 or 1",
        formula="□(0 <= in_view_change <= 1)",
        encode=_prop_in_view_change_valid
    ),
]


EXAMPLES = [
    Example(
        name="start_change",
        description="Start view change",
        pre_state={"current_view": 1, "leader": 1, "in_view_change": 0},
        inputs={"new_view": 3},
        expected_output=True,
        expected_post_state={"current_view": 3, "leader": 0, "in_view_change": 1}
    ),
]


BUGGY_CODE = """
def start_view_change(self, new_view: int) -> bool:
    if new_view > self.current_view:
        self.current_view = new_view
        self.leader = new_view % 3
        # BUG: Sets in_view_change to invalid value
        self.in_view_change = 2
        return True
    return False
"""

CORRECT_CODE = """
def start_view_change(self, new_view: int) -> bool:
    if new_view > self.current_view:
        self.current_view = new_view
        self.leader = new_view % 3
        self.in_view_change = 1
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
        tags=["consensus", "view-change"]
    )
