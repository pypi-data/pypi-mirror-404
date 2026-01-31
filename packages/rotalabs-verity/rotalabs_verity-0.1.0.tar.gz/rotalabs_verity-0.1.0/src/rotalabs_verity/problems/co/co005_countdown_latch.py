"""
CO-005: CountDownLatch

One-time barrier that counts down.
"""

from rotalabs_verity.core import (
    Example,
    ProblemSpec,
    Property,
    StateVariable,
)

PROBLEM_ID = "CO-005"
NAME = "CountDownLatch"
CATEGORY = "coordination"
DIFFICULTY = "easy"

DESCRIPTION = """
Implement a CountDownLatch.

count_down():
1. If count > 0:
   - count -= 1
   - return count == 0 (True if released)
2. return True (already released)

Constants: initial count = 3
"""

METHOD_SIGNATURE = "def count_down(self) -> bool"

STATE_VARIABLES = [
    StateVariable(
        name="count",
        var_type="int",
        description="Remaining count",
        bounds=(0, 10),
        initial_value=3
    ),
]

INPUT_VARIABLES = []

OUTPUT_TYPE = "bool"


def _prop_count_non_negative(pre, post, inputs, output):
    """count must be non-negative."""
    return post["count"] >= 0


PROPERTIES = [
    Property(
        name="count_non_negative",
        description="count must be non-negative",
        formula="□(count >= 0)",
        encode=_prop_count_non_negative
    ),
]


EXAMPLES = [
    Example(
        name="count_down_waiting",
        description="Count down but not released",
        pre_state={"count": 3},
        inputs={},
        expected_output=False,
        expected_post_state={"count": 2}
    ),
    Example(
        name="count_down_released",
        description="Final count releases latch",
        pre_state={"count": 1},
        inputs={},
        expected_output=True,
        expected_post_state={"count": 0}
    ),
]


BUGGY_CODE = """
def count_down(self) -> bool:
    # BUG: No check for count > 0, goes negative
    self.count = self.count - 1
    if self.count == 0:
        return True
    return False
"""

CORRECT_CODE = """
def count_down(self) -> bool:
    if self.count > 0:
        self.count = self.count - 1
        if self.count == 0:
            return True
        return False
    return True
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
        tags=["coordination", "latch"]
    )
