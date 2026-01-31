"""
TX-006: Write-Ahead Log

Log before apply pattern.
"""

from rotalabs_verity.core import (
    Example,
    ProblemSpec,
    Property,
    StateVariable,
)

PROBLEM_ID = "TX-006"
NAME = "Write-Ahead Log"
CATEGORY = "transaction"
DIFFICULTY = "medium"

DESCRIPTION = """
Implement Write-Ahead Log.

append_log():
1. If log_size < max_log:
   - log_size += 1
   - return log_size (new LSN)
2. return -1 (log full)

apply_log():
1. If applied < log_size:
   - applied += 1
   - return True
2. return False

Constants: max_log = 100
"""

METHOD_SIGNATURE = "def append_log(self) -> int"

STATE_VARIABLES = [
    StateVariable(
        name="log_size",
        var_type="int",
        description="Number of log entries",
        bounds=(0, 100),
        initial_value=0
    ),
    StateVariable(
        name="applied",
        var_type="int",
        description="Number of applied entries",
        bounds=(0, 100),
        initial_value=0
    ),
]

INPUT_VARIABLES = []

OUTPUT_TYPE = "int"


def _prop_log_non_negative(pre, post, inputs, output):
    """Log size must be non-negative."""
    return post["log_size"] >= 0


def _prop_log_bounded(pre, post, inputs, output):
    """Log size must not exceed max."""
    return post["log_size"] <= 100


def _prop_applied_bounded(pre, post, inputs, output):
    """Applied must not exceed log_size."""
    return post["applied"] <= post["log_size"]


PROPERTIES = [
    Property(
        name="log_non_negative",
        description="Log size must be non-negative",
        formula="□(log_size >= 0)",
        encode=_prop_log_non_negative
    ),
    Property(
        name="log_bounded",
        description="Log size must not exceed max",
        formula="□(log_size <= max_log)",
        encode=_prop_log_bounded
    ),
]


EXAMPLES = [
    Example(
        name="append_success",
        description="Append to log",
        pre_state={"log_size": 5, "applied": 3},
        inputs={},
        expected_output=6,
        expected_post_state={"log_size": 6, "applied": 3}
    ),
    Example(
        name="append_full",
        description="Cannot append when full",
        pre_state={"log_size": 100, "applied": 50},
        inputs={},
        expected_output=-1,
        expected_post_state={"log_size": 100, "applied": 50}
    ),
]


BUGGY_CODE = """
def append_log(self) -> int:
    # BUG: No check for max
    self.log_size = self.log_size + 1
    return self.log_size
"""

CORRECT_CODE = """
def append_log(self) -> int:
    if self.log_size < 100:
        self.log_size = self.log_size + 1
        return self.log_size
    return -1
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
        tags=["transaction", "wal"]
    )
