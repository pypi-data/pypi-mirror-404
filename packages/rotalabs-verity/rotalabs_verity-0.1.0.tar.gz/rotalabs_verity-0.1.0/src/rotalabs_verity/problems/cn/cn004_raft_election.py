"""
CN-004: Raft Election

Term-based voting for leader election.
"""

from rotalabs_verity.core import (
    Example,
    InputVariable,
    ProblemSpec,
    Property,
    StateVariable,
)

PROBLEM_ID = "CN-004"
NAME = "Raft Election"
CATEGORY = "consensus"
DIFFICULTY = "hard"

DESCRIPTION = """
Implement Raft Election voting.

request_vote(candidate_term, candidate_id):
1. If candidate_term > current_term:
   - current_term = candidate_term
   - voted_for = candidate_id
   - return True
2. If candidate_term == current_term and voted_for == 0:
   - voted_for = candidate_id
   - return True
3. return False
"""

METHOD_SIGNATURE = "def request_vote(self, candidate_term: int, candidate_id: int) -> bool"

STATE_VARIABLES = [
    StateVariable(
        name="current_term",
        var_type="int",
        description="Current term number",
        bounds=(0, 100),
        initial_value=0
    ),
    StateVariable(
        name="voted_for",
        var_type="int",
        description="ID voted for in current term (0 if none)",
        bounds=(0, 100),
        initial_value=0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="candidate_term",
        var_type="int",
        description="Candidate's term",
        bounds=(0, 100)
    ),
    InputVariable(
        name="candidate_id",
        var_type="int",
        description="Candidate's ID",
        bounds=(1, 100)
    ),
]

OUTPUT_TYPE = "bool"


def _prop_term_monotonic(pre, post, inputs, output):
    """Term must not decrease."""
    return post["current_term"] >= pre["current_term"]


def _prop_voted_for_non_negative(pre, post, inputs, output):
    """voted_for must be non-negative."""
    return post["voted_for"] >= 0


PROPERTIES = [
    Property(
        name="term_monotonic",
        description="Term must not decrease",
        formula="□(current_term' >= current_term)",
        encode=_prop_term_monotonic
    ),
    Property(
        name="voted_for_non_negative",
        description="voted_for must be non-negative",
        formula="□(voted_for >= 0)",
        encode=_prop_voted_for_non_negative
    ),
]


EXAMPLES = [
    Example(
        name="grant_vote",
        description="Grant vote for higher term",
        pre_state={"current_term": 1, "voted_for": 0},
        inputs={"candidate_term": 2, "candidate_id": 5},
        expected_output=True,
        expected_post_state={"current_term": 2, "voted_for": 5}
    ),
]


BUGGY_CODE = """
def request_vote(self, candidate_term: int, candidate_id: int) -> bool:
    if candidate_term > self.current_term:
        # BUG: Sets term to negative
        self.current_term = self.current_term - candidate_term
        self.voted_for = candidate_id
        return True
    if candidate_term == self.current_term:
        if self.voted_for == 0:
            self.voted_for = candidate_id
            return True
    return False
"""

CORRECT_CODE = """
def request_vote(self, candidate_term: int, candidate_id: int) -> bool:
    if candidate_term > self.current_term:
        self.current_term = candidate_term
        self.voted_for = candidate_id
        return True
    if candidate_term == self.current_term:
        if self.voted_for == 0:
            self.voted_for = candidate_id
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
        tags=["consensus", "raft"]
    )
