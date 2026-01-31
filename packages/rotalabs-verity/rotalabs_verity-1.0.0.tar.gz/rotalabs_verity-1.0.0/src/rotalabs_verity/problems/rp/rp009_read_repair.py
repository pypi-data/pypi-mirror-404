"""
RP-009: Read Repair

Consistency repair during reads.
"""

from rotalabs_verity.core import (
    Example,
    InputVariable,
    ProblemSpec,
    Property,
    StateVariable,
)

PROBLEM_ID = "RP-009"
NAME = "Read Repair"
CATEGORY = "replication"
DIFFICULTY = "medium"

DESCRIPTION = """
Implement Read Repair.

repair_if_needed(read_value, read_version):
1. If read_version > local_version:
   - local_value = read_value
   - local_version = read_version
   - repairs_done = repairs_done + 1
   - return True (repaired)
2. return False (no repair needed)
"""

METHOD_SIGNATURE = "def repair_if_needed(self, read_value: int, read_version: int) -> bool"

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
    StateVariable(
        name="repairs_done",
        var_type="int",
        description="Count of repairs performed",
        bounds=(0, 100),
        initial_value=0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="read_value",
        var_type="int",
        description="Value read from other replica",
        bounds=(1, 1000)
    ),
    InputVariable(
        name="read_version",
        var_type="int",
        description="Version read from other replica",
        bounds=(0, 100)
    ),
]

OUTPUT_TYPE = "bool"


def _prop_version_monotonic(pre, post, inputs, output):
    """local_version must not decrease."""
    return post["local_version"] >= pre["local_version"]


def _prop_repairs_monotonic(pre, post, inputs, output):
    """repairs_done must not decrease."""
    return post["repairs_done"] >= pre["repairs_done"]


PROPERTIES = [
    Property(
        name="version_monotonic",
        description="local_version must not decrease",
        formula="□(local_version' >= local_version)",
        encode=_prop_version_monotonic
    ),
    Property(
        name="repairs_monotonic",
        description="repairs_done must not decrease",
        formula="□(repairs_done' >= repairs_done)",
        encode=_prop_repairs_monotonic
    ),
]


EXAMPLES = [
    Example(
        name="repair",
        description="Repair from stale read",
        pre_state={"local_value": 10, "local_version": 2, "repairs_done": 0},
        inputs={"read_value": 42, "read_version": 5},
        expected_output=True,
        expected_post_state={"local_value": 42, "local_version": 5, "repairs_done": 1}
    ),
]


BUGGY_CODE = """
def repair_if_needed(self, read_value: int, read_version: int) -> bool:
    if read_version > self.local_version:
        self.local_value = read_value
        # BUG: Decreases version instead of updating
        self.local_version = self.local_version - 1
        self.repairs_done = self.repairs_done + 1
        return True
    return False
"""

CORRECT_CODE = """
def repair_if_needed(self, read_value: int, read_version: int) -> bool:
    if read_version > self.local_version:
        self.local_value = read_value
        self.local_version = read_version
        self.repairs_done = self.repairs_done + 1
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
        tags=["replication", "read-repair"]
    )
