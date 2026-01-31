"""
CO-001: Distributed Lock

Mutual exclusion with lock/unlock operations.
"""

from rotalabs_verity.core import (
    Example,
    InputVariable,
    ProblemSpec,
    Property,
    StateVariable,
)

PROBLEM_ID = "CO-001"
NAME = "Distributed Lock"
CATEGORY = "coordination"
DIFFICULTY = "medium"

DESCRIPTION = """
Implement a Distributed Lock.

try_acquire(owner_id):
1. If locked == 0:
   - locked = 1
   - lock_owner = owner_id
   - return True
2. return False

release(owner_id):
1. If locked == 1 and lock_owner == owner_id:
   - locked = 0
   - lock_owner = 0
   - return True
2. return False
"""

METHOD_SIGNATURE = "def try_acquire(self, owner_id: int) -> bool"

STATE_VARIABLES = [
    StateVariable(
        name="locked",
        var_type="int",
        description="Whether lock is held (0 or 1)",
        bounds=(0, 1),
        initial_value=0
    ),
    StateVariable(
        name="lock_owner",
        var_type="int",
        description="ID of lock owner (0 if unlocked)",
        bounds=(0, 100),
        initial_value=0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="owner_id",
        var_type="int",
        description="ID of requesting owner",
        bounds=(1, 100)
    ),
]

OUTPUT_TYPE = "bool"


def _prop_locked_valid(pre, post, inputs, output):
    """locked must be 0 or 1."""
    import z3
    return z3.And(post["locked"] >= 0, post["locked"] <= 1)


def _prop_owner_non_negative(pre, post, inputs, output):
    """Lock owner must be non-negative."""
    return post["lock_owner"] >= 0


PROPERTIES = [
    Property(
        name="locked_valid",
        description="locked must be 0 or 1",
        formula="□(0 <= locked <= 1)",
        encode=_prop_locked_valid
    ),
    Property(
        name="owner_non_negative",
        description="Lock owner must be non-negative",
        formula="□(lock_owner >= 0)",
        encode=_prop_owner_non_negative
    ),
]


EXAMPLES = [
    Example(
        name="acquire_free",
        description="Acquire free lock",
        pre_state={"locked": 0, "lock_owner": 0},
        inputs={"owner_id": 5},
        expected_output=True,
        expected_post_state={"locked": 1, "lock_owner": 5}
    ),
    Example(
        name="acquire_held",
        description="Cannot acquire held lock",
        pre_state={"locked": 1, "lock_owner": 3},
        inputs={"owner_id": 5},
        expected_output=False,
        expected_post_state={"locked": 1, "lock_owner": 3}
    ),
]


BUGGY_CODE = """
def try_acquire(self, owner_id: int) -> bool:
    # BUG: Sets locked to 2 (invalid)
    self.locked = 2
    self.lock_owner = owner_id
    return True
"""

CORRECT_CODE = """
def try_acquire(self, owner_id: int) -> bool:
    if self.locked == 0:
        self.locked = 1
        self.lock_owner = owner_id
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
        tags=["coordination", "lock", "mutex"]
    )
