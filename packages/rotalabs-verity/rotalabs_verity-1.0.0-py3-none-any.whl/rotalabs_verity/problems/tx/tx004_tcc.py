"""
TX-004: TCC Pattern

Try/Confirm/Cancel pattern.
"""

from rotalabs_verity.core import (
    Example,
    InputVariable,
    ProblemSpec,
    Property,
    StateVariable,
)

PROBLEM_ID = "TX-004"
NAME = "TCC Pattern"
CATEGORY = "transaction"
DIFFICULTY = "hard"

DESCRIPTION = """
Implement the TCC (Try/Confirm/Cancel) Pattern.

States: INIT=0, TRIED=1, CONFIRMED=2, CANCELLED=3

try_reserve(amount):
1. If state == INIT and available >= amount:
   - reserved = amount
   - available -= amount
   - state = TRIED
   - return True
2. return False

Only transition from INIT to TRIED if sufficient available.
"""

METHOD_SIGNATURE = "def try_reserve(self, amount: int) -> bool"

STATE_VARIABLES = [
    StateVariable(
        name="state",
        var_type="int",
        description="TCC state (0=INIT, 1=TRIED, 2=CONFIRMED, 3=CANCELLED)",
        bounds=(0, 3),
        initial_value=0
    ),
    StateVariable(
        name="available",
        var_type="int",
        description="Available resources",
        bounds=(0, 100),
        initial_value=100
    ),
    StateVariable(
        name="reserved",
        var_type="int",
        description="Reserved amount",
        bounds=(0, 100),
        initial_value=0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="amount",
        var_type="int",
        description="Amount to reserve",
        bounds=(1, 50)
    ),
]

OUTPUT_TYPE = "bool"


def _prop_state_valid(pre, post, inputs, output):
    """State must be valid."""
    import z3
    return z3.And(post["state"] >= 0, post["state"] <= 3)


def _prop_available_non_negative(pre, post, inputs, output):
    """Available must be non-negative."""
    return post["available"] >= 0


def _prop_reserved_non_negative(pre, post, inputs, output):
    """Reserved must be non-negative."""
    return post["reserved"] >= 0


PROPERTIES = [
    Property(
        name="state_valid",
        description="State must be valid (0-3)",
        formula="□(0 <= state <= 3)",
        encode=_prop_state_valid
    ),
    Property(
        name="available_non_negative",
        description="Available must be non-negative",
        formula="□(available >= 0)",
        encode=_prop_available_non_negative
    ),
]


EXAMPLES = [
    Example(
        name="try_success",
        description="Successful try",
        pre_state={"state": 0, "available": 100, "reserved": 0},
        inputs={"amount": 30},
        expected_output=True,
        expected_post_state={"state": 1, "available": 70, "reserved": 30}
    ),
    Example(
        name="try_insufficient",
        description="Try fails with insufficient resources",
        pre_state={"state": 0, "available": 20, "reserved": 0},
        inputs={"amount": 30},
        expected_output=False,
        expected_post_state={"state": 0, "available": 20, "reserved": 0}
    ),
]


BUGGY_CODE = """
def try_reserve(self, amount: int) -> bool:
    if self.state == 0:
        # BUG: No check for available >= amount
        self.reserved = amount
        self.available = self.available - amount
        self.state = 1
        return True
    return False
"""

CORRECT_CODE = """
def try_reserve(self, amount: int) -> bool:
    if self.state == 0:
        if self.available >= amount:
            self.reserved = amount
            self.available = self.available - amount
            self.state = 1
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
        tags=["transaction", "tcc"]
    )
