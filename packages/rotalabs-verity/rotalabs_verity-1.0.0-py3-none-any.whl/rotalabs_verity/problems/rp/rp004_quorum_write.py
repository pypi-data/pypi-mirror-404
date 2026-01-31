"""
RP-004: Quorum Write

Write quorum logic for distributed storage.
"""

from rotalabs_verity.core import (
    Example,
    InputVariable,
    ProblemSpec,
    Property,
    StateVariable,
)

PROBLEM_ID = "RP-004"
NAME = "Quorum Write"
CATEGORY = "replication"
DIFFICULTY = "medium"

DESCRIPTION = """
Implement Quorum Write.

collect_write_ack(replica_id):
1. If acks_received < write_quorum:
   - acks_received = acks_received + 1
2. If acks_received >= write_quorum:
   - committed = 1
   - return True
3. return False (not yet committed)

Constants: write_quorum = 2
"""

METHOD_SIGNATURE = "def collect_write_ack(self, replica_id: int) -> bool"

STATE_VARIABLES = [
    StateVariable(
        name="acks_received",
        var_type="int",
        description="Number of acks received",
        bounds=(0, 5),
        initial_value=0
    ),
    StateVariable(
        name="committed",
        var_type="int",
        description="Whether write is committed (0 or 1)",
        bounds=(0, 1),
        initial_value=0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="replica_id",
        var_type="int",
        description="ID of replica sending ack",
        bounds=(1, 10)
    ),
]

OUTPUT_TYPE = "bool"


def _prop_acks_bounded(pre, post, inputs, output):
    """acks_received must not exceed max."""
    return post["acks_received"] <= 5


def _prop_committed_valid(pre, post, inputs, output):
    """committed must be 0 or 1."""
    import z3
    return z3.And(post["committed"] >= 0, post["committed"] <= 1)


PROPERTIES = [
    Property(
        name="acks_bounded",
        description="acks_received must not exceed max",
        formula="□(acks_received <= max_acks)",
        encode=_prop_acks_bounded
    ),
    Property(
        name="committed_valid",
        description="committed must be 0 or 1",
        formula="□(0 <= committed <= 1)",
        encode=_prop_committed_valid
    ),
]


EXAMPLES = [
    Example(
        name="collect_ack",
        description="Collect write acknowledgment",
        pre_state={"acks_received": 1, "committed": 0},
        inputs={"replica_id": 2},
        expected_output=True,
        expected_post_state={"acks_received": 2, "committed": 1}
    ),
]


BUGGY_CODE = """
def collect_write_ack(self, replica_id: int) -> bool:
    # BUG: No bound check
    self.acks_received = self.acks_received + 1
    if self.acks_received >= 2:
        # BUG: Sets committed to invalid value
        self.committed = 2
        return True
    return False
"""

CORRECT_CODE = """
def collect_write_ack(self, replica_id: int) -> bool:
    if self.acks_received < 5:
        self.acks_received = self.acks_received + 1
    if self.acks_received >= 2:
        self.committed = 1
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
        tags=["replication", "quorum"]
    )
