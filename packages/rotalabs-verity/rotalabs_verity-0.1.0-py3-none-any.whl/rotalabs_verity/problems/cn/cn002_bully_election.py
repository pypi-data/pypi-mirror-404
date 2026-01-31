"""
CN-002: Bully Election

Highest ID wins election.
"""

from rotalabs_verity.core import (
    Example,
    InputVariable,
    ProblemSpec,
    Property,
    StateVariable,
)

PROBLEM_ID = "CN-002"
NAME = "Bully Election"
CATEGORY = "consensus"
DIFFICULTY = "medium"

DESCRIPTION = """
Implement Bully Election Algorithm.

receive_election(sender_id):
1. If sender_id > my_id:
   - leader = 0 (no leader yet)
   - return 0 (acknowledge higher node)
2. If sender_id < my_id:
   - leader = my_id (I'm the leader)
   - return my_id
3. return leader

The node with highest ID becomes leader.
"""

METHOD_SIGNATURE = "def receive_election(self, sender_id: int) -> int"

STATE_VARIABLES = [
    StateVariable(
        name="my_id",
        var_type="int",
        description="This node's ID",
        bounds=(1, 10),
        initial_value=5
    ),
    StateVariable(
        name="leader",
        var_type="int",
        description="Current known leader",
        bounds=(0, 10),
        initial_value=0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="sender_id",
        var_type="int",
        description="ID of node sending election message",
        bounds=(1, 10)
    ),
]

OUTPUT_TYPE = "int"


def _prop_leader_valid(pre, post, inputs, output):
    """Leader must be in valid range."""
    import z3
    return z3.And(post["leader"] >= 0, post["leader"] <= 10)


def _prop_my_id_unchanged(pre, post, inputs, output):
    """my_id should not change."""
    return post["my_id"] == pre["my_id"]


PROPERTIES = [
    Property(
        name="leader_valid",
        description="Leader must be in valid range",
        formula="□(0 <= leader <= 10)",
        encode=_prop_leader_valid
    ),
    Property(
        name="my_id_unchanged",
        description="my_id should not change",
        formula="□(my_id' == my_id)",
        encode=_prop_my_id_unchanged
    ),
]


EXAMPLES = [
    Example(
        name="higher_wins",
        description="Higher ID takes over",
        pre_state={"my_id": 5, "leader": 5},
        inputs={"sender_id": 8},
        expected_output=0,
        expected_post_state={"my_id": 5, "leader": 0}
    ),
]


BUGGY_CODE = """
def receive_election(self, sender_id: int) -> int:
    if sender_id > self.my_id:
        self.leader = 0
        return 0
    else:
        # BUG: Sets leader to invalid value
        self.leader = 99
        return self.my_id
"""

CORRECT_CODE = """
def receive_election(self, sender_id: int) -> int:
    if sender_id > self.my_id:
        self.leader = 0
        return 0
    else:
        self.leader = self.my_id
        return self.my_id
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
        tags=["consensus", "bully-election"]
    )
