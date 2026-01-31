"""
TX-005: Idempotent Operation

An idempotent operation tracker that ensures operations are executed exactly once.
"""

import z3

from rotalabs_verity.core import (
    Example,
    InputVariable,
    ProblemSpec,
    Property,
    StateVariable,
)

# =============================================================================
# PROBLEM SPECIFICATION
# =============================================================================

PROBLEM_ID = "TX-005"
NAME = "Idempotent Operation"
CATEGORY = "transaction"
DIFFICULTY = "easy"

DESCRIPTION = """
Implement an Idempotent Operation Tracker.

Idempotency ensures that an operation is only executed once, even if called multiple
times with the same request ID. This is critical for financial transactions.

execute(request_id, amount):
1. If request_id == last_request_id: return last_result (duplicate)
2. Otherwise:
   - Update balance by amount
   - Store request_id as last_request_id
   - Store result
   - Return True if balance stays non-negative, False otherwise

Note: We simplify by only tracking the last request. Real systems use a database.
"""

METHOD_SIGNATURE = "def execute(self, request_id: int, amount: int) -> bool"

STATE_VARIABLES = [
    StateVariable(
        name="balance",
        var_type="int",
        description="Current balance",
        bounds=(0, 1000),
        initial_value=100
    ),
    StateVariable(
        name="last_request_id",
        var_type="int",
        description="Last processed request ID",
        bounds=(0, 1000),
        initial_value=0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="request_id",
        var_type="int",
        description="Unique request identifier",
        bounds=(1, 1000)
    ),
    InputVariable(
        name="amount",
        var_type="int",
        description="Amount to add (negative for subtract)",
        bounds=(-100, 100)
    ),
]

OUTPUT_TYPE = "bool"


# =============================================================================
# PROPERTIES
# =============================================================================

def _prop_balance_non_negative(pre, post, inputs, output):
    """Balance must never go negative."""
    return post["balance"] >= 0


def _prop_idempotent(pre, post, inputs, output):
    """Duplicate requests must not change balance."""
    is_duplicate = inputs["request_id"] == pre["last_request_id"]
    return z3.Implies(is_duplicate, post["balance"] == pre["balance"])



PROPERTIES = [
    Property(
        name="balance_non_negative",
        description="Balance must never go negative",
        formula="□(balance >= 0)",
        encode=_prop_balance_non_negative
    ),
    Property(
        name="idempotent",
        description="Duplicate requests must not change state",
        formula="□(duplicate → balance_unchanged)",
        encode=_prop_idempotent
    ),
]


# =============================================================================
# EXAMPLES
# =============================================================================

EXAMPLES = [
    Example(
        name="new_request",
        description="Process new request",
        pre_state={"balance": 100, "last_request_id": 0},
        inputs={"request_id": 1, "amount": -50},
        expected_output=True,
        expected_post_state={"balance": 50, "last_request_id": 1}
    ),
    Example(
        name="duplicate_request",
        description="Duplicate request returns same result without change",
        pre_state={"balance": 50, "last_request_id": 1},
        inputs={"request_id": 1, "amount": -50},
        expected_output=True,
        expected_post_state={"balance": 50, "last_request_id": 1}
    ),
]


# =============================================================================
# REFERENCE IMPLEMENTATIONS
# =============================================================================

BUGGY_CODE = """
def execute(self, request_id: int, amount: int) -> bool:
    # BUG: Doesn't check for duplicate, always processes
    self.balance = self.balance + amount
    self.last_request_id = request_id
    return True
"""

CORRECT_CODE = """
def execute(self, request_id: int, amount: int) -> bool:
    # Check for duplicate request
    if request_id == self.last_request_id:
        return True
    else:
        # Check if operation would succeed
        if self.balance + amount >= 0:
            self.balance = self.balance + amount
            self.last_request_id = request_id
            return True
        else:
            return False
"""


# =============================================================================
# BUILD SPEC
# =============================================================================

def get_spec() -> ProblemSpec:
    """Get the complete problem specification."""
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
        tags=["transaction", "idempotency", "exactly-once"]
    )
