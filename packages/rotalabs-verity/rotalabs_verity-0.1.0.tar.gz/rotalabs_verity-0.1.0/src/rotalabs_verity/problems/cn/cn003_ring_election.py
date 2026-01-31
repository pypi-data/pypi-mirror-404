"""
CN-003: Ring Election

Token passing election in a ring.
"""

from rotalabs_verity.core import (
    Example,
    InputVariable,
    ProblemSpec,
    Property,
    StateVariable,
)

PROBLEM_ID = "CN-003"
NAME = "Ring Election"
CATEGORY = "consensus"
DIFFICULTY = "easy"

DESCRIPTION = """
Implement Ring Election.

pass_token(token_id):
1. If token_id > max_seen:
   - max_seen = token_id
2. If token_id == my_id:
   - leader = max_seen
   - return True (election complete)
3. return False (continue passing)
"""

METHOD_SIGNATURE = "def pass_token(self, token_id: int) -> bool"

STATE_VARIABLES = [
    StateVariable(
        name="max_seen",
        var_type="int",
        description="Maximum ID seen so far",
        bounds=(0, 100),
        initial_value=0
    ),
    StateVariable(
        name="leader",
        var_type="int",
        description="Elected leader",
        bounds=(0, 100),
        initial_value=0
    ),
    StateVariable(
        name="my_id",
        var_type="int",
        description="This node's ID",
        bounds=(1, 100),
        initial_value=5
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="token_id",
        var_type="int",
        description="ID on the token",
        bounds=(1, 100)
    ),
]

OUTPUT_TYPE = "bool"


def _prop_max_seen_non_negative(pre, post, inputs, output):
    """max_seen must be non-negative."""
    return post["max_seen"] >= 0


def _prop_leader_non_negative(pre, post, inputs, output):
    """leader must be non-negative."""
    return post["leader"] >= 0


PROPERTIES = [
    Property(
        name="max_seen_non_negative",
        description="max_seen must be non-negative",
        formula="□(max_seen >= 0)",
        encode=_prop_max_seen_non_negative
    ),
    Property(
        name="leader_non_negative",
        description="leader must be non-negative",
        formula="□(leader >= 0)",
        encode=_prop_leader_non_negative
    ),
]


EXAMPLES = [
    Example(
        name="update_max",
        description="Update max_seen with higher token",
        pre_state={"max_seen": 3, "leader": 0, "my_id": 5},
        inputs={"token_id": 7},
        expected_output=False,
        expected_post_state={"max_seen": 7, "leader": 0, "my_id": 5}
    ),
]


BUGGY_CODE = """
def pass_token(self, token_id: int) -> bool:
    if token_id > self.max_seen:
        self.max_seen = token_id
    if token_id == self.my_id:
        # BUG: Sets leader to -1
        self.leader = -1
        return True
    return False
"""

CORRECT_CODE = """
def pass_token(self, token_id: int) -> bool:
    if token_id > self.max_seen:
        self.max_seen = token_id
    if token_id == self.my_id:
        self.leader = self.max_seen
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
        tags=["consensus", "ring-election"]
    )
