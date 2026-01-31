"""
CO-008: Future/Promise

Async result container.
"""

from rotalabs_verity.core import (
    Example,
    InputVariable,
    ProblemSpec,
    Property,
    StateVariable,
)

PROBLEM_ID = "CO-008"
NAME = "Future/Promise"
CATEGORY = "coordination"
DIFFICULTY = "medium"

DESCRIPTION = """
Implement a Future/Promise for async results.

complete(value):
1. If completed == 0:
   - result = value
   - completed = 1
   - return True
2. return False (already completed)

Only first completion succeeds.
"""

METHOD_SIGNATURE = "def complete(self, value: int) -> bool"

STATE_VARIABLES = [
    StateVariable(
        name="completed",
        var_type="int",
        description="Whether future is completed (0 or 1)",
        bounds=(0, 1),
        initial_value=0
    ),
    StateVariable(
        name="result",
        var_type="int",
        description="The result value",
        bounds=(0, 1000),
        initial_value=0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="value",
        var_type="int",
        description="Value to complete with",
        bounds=(1, 1000)
    ),
]

OUTPUT_TYPE = "bool"


def _prop_completed_valid(pre, post, inputs, output):
    """completed must be 0 or 1."""
    import z3
    return z3.And(post["completed"] >= 0, post["completed"] <= 1)


def _prop_completed_monotonic(pre, post, inputs, output):
    """Once completed, stays completed."""
    import z3
    return z3.Implies(pre["completed"] == 1, post["completed"] == 1)


PROPERTIES = [
    Property(
        name="completed_valid",
        description="completed must be 0 or 1",
        formula="□(0 <= completed <= 1)",
        encode=_prop_completed_valid
    ),
    Property(
        name="completed_monotonic",
        description="Once completed, stays completed",
        formula="□(completed → completed')",
        encode=_prop_completed_monotonic
    ),
]


EXAMPLES = [
    Example(
        name="first_complete",
        description="First completion succeeds",
        pre_state={"completed": 0, "result": 0},
        inputs={"value": 42},
        expected_output=True,
        expected_post_state={"completed": 1, "result": 42}
    ),
    Example(
        name="already_complete",
        description="Second completion fails",
        pre_state={"completed": 1, "result": 42},
        inputs={"value": 100},
        expected_output=False,
        expected_post_state={"completed": 1, "result": 42}
    ),
]


BUGGY_CODE = """
def complete(self, value: int) -> bool:
    # BUG: Sets completed to 2 (invalid)
    self.result = value
    self.completed = 2
    return True
"""

CORRECT_CODE = """
def complete(self, value: int) -> bool:
    if self.completed == 0:
        self.result = value
        self.completed = 1
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
        tags=["coordination", "future", "promise"]
    )
