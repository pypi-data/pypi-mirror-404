"""
CN-006: Paxos Acceptor

Promise/accept logic in Paxos.
"""

from rotalabs_verity.core import (
    Example,
    InputVariable,
    ProblemSpec,
    Property,
    StateVariable,
)

PROBLEM_ID = "CN-006"
NAME = "Paxos Acceptor"
CATEGORY = "consensus"
DIFFICULTY = "hard"

DESCRIPTION = """
Implement Paxos Acceptor.

receive_prepare(proposal_num):
1. If proposal_num > promised:
   - promised = proposal_num
   - return True (promise)
2. return False (reject)

The acceptor promises not to accept lower proposals.
"""

METHOD_SIGNATURE = "def receive_prepare(self, proposal_num: int) -> bool"

STATE_VARIABLES = [
    StateVariable(
        name="promised",
        var_type="int",
        description="Highest promised proposal number",
        bounds=(0, 100),
        initial_value=0
    ),
    StateVariable(
        name="accepted_num",
        var_type="int",
        description="Accepted proposal number",
        bounds=(0, 100),
        initial_value=0
    ),
    StateVariable(
        name="accepted_value",
        var_type="int",
        description="Accepted value",
        bounds=(0, 100),
        initial_value=0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="proposal_num",
        var_type="int",
        description="Proposal number in prepare request",
        bounds=(1, 100)
    ),
]

OUTPUT_TYPE = "bool"


def _prop_promised_monotonic(pre, post, inputs, output):
    """promised must not decrease."""
    return post["promised"] >= pre["promised"]


def _prop_promised_non_negative(pre, post, inputs, output):
    """promised must be non-negative."""
    return post["promised"] >= 0


PROPERTIES = [
    Property(
        name="promised_monotonic",
        description="promised must not decrease",
        formula="□(promised' >= promised)",
        encode=_prop_promised_monotonic
    ),
    Property(
        name="promised_non_negative",
        description="promised must be non-negative",
        formula="□(promised >= 0)",
        encode=_prop_promised_non_negative
    ),
]


EXAMPLES = [
    Example(
        name="promise",
        description="Promise for higher proposal",
        pre_state={"promised": 3, "accepted_num": 0, "accepted_value": 0},
        inputs={"proposal_num": 5},
        expected_output=True,
        expected_post_state={"promised": 5, "accepted_num": 0, "accepted_value": 0}
    ),
]


BUGGY_CODE = """
def receive_prepare(self, proposal_num: int) -> bool:
    if proposal_num > self.promised:
        # BUG: Decreases promised instead of increasing
        self.promised = self.promised - 1
        return True
    return False
"""

CORRECT_CODE = """
def receive_prepare(self, proposal_num: int) -> bool:
    if proposal_num > self.promised:
        self.promised = proposal_num
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
        tags=["consensus", "paxos"]
    )
