"""
TX-008: Event Sourcing

State from event replay.
"""

from rotalabs_verity.core import (
    Example,
    InputVariable,
    ProblemSpec,
    Property,
    StateVariable,
)

PROBLEM_ID = "TX-008"
NAME = "Event Sourcing"
CATEGORY = "transaction"
DIFFICULTY = "hard"

DESCRIPTION = """
Implement Event Sourcing.

apply_event(event_type, amount):
1. event_type: 1=deposit, 2=withdraw
2. If event_type == 1:
   - balance += amount
   - events += 1
3. If event_type == 2 and balance >= amount:
   - balance -= amount
   - events += 1
   - return True
4. return event_type == 1

Events are immutable - state derived from replaying events.
"""

METHOD_SIGNATURE = "def apply_event(self, event_type: int, amount: int) -> bool"

STATE_VARIABLES = [
    StateVariable(
        name="balance",
        var_type="int",
        description="Derived balance",
        bounds=(0, 1000),
        initial_value=0
    ),
    StateVariable(
        name="events",
        var_type="int",
        description="Number of events",
        bounds=(0, 100),
        initial_value=0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="event_type",
        var_type="int",
        description="Event type (1=deposit, 2=withdraw)",
        bounds=(1, 2)
    ),
    InputVariable(
        name="amount",
        var_type="int",
        description="Event amount",
        bounds=(1, 100)
    ),
]

OUTPUT_TYPE = "bool"


def _prop_balance_non_negative(pre, post, inputs, output):
    """Balance must be non-negative."""
    return post["balance"] >= 0


def _prop_events_non_negative(pre, post, inputs, output):
    """Events must be non-negative."""
    return post["events"] >= 0


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
        name="deposit",
        description="Apply deposit event",
        pre_state={"balance": 100, "events": 5},
        inputs={"event_type": 1, "amount": 50},
        expected_output=True,
        expected_post_state={"balance": 150, "events": 6}
    ),
    Example(
        name="withdraw_insufficient",
        description="Cannot withdraw more than balance",
        pre_state={"balance": 30, "events": 5},
        inputs={"event_type": 2, "amount": 50},
        expected_output=False,
        expected_post_state={"balance": 30, "events": 5}
    ),
]


BUGGY_CODE = """
def apply_event(self, event_type: int, amount: int) -> bool:
    if event_type == 1:
        # BUG: No upper bound check
        self.balance = self.balance + amount
        self.events = self.events + 1
        return True
    else:
        if self.balance >= amount:
            self.balance = self.balance - amount
            self.events = self.events + 1
            return True
    return False
"""

CORRECT_CODE = """
def apply_event(self, event_type: int, amount: int) -> bool:
    if event_type == 1:
        new_balance = self.balance + amount
        if new_balance <= 1000:
            self.balance = new_balance
            self.events = self.events + 1
            return True
        return False
    else:
        if self.balance >= amount:
            self.balance = self.balance - amount
            self.events = self.events + 1
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
        tags=["transaction", "event-sourcing"]
    )
