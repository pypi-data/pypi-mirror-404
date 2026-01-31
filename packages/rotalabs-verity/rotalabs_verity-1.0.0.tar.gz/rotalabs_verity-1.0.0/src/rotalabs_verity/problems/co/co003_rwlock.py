"""
CO-003: Read-Write Lock

Multiple readers OR single writer.
"""

from rotalabs_verity.core import (
    Example,
    ProblemSpec,
    Property,
    StateVariable,
)

PROBLEM_ID = "CO-003"
NAME = "Read-Write Lock"
CATEGORY = "coordination"
DIFFICULTY = "hard"

DESCRIPTION = """
Implement a Read-Write Lock.

acquire_read():
1. If write_locked == 0:
   - readers += 1
   - return True
2. return False

acquire_write():
1. If write_locked == 0 and readers == 0:
   - write_locked = 1
   - return True
2. return False
"""

METHOD_SIGNATURE = "def acquire_read(self) -> bool"

STATE_VARIABLES = [
    StateVariable(
        name="readers",
        var_type="int",
        description="Number of active readers",
        bounds=(0, 10),
        initial_value=0
    ),
    StateVariable(
        name="write_locked",
        var_type="int",
        description="Whether write lock held (0 or 1)",
        bounds=(0, 1),
        initial_value=0
    ),
]

INPUT_VARIABLES = []

OUTPUT_TYPE = "bool"


def _prop_readers_non_negative(pre, post, inputs, output):
    """Readers must be non-negative."""
    return post["readers"] >= 0


def _prop_write_locked_valid(pre, post, inputs, output):
    """write_locked must be 0 or 1."""
    import z3
    return z3.And(post["write_locked"] >= 0, post["write_locked"] <= 1)


def _prop_mutual_exclusion(pre, post, inputs, output):
    """Cannot have readers and writer simultaneously."""
    import z3
    return z3.Implies(post["write_locked"] == 1, post["readers"] == 0)


PROPERTIES = [
    Property(
        name="readers_non_negative",
        description="Readers must be non-negative",
        formula="□(readers >= 0)",
        encode=_prop_readers_non_negative
    ),
    Property(
        name="write_locked_valid",
        description="write_locked must be 0 or 1",
        formula="□(0 <= write_locked <= 1)",
        encode=_prop_write_locked_valid
    ),
]


EXAMPLES = [
    Example(
        name="read_success",
        description="Acquire read when no writer",
        pre_state={"readers": 2, "write_locked": 0},
        inputs={},
        expected_output=True,
        expected_post_state={"readers": 3, "write_locked": 0}
    ),
    Example(
        name="read_blocked",
        description="Cannot read when write locked",
        pre_state={"readers": 0, "write_locked": 1},
        inputs={},
        expected_output=False,
        expected_post_state={"readers": 0, "write_locked": 1}
    ),
]


BUGGY_CODE = """
def acquire_read(self) -> bool:
    # BUG: Sets write_locked to 2 (invalid)
    self.write_locked = 2
    self.readers = self.readers + 1
    return True
"""

CORRECT_CODE = """
def acquire_read(self) -> bool:
    if self.write_locked == 0:
        self.readers = self.readers + 1
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
        tags=["coordination", "rwlock"]
    )
