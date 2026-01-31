"""
TX-007: Compensating Transaction

Undo on failure.
"""

from rotalabs_verity.core import (
    Example,
    InputVariable,
    ProblemSpec,
    Property,
    StateVariable,
)

PROBLEM_ID = "TX-007"
NAME = "Compensating Transaction"
CATEGORY = "transaction"
DIFFICULTY = "medium"

DESCRIPTION = """
Implement Compensating Transaction.

execute(amount):
1. If balance + amount >= 0:
   - balance += amount
   - return True
2. return False

compensate(amount):
1. Reverse the effect: balance -= amount
2. return balance

Balance must stay non-negative after execute.
"""

METHOD_SIGNATURE = "def execute(self, amount: int) -> bool"

STATE_VARIABLES = [
    StateVariable(
        name="balance",
        var_type="int",
        description="Current balance",
        bounds=(0, 1000),
        initial_value=100
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="amount",
        var_type="int",
        description="Amount to add (can be negative)",
        bounds=(-100, 100)
    ),
]

OUTPUT_TYPE = "bool"


def _prop_balance_non_negative(pre, post, inputs, output):
    """Balance must be non-negative."""
    return post["balance"] >= 0


def _prop_balance_bounded(pre, post, inputs, output):
    """Balance must not exceed max."""
    return post["balance"] <= 1000


PROPERTIES = [
    Property(
        name="balance_non_negative",
        description="Balance must be non-negative",
        formula="□(balance >= 0)",
        encode=_prop_balance_non_negative
    ),
    Property(
        name="balance_bounded",
        description="Balance must not exceed max",
        formula="□(balance <= max)",
        encode=_prop_balance_bounded
    ),
]


EXAMPLES = [
    Example(
        name="execute_success",
        description="Successful execution",
        pre_state={"balance": 100},
        inputs={"amount": 50},
        expected_output=True,
        expected_post_state={"balance": 150}
    ),
    Example(
        name="execute_fail",
        description="Insufficient balance",
        pre_state={"balance": 50},
        inputs={"amount": -100},
        expected_output=False,
        expected_post_state={"balance": 50}
    ),
]


BUGGY_CODE = """
def execute(self, amount: int) -> bool:
    # BUG: No bounds check
    self.balance = self.balance + amount
    return True
"""

CORRECT_CODE = """
def execute(self, amount: int) -> bool:
    new_balance = self.balance + amount
    if new_balance >= 0:
        if new_balance <= 1000:
            self.balance = new_balance
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
        tags=["transaction", "compensating"]
    )
