"""
CN-009: Lease Manager

Time-bounded ownership.
"""

from rotalabs_verity.core import (
    Example,
    InputVariable,
    ProblemSpec,
    Property,
    StateVariable,
)

PROBLEM_ID = "CN-009"
NAME = "Lease Manager"
CATEGORY = "consensus"
DIFFICULTY = "medium"

DESCRIPTION = """
Implement Lease Manager.

acquire_lease(requestor, duration):
1. If lease_holder == 0 (no current holder):
   - lease_holder = requestor
   - lease_expiry = current_time + duration
   - return True
2. return False (lease held)

Time is simulated via current_time state.
"""

METHOD_SIGNATURE = "def acquire_lease(self, requestor: int, duration: int) -> bool"

STATE_VARIABLES = [
    StateVariable(
        name="lease_holder",
        var_type="int",
        description="Current lease holder (0 if none)",
        bounds=(0, 100),
        initial_value=0
    ),
    StateVariable(
        name="lease_expiry",
        var_type="int",
        description="When lease expires",
        bounds=(0, 1000),
        initial_value=0
    ),
    StateVariable(
        name="current_time",
        var_type="int",
        description="Current simulated time",
        bounds=(0, 1000),
        initial_value=0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="requestor",
        var_type="int",
        description="ID of requestor",
        bounds=(1, 100)
    ),
    InputVariable(
        name="duration",
        var_type="int",
        description="Requested lease duration",
        bounds=(1, 100)
    ),
]

OUTPUT_TYPE = "bool"


def _prop_holder_non_negative(pre, post, inputs, output):
    """lease_holder must be non-negative."""
    return post["lease_holder"] >= 0


def _prop_expiry_non_negative(pre, post, inputs, output):
    """lease_expiry must be non-negative."""
    return post["lease_expiry"] >= 0


PROPERTIES = [
    Property(
        name="holder_non_negative",
        description="lease_holder must be non-negative",
        formula="□(lease_holder >= 0)",
        encode=_prop_holder_non_negative
    ),
    Property(
        name="expiry_non_negative",
        description="lease_expiry must be non-negative",
        formula="□(lease_expiry >= 0)",
        encode=_prop_expiry_non_negative
    ),
]


EXAMPLES = [
    Example(
        name="acquire",
        description="Acquire lease",
        pre_state={"lease_holder": 0, "lease_expiry": 0, "current_time": 10},
        inputs={"requestor": 5, "duration": 30},
        expected_output=True,
        expected_post_state={"lease_holder": 5, "lease_expiry": 40, "current_time": 10}
    ),
]


BUGGY_CODE = """
def acquire_lease(self, requestor: int, duration: int) -> bool:
    if self.lease_holder == 0:
        # BUG: Sets lease_holder to -1
        self.lease_holder = -1
        self.lease_expiry = self.current_time + duration
        return True
    return False
"""

CORRECT_CODE = """
def acquire_lease(self, requestor: int, duration: int) -> bool:
    if self.lease_holder == 0:
        self.lease_holder = requestor
        self.lease_expiry = self.current_time + duration
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
        tags=["consensus", "lease"]
    )
