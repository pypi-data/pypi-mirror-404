"""
CN-008: Membership Protocol

Join/leave handling for cluster membership.
"""

from rotalabs_verity.core import (
    Example,
    InputVariable,
    ProblemSpec,
    Property,
    StateVariable,
)

PROBLEM_ID = "CN-008"
NAME = "Membership Protocol"
CATEGORY = "consensus"
DIFFICULTY = "medium"

DESCRIPTION = """
Implement Membership Protocol.

add_member(node_id):
1. If member_count < max_members:
   - member_count = member_count + 1
   - epoch = epoch + 1
   - return True
2. return False (cluster full)

Constants: max_members = 5
"""

METHOD_SIGNATURE = "def add_member(self, node_id: int) -> bool"

STATE_VARIABLES = [
    StateVariable(
        name="member_count",
        var_type="int",
        description="Current number of members",
        bounds=(0, 5),
        initial_value=1
    ),
    StateVariable(
        name="epoch",
        var_type="int",
        description="Membership epoch (increments on changes)",
        bounds=(0, 100),
        initial_value=0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="node_id",
        var_type="int",
        description="ID of node to add",
        bounds=(1, 100)
    ),
]

OUTPUT_TYPE = "bool"


def _prop_member_count_bounded(pre, post, inputs, output):
    """member_count must not exceed max_members."""
    return post["member_count"] <= 5


def _prop_epoch_monotonic(pre, post, inputs, output):
    """epoch must not decrease."""
    return post["epoch"] >= pre["epoch"]


PROPERTIES = [
    Property(
        name="member_count_bounded",
        description="member_count must not exceed max_members",
        formula="□(member_count <= max_members)",
        encode=_prop_member_count_bounded
    ),
    Property(
        name="epoch_monotonic",
        description="epoch must not decrease",
        formula="□(epoch' >= epoch)",
        encode=_prop_epoch_monotonic
    ),
]


EXAMPLES = [
    Example(
        name="add_member",
        description="Add a new member",
        pre_state={"member_count": 2, "epoch": 3},
        inputs={"node_id": 5},
        expected_output=True,
        expected_post_state={"member_count": 3, "epoch": 4}
    ),
]


BUGGY_CODE = """
def add_member(self, node_id: int) -> bool:
    if self.member_count < 5:
        # BUG: No bound check - always increments
        self.member_count = self.member_count + 1
        self.epoch = self.epoch + 1
        return True
    # BUG: Still increments even when full
    self.member_count = self.member_count + 1
    return False
"""

CORRECT_CODE = """
def add_member(self, node_id: int) -> bool:
    if self.member_count < 5:
        self.member_count = self.member_count + 1
        self.epoch = self.epoch + 1
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
        tags=["consensus", "membership"]
    )
