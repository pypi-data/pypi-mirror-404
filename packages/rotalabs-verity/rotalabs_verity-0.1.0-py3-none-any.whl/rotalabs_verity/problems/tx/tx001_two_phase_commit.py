"""
TX-001: Two-Phase Commit Coordinator

Prepare/commit protocol for distributed transactions.
"""

from rotalabs_verity.core import (
    Example,
    InputVariable,
    ProblemSpec,
    Property,
    StateVariable,
)

PROBLEM_ID = "TX-001"
NAME = "Two-Phase Commit Coordinator"
CATEGORY = "transaction"
DIFFICULTY = "hard"

DESCRIPTION = """
Implement a Two-Phase Commit Coordinator.

States: INIT=0, PREPARING=1, PREPARED=2, COMMITTING=3, COMMITTED=4, ABORTED=5

prepare_vote(vote):
1. If state == PREPARING:
   - If vote == 1 (yes):
     - votes_yes += 1
     - If votes_yes >= required:
       - state = PREPARED
   - Else:
     - state = ABORTED
   - return state
2. return state

Constants: required = 3
"""

METHOD_SIGNATURE = "def prepare_vote(self, vote: int) -> int"

STATE_VARIABLES = [
    StateVariable(
        name="state",
        var_type="int",
        description="Coordinator state (0-5)",
        bounds=(0, 5),
        initial_value=1  # PREPARING
    ),
    StateVariable(
        name="votes_yes",
        var_type="int",
        description="Number of yes votes",
        bounds=(0, 3),
        initial_value=0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="vote",
        var_type="int",
        description="Vote (0=no, 1=yes)",
        bounds=(0, 1)
    ),
]

OUTPUT_TYPE = "int"


def _prop_state_valid(pre, post, inputs, output):
    """State must be in valid range."""
    import z3
    return z3.And(post["state"] >= 0, post["state"] <= 5)


def _prop_votes_bounded(pre, post, inputs, output):
    """Votes must not exceed required."""
    return post["votes_yes"] <= 3


PROPERTIES = [
    Property(
        name="state_valid",
        description="State must be valid (0-5)",
        formula="□(0 <= state <= 5)",
        encode=_prop_state_valid
    ),
    Property(
        name="votes_bounded",
        description="Votes must not exceed required",
        formula="□(votes_yes <= required)",
        encode=_prop_votes_bounded
    ),
]


EXAMPLES = [
    Example(
        name="vote_yes",
        description="Record yes vote",
        pre_state={"state": 1, "votes_yes": 1},
        inputs={"vote": 1},
        expected_output=1,
        expected_post_state={"state": 1, "votes_yes": 2}
    ),
    Example(
        name="vote_no_aborts",
        description="No vote aborts",
        pre_state={"state": 1, "votes_yes": 1},
        inputs={"vote": 0},
        expected_output=5,
        expected_post_state={"state": 5, "votes_yes": 1}
    ),
]


BUGGY_CODE = """
def prepare_vote(self, vote: int) -> int:
    if self.state == 1:
        if vote == 1:
            # BUG: No bound check on votes
            self.votes_yes = self.votes_yes + 1
            if self.votes_yes >= 3:
                self.state = 2
        else:
            self.state = 5
    return self.state
"""

CORRECT_CODE = """
def prepare_vote(self, vote: int) -> int:
    if self.state == 1:
        if vote == 1:
            if self.votes_yes < 3:
                self.votes_yes = self.votes_yes + 1
            if self.votes_yes >= 3:
                self.state = 2
        else:
            self.state = 5
    return self.state
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
        tags=["transaction", "2pc"]
    )
