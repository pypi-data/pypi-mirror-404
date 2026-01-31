"""
CO-007: Event Flag

Simple event signaling mechanism.
"""

from rotalabs_verity.core import (
    Example,
    ProblemSpec,
    Property,
    StateVariable,
)

PROBLEM_ID = "CO-007"
NAME = "Event Flag"
CATEGORY = "coordination"
DIFFICULTY = "easy"

DESCRIPTION = """
Implement Event Flag for signaling.

set_event():
1. If flag == 0:
   - flag = 1
   - waiters_notified = waiting_count
   - return True
2. return False (already set)

clear_event():
1. flag = 0
2. return True
"""

METHOD_SIGNATURE = "def set_event(self) -> bool"

STATE_VARIABLES = [
    StateVariable(
        name="flag",
        var_type="int",
        description="Event flag (0=clear, 1=set)",
        bounds=(0, 1),
        initial_value=0
    ),
    StateVariable(
        name="waiting_count",
        var_type="int",
        description="Number of waiters",
        bounds=(0, 10),
        initial_value=0
    ),
    StateVariable(
        name="waiters_notified",
        var_type="int",
        description="Waiters notified on last set",
        bounds=(0, 10),
        initial_value=0
    ),
]

INPUT_VARIABLES = []

OUTPUT_TYPE = "bool"


def _prop_flag_valid(pre, post, inputs, output):
    """flag must be 0 or 1."""
    import z3
    return z3.And(post["flag"] >= 0, post["flag"] <= 1)


def _prop_waiters_non_negative(pre, post, inputs, output):
    """waiters_notified must be non-negative."""
    return post["waiters_notified"] >= 0


PROPERTIES = [
    Property(
        name="flag_valid",
        description="flag must be 0 or 1",
        formula="□(0 <= flag <= 1)",
        encode=_prop_flag_valid
    ),
    Property(
        name="waiters_non_negative",
        description="waiters_notified must be non-negative",
        formula="□(waiters_notified >= 0)",
        encode=_prop_waiters_non_negative
    ),
]


EXAMPLES = [
    Example(
        name="set_flag",
        description="Set the event flag",
        pre_state={"flag": 0, "waiting_count": 3, "waiters_notified": 0},
        inputs={},
        expected_output=True,
        expected_post_state={"flag": 1, "waiting_count": 3, "waiters_notified": 3}
    ),
]


BUGGY_CODE = """
def set_event(self) -> bool:
    if self.flag == 0:
        # BUG: Sets flag to invalid value
        self.flag = 2
        self.waiters_notified = self.waiting_count
        return True
    return False
"""

CORRECT_CODE = """
def set_event(self) -> bool:
    if self.flag == 0:
        self.flag = 1
        self.waiters_notified = self.waiting_count
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
        tags=["coordination", "event-flag"]
    )
