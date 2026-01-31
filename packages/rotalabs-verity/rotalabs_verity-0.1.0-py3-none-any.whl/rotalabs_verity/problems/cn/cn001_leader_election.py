"""
CN-001: Leader Election

Basic leader selection.
"""

from rotalabs_verity.core import (
    Example,
    InputVariable,
    ProblemSpec,
    Property,
    StateVariable,
)

PROBLEM_ID = "CN-001"
NAME = "Leader Election"
CATEGORY = "consensus"
DIFFICULTY = "medium"

DESCRIPTION = """
Implement Leader Election.

propose_leader(candidate_id):
1. If no_leader (leader == 0):
   - If candidate_id > current_candidate:
     - current_candidate = candidate_id
   - If votes >= quorum:
     - leader = current_candidate
     - return leader
2. return leader

Constants: quorum = 2
"""

METHOD_SIGNATURE = "def propose_leader(self, candidate_id: int) -> int"

STATE_VARIABLES = [
    StateVariable(
        name="leader",
        var_type="int",
        description="Current leader (0 if none)",
        bounds=(0, 100),
        initial_value=0
    ),
    StateVariable(
        name="current_candidate",
        var_type="int",
        description="Current candidate being considered",
        bounds=(0, 100),
        initial_value=0
    ),
    StateVariable(
        name="votes",
        var_type="int",
        description="Votes for current candidate",
        bounds=(0, 5),
        initial_value=0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="candidate_id",
        var_type="int",
        description="ID of proposed candidate",
        bounds=(1, 100)
    ),
]

OUTPUT_TYPE = "int"


def _prop_leader_non_negative(pre, post, inputs, output):
    """Leader must be non-negative."""
    return post["leader"] >= 0


def _prop_votes_bounded(pre, post, inputs, output):
    """Votes must not exceed max."""
    return post["votes"] <= 5


PROPERTIES = [
    Property(
        name="leader_non_negative",
        description="Leader must be non-negative",
        formula="□(leader >= 0)",
        encode=_prop_leader_non_negative
    ),
    Property(
        name="votes_bounded",
        description="Votes must not exceed max",
        formula="□(votes <= max_votes)",
        encode=_prop_votes_bounded
    ),
]


EXAMPLES = [
    Example(
        name="propose",
        description="Propose a candidate",
        pre_state={"leader": 0, "current_candidate": 0, "votes": 0},
        inputs={"candidate_id": 5},
        expected_output=0,
        expected_post_state={"leader": 0, "current_candidate": 5, "votes": 1}
    ),
]


BUGGY_CODE = """
def propose_leader(self, candidate_id: int) -> int:
    if self.leader == 0:
        if candidate_id > self.current_candidate:
            self.current_candidate = candidate_id
        # BUG: No bound check on votes
        self.votes = self.votes + 1
        if self.votes >= 2:
            self.leader = self.current_candidate
    return self.leader
"""

CORRECT_CODE = """
def propose_leader(self, candidate_id: int) -> int:
    if self.leader == 0:
        if candidate_id > self.current_candidate:
            self.current_candidate = candidate_id
        if self.votes < 5:
            self.votes = self.votes + 1
        if self.votes >= 2:
            self.leader = self.current_candidate
    return self.leader
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
        tags=["consensus", "leader-election"]
    )
