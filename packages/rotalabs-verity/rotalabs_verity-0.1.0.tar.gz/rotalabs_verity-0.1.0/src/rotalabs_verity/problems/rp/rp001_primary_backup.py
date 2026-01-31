"""
RP-001: Primary-Backup

Simple replication with primary and backup.
"""

from rotalabs_verity.core import (
    Example,
    InputVariable,
    ProblemSpec,
    Property,
    StateVariable,
)

PROBLEM_ID = "RP-001"
NAME = "Primary-Backup"
CATEGORY = "replication"
DIFFICULTY = "medium"

DESCRIPTION = """
Implement Primary-Backup replication.

replicate(value):
1. If is_primary == 1:
   - primary_value = value
   - backup_value = value
   - sync_count = sync_count + 1
   - return True
2. return False (not primary)
"""

METHOD_SIGNATURE = "def replicate(self, value: int) -> bool"

STATE_VARIABLES = [
    StateVariable(
        name="is_primary",
        var_type="int",
        description="Whether this is primary (0 or 1)",
        bounds=(0, 1),
        initial_value=1
    ),
    StateVariable(
        name="primary_value",
        var_type="int",
        description="Value on primary",
        bounds=(0, 1000),
        initial_value=0
    ),
    StateVariable(
        name="backup_value",
        var_type="int",
        description="Value on backup",
        bounds=(0, 1000),
        initial_value=0
    ),
    StateVariable(
        name="sync_count",
        var_type="int",
        description="Number of syncs performed",
        bounds=(0, 100),
        initial_value=0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="value",
        var_type="int",
        description="Value to replicate",
        bounds=(1, 1000)
    ),
]

OUTPUT_TYPE = "bool"


def _prop_sync_after_write(pre, post, inputs, output):
    """After write, primary and backup must match."""
    import z3
    return z3.Implies(
        z3.And(pre["is_primary"] == 1, output),
        post["primary_value"] == post["backup_value"]
    )


def _prop_sync_count_non_negative(pre, post, inputs, output):
    """sync_count must be non-negative."""
    return post["sync_count"] >= 0


PROPERTIES = [
    Property(
        name="sync_after_write",
        description="After write, primary and backup must match",
        formula="□(is_primary ∧ write → primary_value' = backup_value')",
        encode=_prop_sync_after_write
    ),
    Property(
        name="sync_count_non_negative",
        description="sync_count must be non-negative",
        formula="□(sync_count >= 0)",
        encode=_prop_sync_count_non_negative
    ),
]


EXAMPLES = [
    Example(
        name="replicate",
        description="Replicate value to backup",
        pre_state={"is_primary": 1, "primary_value": 0, "backup_value": 0, "sync_count": 0},
        inputs={"value": 42},
        expected_output=True,
        expected_post_state={"is_primary": 1, "primary_value": 42, "backup_value": 42, "sync_count": 1}
    ),
]


BUGGY_CODE = """
def replicate(self, value: int) -> bool:
    if self.is_primary == 1:
        self.primary_value = value
        # BUG: Doesn't sync to backup
        self.sync_count = self.sync_count + 1
        return True
    return False
"""

CORRECT_CODE = """
def replicate(self, value: int) -> bool:
    if self.is_primary == 1:
        self.primary_value = value
        self.backup_value = value
        self.sync_count = self.sync_count + 1
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
        tags=["replication", "primary-backup"]
    )
