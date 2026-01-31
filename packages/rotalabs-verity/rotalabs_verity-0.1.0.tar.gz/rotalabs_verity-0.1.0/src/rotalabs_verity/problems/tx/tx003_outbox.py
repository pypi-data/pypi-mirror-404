"""
TX-003: Outbox Pattern

Reliable event publishing with outbox.
"""

from rotalabs_verity.core import (
    Example,
    ProblemSpec,
    Property,
    StateVariable,
)

PROBLEM_ID = "TX-003"
NAME = "Outbox Pattern"
CATEGORY = "transaction"
DIFFICULTY = "medium"

DESCRIPTION = """
Implement the Outbox Pattern for reliable event publishing.

add_to_outbox():
1. If outbox_count < max_outbox:
   - outbox_count += 1
   - return True
2. return False

process_outbox():
1. If outbox_count > 0:
   - outbox_count -= 1
   - published += 1
   - return True
2. return False

Constants: max_outbox = 10
"""

METHOD_SIGNATURE = "def add_to_outbox(self) -> bool"

STATE_VARIABLES = [
    StateVariable(
        name="outbox_count",
        var_type="int",
        description="Events in outbox",
        bounds=(0, 10),
        initial_value=0
    ),
    StateVariable(
        name="published",
        var_type="int",
        description="Events published",
        bounds=(0, 100),
        initial_value=0
    ),
]

INPUT_VARIABLES = []

OUTPUT_TYPE = "bool"


def _prop_outbox_non_negative(pre, post, inputs, output):
    """Outbox count must be non-negative."""
    return post["outbox_count"] >= 0


def _prop_outbox_bounded(pre, post, inputs, output):
    """Outbox count must not exceed max."""
    return post["outbox_count"] <= 10


PROPERTIES = [
    Property(
        name="outbox_non_negative",
        description="Outbox count must be non-negative",
        formula="□(outbox_count >= 0)",
        encode=_prop_outbox_non_negative
    ),
    Property(
        name="outbox_bounded",
        description="Outbox count must not exceed max",
        formula="□(outbox_count <= max_outbox)",
        encode=_prop_outbox_bounded
    ),
]


EXAMPLES = [
    Example(
        name="add_success",
        description="Add to outbox",
        pre_state={"outbox_count": 5, "published": 10},
        inputs={},
        expected_output=True,
        expected_post_state={"outbox_count": 6, "published": 10}
    ),
    Example(
        name="add_full",
        description="Cannot add when full",
        pre_state={"outbox_count": 10, "published": 10},
        inputs={},
        expected_output=False,
        expected_post_state={"outbox_count": 10, "published": 10}
    ),
]


BUGGY_CODE = """
def add_to_outbox(self) -> bool:
    # BUG: No check for max
    self.outbox_count = self.outbox_count + 1
    return True
"""

CORRECT_CODE = """
def add_to_outbox(self) -> bool:
    if self.outbox_count < 10:
        self.outbox_count = self.outbox_count + 1
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
        tags=["transaction", "outbox"]
    )
