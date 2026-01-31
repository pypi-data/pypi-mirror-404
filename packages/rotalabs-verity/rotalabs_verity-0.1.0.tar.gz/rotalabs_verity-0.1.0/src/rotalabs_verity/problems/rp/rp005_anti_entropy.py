"""
RP-005: Anti-Entropy

State reconciliation between replicas.
"""

from rotalabs_verity.core import (
    Example,
    InputVariable,
    ProblemSpec,
    Property,
    StateVariable,
)

PROBLEM_ID = "RP-005"
NAME = "Anti-Entropy"
CATEGORY = "replication"
DIFFICULTY = "hard"

DESCRIPTION = """
Implement Anti-Entropy reconciliation.

reconcile(remote_value, remote_version):
1. If remote_version > local_version:
   - local_value = remote_value
   - local_version = remote_version
   - return True (updated)
2. return False (no update needed)
"""

METHOD_SIGNATURE = "def reconcile(self, remote_value: int, remote_version: int) -> bool"

STATE_VARIABLES = [
    StateVariable(
        name="local_value",
        var_type="int",
        description="Local data value",
        bounds=(0, 1000),
        initial_value=0
    ),
    StateVariable(
        name="local_version",
        var_type="int",
        description="Local version number",
        bounds=(0, 100),
        initial_value=0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="remote_value",
        var_type="int",
        description="Value from remote replica",
        bounds=(1, 1000)
    ),
    InputVariable(
        name="remote_version",
        var_type="int",
        description="Version from remote replica",
        bounds=(0, 100)
    ),
]

OUTPUT_TYPE = "bool"


def _prop_version_monotonic(pre, post, inputs, output):
    """local_version must not decrease."""
    return post["local_version"] >= pre["local_version"]


def _prop_value_non_negative(pre, post, inputs, output):
    """local_value must be non-negative."""
    return post["local_value"] >= 0


PROPERTIES = [
    Property(
        name="version_monotonic",
        description="local_version must not decrease",
        formula="□(local_version' >= local_version)",
        encode=_prop_version_monotonic
    ),
    Property(
        name="value_non_negative",
        description="local_value must be non-negative",
        formula="□(local_value >= 0)",
        encode=_prop_value_non_negative
    ),
]


EXAMPLES = [
    Example(
        name="update",
        description="Update from newer remote",
        pre_state={"local_value": 10, "local_version": 2},
        inputs={"remote_value": 42, "remote_version": 5},
        expected_output=True,
        expected_post_state={"local_value": 42, "local_version": 5}
    ),
]


BUGGY_CODE = """
def reconcile(self, remote_value: int, remote_version: int) -> bool:
    if remote_version > self.local_version:
        # BUG: Decreases version instead of updating
        self.local_version = self.local_version - 1
        self.local_value = remote_value
        return True
    return False
"""

CORRECT_CODE = """
def reconcile(self, remote_value: int, remote_version: int) -> bool:
    if remote_version > self.local_version:
        self.local_value = remote_value
        self.local_version = remote_version
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
        tags=["replication", "anti-entropy"]
    )
