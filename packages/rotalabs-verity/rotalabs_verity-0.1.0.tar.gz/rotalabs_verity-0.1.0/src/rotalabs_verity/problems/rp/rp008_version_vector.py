"""
RP-008: Version Vector

Conflict detection with version vectors.
"""

from rotalabs_verity.core import (
    Example,
    InputVariable,
    ProblemSpec,
    Property,
    StateVariable,
)

PROBLEM_ID = "RP-008"
NAME = "Version Vector"
CATEGORY = "replication"
DIFFICULTY = "medium"

DESCRIPTION = """
Implement Version Vector conflict detection.

check_and_update(incoming_version):
1. If incoming_version > local_version:
   - local_version = incoming_version
   - conflicts = 0
   - return 0 (no conflict, updated)
2. If incoming_version < local_version:
   - return 1 (stale, ignored)
3. conflicts = 1
4. return 2 (concurrent, conflict detected)
"""

METHOD_SIGNATURE = "def check_and_update(self, incoming_version: int) -> int"

STATE_VARIABLES = [
    StateVariable(
        name="local_version",
        var_type="int",
        description="Local version number",
        bounds=(0, 100),
        initial_value=0
    ),
    StateVariable(
        name="conflicts",
        var_type="int",
        description="Whether conflicts detected (0 or 1)",
        bounds=(0, 1),
        initial_value=0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="incoming_version",
        var_type="int",
        description="Incoming version number",
        bounds=(0, 100)
    ),
]

OUTPUT_TYPE = "int"


def _prop_version_non_negative(pre, post, inputs, output):
    """local_version must be non-negative."""
    return post["local_version"] >= 0


def _prop_conflicts_valid(pre, post, inputs, output):
    """conflicts must be 0 or 1."""
    import z3
    return z3.And(post["conflicts"] >= 0, post["conflicts"] <= 1)


PROPERTIES = [
    Property(
        name="version_non_negative",
        description="local_version must be non-negative",
        formula="□(local_version >= 0)",
        encode=_prop_version_non_negative
    ),
    Property(
        name="conflicts_valid",
        description="conflicts must be 0 or 1",
        formula="□(0 <= conflicts <= 1)",
        encode=_prop_conflicts_valid
    ),
]


EXAMPLES = [
    Example(
        name="update",
        description="Update from higher version",
        pre_state={"local_version": 2, "conflicts": 0},
        inputs={"incoming_version": 5},
        expected_output=0,
        expected_post_state={"local_version": 5, "conflicts": 0}
    ),
]


BUGGY_CODE = """
def check_and_update(self, incoming_version: int) -> int:
    if incoming_version > self.local_version:
        self.local_version = incoming_version
        self.conflicts = 0
        return 0
    if incoming_version < self.local_version:
        return 1
    # BUG: Sets conflicts to invalid value
    self.conflicts = 5
    return 2
"""

CORRECT_CODE = """
def check_and_update(self, incoming_version: int) -> int:
    if incoming_version > self.local_version:
        self.local_version = incoming_version
        self.conflicts = 0
        return 0
    if incoming_version < self.local_version:
        return 1
    self.conflicts = 1
    return 2
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
        tags=["replication", "version-vector"]
    )
