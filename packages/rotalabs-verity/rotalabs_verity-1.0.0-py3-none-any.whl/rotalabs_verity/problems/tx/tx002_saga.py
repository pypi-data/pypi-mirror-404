"""
TX-002: Saga Orchestrator

Compensating transaction chain.
"""

from rotalabs_verity.core import (
    Example,
    InputVariable,
    ProblemSpec,
    Property,
    StateVariable,
)

PROBLEM_ID = "TX-002"
NAME = "Saga Orchestrator"
CATEGORY = "transaction"
DIFFICULTY = "hard"

DESCRIPTION = """
Implement a Saga Orchestrator.

Track steps completed and handle compensation on failure.

execute_step(success):
1. If compensating == 0 (forward mode):
   - If success:
     - steps_completed += 1
     - return steps_completed
   - Else:
     - compensating = 1
     - return -steps_completed
2. If compensating == 1 (compensating mode):
   - If steps_completed > 0:
     - steps_completed -= 1
   - return -steps_completed
"""

METHOD_SIGNATURE = "def execute_step(self, success: bool) -> int"

STATE_VARIABLES = [
    StateVariable(
        name="steps_completed",
        var_type="int",
        description="Number of steps completed",
        bounds=(0, 5),
        initial_value=0
    ),
    StateVariable(
        name="compensating",
        var_type="int",
        description="Whether in compensating mode (0 or 1)",
        bounds=(0, 1),
        initial_value=0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="success",
        var_type="bool",
        description="Whether step succeeded"
    ),
]

OUTPUT_TYPE = "int"


def _prop_steps_non_negative(pre, post, inputs, output):
    """Steps must be non-negative."""
    return post["steps_completed"] >= 0


def _prop_steps_bounded(pre, post, inputs, output):
    """Steps must not exceed max."""
    return post["steps_completed"] <= 5


def _prop_compensating_valid(pre, post, inputs, output):
    """compensating must be 0 or 1."""
    import z3
    return z3.And(post["compensating"] >= 0, post["compensating"] <= 1)


PROPERTIES = [
    Property(
        name="steps_non_negative",
        description="Steps must be non-negative",
        formula="□(steps_completed >= 0)",
        encode=_prop_steps_non_negative
    ),
    Property(
        name="steps_bounded",
        description="Steps must not exceed max",
        formula="□(steps_completed <= max_steps)",
        encode=_prop_steps_bounded
    ),
]


EXAMPLES = [
    Example(
        name="step_success",
        description="Successful step",
        pre_state={"steps_completed": 2, "compensating": 0},
        inputs={"success": True},
        expected_output=3,
        expected_post_state={"steps_completed": 3, "compensating": 0}
    ),
    Example(
        name="step_failure",
        description="Failed step triggers compensation",
        pre_state={"steps_completed": 2, "compensating": 0},
        inputs={"success": False},
        expected_output=-2,
        expected_post_state={"steps_completed": 2, "compensating": 1}
    ),
]


BUGGY_CODE = """
def execute_step(self, success: bool) -> int:
    if self.compensating == 0:
        if success:
            # BUG: No bound check
            self.steps_completed = self.steps_completed + 1
            return self.steps_completed
        else:
            self.compensating = 1
            return -self.steps_completed
    else:
        if self.steps_completed > 0:
            self.steps_completed = self.steps_completed - 1
        return -self.steps_completed
"""

CORRECT_CODE = """
def execute_step(self, success: bool) -> int:
    if self.compensating == 0:
        if success:
            if self.steps_completed < 5:
                self.steps_completed = self.steps_completed + 1
            return self.steps_completed
        else:
            self.compensating = 1
            return -self.steps_completed
    else:
        if self.steps_completed > 0:
            self.steps_completed = self.steps_completed - 1
        return -self.steps_completed
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
        tags=["transaction", "saga"]
    )
