"""
CN-005: Paxos Proposer

Proposal submission in Paxos.
"""

from rotalabs_verity.core import (
    Example,
    InputVariable,
    ProblemSpec,
    Property,
    StateVariable,
)

PROBLEM_ID = "CN-005"
NAME = "Paxos Proposer"
CATEGORY = "consensus"
DIFFICULTY = "hard"

DESCRIPTION = """
Implement Paxos Proposer.

prepare(proposal_num):
1. If proposal_num > highest_proposed:
   - highest_proposed = proposal_num
   - promises_received = 0
   - phase = 1 (prepare phase)
   - return True
2. return False (proposal too low)

Constants: quorum = 2
"""

METHOD_SIGNATURE = "def prepare(self, proposal_num: int) -> bool"

STATE_VARIABLES = [
    StateVariable(
        name="highest_proposed",
        var_type="int",
        description="Highest proposal number sent",
        bounds=(0, 100),
        initial_value=0
    ),
    StateVariable(
        name="promises_received",
        var_type="int",
        description="Number of promise responses",
        bounds=(0, 5),
        initial_value=0
    ),
    StateVariable(
        name="phase",
        var_type="int",
        description="Current phase (0=idle, 1=prepare, 2=accept)",
        bounds=(0, 2),
        initial_value=0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="proposal_num",
        var_type="int",
        description="Proposal number to use",
        bounds=(1, 100)
    ),
]

OUTPUT_TYPE = "bool"


def _prop_proposal_monotonic(pre, post, inputs, output):
    """highest_proposed must not decrease."""
    return post["highest_proposed"] >= pre["highest_proposed"]


def _prop_phase_valid(pre, post, inputs, output):
    """phase must be 0, 1, or 2."""
    import z3
    return z3.And(post["phase"] >= 0, post["phase"] <= 2)


PROPERTIES = [
    Property(
        name="proposal_monotonic",
        description="highest_proposed must not decrease",
        formula="□(highest_proposed' >= highest_proposed)",
        encode=_prop_proposal_monotonic
    ),
    Property(
        name="phase_valid",
        description="phase must be 0, 1, or 2",
        formula="□(0 <= phase <= 2)",
        encode=_prop_phase_valid
    ),
]


EXAMPLES = [
    Example(
        name="start_prepare",
        description="Start prepare phase",
        pre_state={"highest_proposed": 0, "promises_received": 0, "phase": 0},
        inputs={"proposal_num": 5},
        expected_output=True,
        expected_post_state={"highest_proposed": 5, "promises_received": 0, "phase": 1}
    ),
]


BUGGY_CODE = """
def prepare(self, proposal_num: int) -> bool:
    if proposal_num > self.highest_proposed:
        self.highest_proposed = proposal_num
        self.promises_received = 0
        # BUG: Sets phase to invalid value
        self.phase = 5
        return True
    return False
"""

CORRECT_CODE = """
def prepare(self, proposal_num: int) -> bool:
    if proposal_num > self.highest_proposed:
        self.highest_proposed = proposal_num
        self.promises_received = 0
        self.phase = 1
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
