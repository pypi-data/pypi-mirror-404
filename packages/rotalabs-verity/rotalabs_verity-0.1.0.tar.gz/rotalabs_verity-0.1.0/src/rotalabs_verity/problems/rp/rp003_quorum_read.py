"""
RP-003: Quorum Read

Read quorum logic for distributed storage.
"""

from rotalabs_verity.core import (
    Example,
    InputVariable,
    ProblemSpec,
    Property,
    StateVariable,
)

PROBLEM_ID = "RP-003"
NAME = "Quorum Read"
CATEGORY = "replication"
DIFFICULTY = "medium"

DESCRIPTION = """
Implement Quorum Read.

collect_read_response(replica_value, replica_version):
1. responses_received = responses_received + 1
2. If replica_version > best_version:
   - best_version = replica_version
   - best_value = replica_value
3. If responses_received >= read_quorum:
   - return True (quorum reached)
4. return False (waiting for more)

Constants: read_quorum = 2
"""

METHOD_SIGNATURE = "def collect_read_response(self, replica_value: int, replica_version: int) -> bool"

STATE_VARIABLES = [
    StateVariable(
        name="responses_received",
        var_type="int",
        description="Number of responses received",
        bounds=(0, 5),
        initial_value=0
    ),
    StateVariable(
        name="best_value",
        var_type="int",
        description="Best value seen (highest version)",
        bounds=(0, 1000),
        initial_value=0
    ),
    StateVariable(
        name="best_version",
        var_type="int",
        description="Highest version seen",
        bounds=(0, 100),
        initial_value=0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="replica_value",
        var_type="int",
        description="Value from replica",
        bounds=(1, 1000)
    ),
    InputVariable(
        name="replica_version",
        var_type="int",
        description="Version from replica",
        bounds=(0, 100)
    ),
]

OUTPUT_TYPE = "bool"


def _prop_responses_bounded(pre, post, inputs, output):
    """responses_received must not exceed max."""
    return post["responses_received"] <= 5


def _prop_version_monotonic(pre, post, inputs, output):
    """best_version must not decrease."""
    return post["best_version"] >= pre["best_version"]


PROPERTIES = [
    Property(
        name="responses_bounded",
        description="responses_received must not exceed max",
        formula="□(responses_received <= max_responses)",
        encode=_prop_responses_bounded
    ),
    Property(
        name="version_monotonic",
        description="best_version must not decrease",
        formula="□(best_version' >= best_version)",
        encode=_prop_version_monotonic
    ),
]


EXAMPLES = [
    Example(
        name="collect_better",
        description="Collect response with better version",
        pre_state={"responses_received": 0, "best_value": 0, "best_version": 0},
        inputs={"replica_value": 42, "replica_version": 3},
        expected_output=False,
        expected_post_state={"responses_received": 1, "best_value": 42, "best_version": 3}
    ),
]


BUGGY_CODE = """
def collect_read_response(self, replica_value: int, replica_version: int) -> bool:
    # BUG: No bound check - always increments
    self.responses_received = self.responses_received + 1
    if replica_version > self.best_version:
        self.best_version = replica_version
        self.best_value = replica_value
    # BUG: Extra increment causes overflow
    self.responses_received = self.responses_received + 1
    if self.responses_received >= 2:
        return True
    return False
"""

CORRECT_CODE = """
def collect_read_response(self, replica_value: int, replica_version: int) -> bool:
    if self.responses_received < 5:
        self.responses_received = self.responses_received + 1
    if replica_version > self.best_version:
        self.best_version = replica_version
        self.best_value = replica_value
    if self.responses_received >= 2:
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
