"""
RP-002: Chain Replication

Sequential writes through a chain.
"""

from rotalabs_verity.core import (
    Example,
    InputVariable,
    ProblemSpec,
    Property,
    StateVariable,
)

PROBLEM_ID = "RP-002"
NAME = "Chain Replication"
CATEGORY = "replication"
DIFFICULTY = "hard"

DESCRIPTION = """
Implement Chain Replication.

forward_write(value, position):
1. If position == my_position:
   - local_value = value
   - If position < chain_length - 1:
     - pending_forwards = pending_forwards + 1
   - return True
2. return False (wrong position)

Constants: chain_length = 3
"""

METHOD_SIGNATURE = "def forward_write(self, value: int, position: int) -> bool"

STATE_VARIABLES = [
    StateVariable(
        name="my_position",
        var_type="int",
        description="Position in chain (0=head, 2=tail)",
        bounds=(0, 2),
        initial_value=0
    ),
    StateVariable(
        name="local_value",
        var_type="int",
        description="Locally stored value",
        bounds=(0, 1000),
        initial_value=0
    ),
    StateVariable(
        name="pending_forwards",
        var_type="int",
        description="Writes pending forward to next node",
        bounds=(0, 10),
        initial_value=0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="value",
        var_type="int",
        description="Value to write",
        bounds=(1, 1000)
    ),
    InputVariable(
        name="position",
        var_type="int",
        description="Target position in chain",
        bounds=(0, 2)
    ),
]

OUTPUT_TYPE = "bool"


def _prop_pending_bounded(pre, post, inputs, output):
    """pending_forwards must not exceed limit."""
    return post["pending_forwards"] <= 10


def _prop_position_unchanged(pre, post, inputs, output):
    """my_position should not change."""
    return post["my_position"] == pre["my_position"]


PROPERTIES = [
    Property(
        name="pending_bounded",
        description="pending_forwards must not exceed limit",
        formula="□(pending_forwards <= max_pending)",
        encode=_prop_pending_bounded
    ),
    Property(
        name="position_unchanged",
        description="my_position should not change",
        formula="□(my_position' == my_position)",
        encode=_prop_position_unchanged
    ),
]


EXAMPLES = [
    Example(
        name="head_write",
        description="Head receives write",
        pre_state={"my_position": 0, "local_value": 0, "pending_forwards": 0},
        inputs={"value": 42, "position": 0},
        expected_output=True,
        expected_post_state={"my_position": 0, "local_value": 42, "pending_forwards": 1}
    ),
]


BUGGY_CODE = """
def forward_write(self, value: int, position: int) -> bool:
    if position == self.my_position:
        self.local_value = value
        if self.my_position < 2:
            # BUG: No bound check on pending_forwards
            self.pending_forwards = self.pending_forwards + 1
        # BUG: Always increments even at tail
        self.pending_forwards = self.pending_forwards + 1
        return True
    return False
"""

CORRECT_CODE = """
def forward_write(self, value: int, position: int) -> bool:
    if position == self.my_position:
        self.local_value = value
        if self.my_position < 2:
            if self.pending_forwards < 10:
                self.pending_forwards = self.pending_forwards + 1
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
        tags=["replication", "chain-replication"]
    )
