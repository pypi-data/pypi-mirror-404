"""
CB-002: Bulkhead

Isolates failures to partitions to prevent cascading failures.
"""

from rotalabs_verity.core import (
    Example,
    ProblemSpec,
    Property,
    StateVariable,
)

# =============================================================================
# PROBLEM SPECIFICATION
# =============================================================================

PROBLEM_ID = "CB-002"
NAME = "Bulkhead"
CATEGORY = "circuit_breaker"
DIFFICULTY = "medium"

DESCRIPTION = """
Implement a Bulkhead pattern.

A bulkhead isolates failures by partitioning resources. Each partition has
its own limit of concurrent executions.

try_acquire(partition):
1. If partition_count[partition] < max_per_partition:
   - partition_count[partition] += 1
   - return True
2. return False

For simplicity, we model a single partition with a count.

Constants: max_per_partition = 5
"""

METHOD_SIGNATURE = "def try_acquire(self) -> bool"

STATE_VARIABLES = [
    StateVariable(
        name="partition_count",
        var_type="int",
        description="Active requests in partition",
        bounds=(0, 5),
        initial_value=0
    ),
]

INPUT_VARIABLES = []

OUTPUT_TYPE = "bool"


# =============================================================================
# PROPERTIES
# =============================================================================

def _prop_count_non_negative(pre, post, inputs, output):
    """Partition count must never go negative."""
    return post["partition_count"] >= 0


def _prop_count_bounded(pre, post, inputs, output):
    """Partition count must not exceed max_per_partition."""
    return post["partition_count"] <= 5


PROPERTIES = [
    Property(
        name="count_non_negative",
        description="Partition count must never go negative",
        formula="□(partition_count >= 0)",
        encode=_prop_count_non_negative
    ),
    Property(
        name="count_bounded",
        description="Partition count must not exceed limit",
        formula="□(partition_count <= max_per_partition)",
        encode=_prop_count_bounded
    ),
]


# =============================================================================
# EXAMPLES
# =============================================================================

EXAMPLES = [
    Example(
        name="acquire_success",
        description="Acquire when under limit",
        pre_state={"partition_count": 3},
        inputs={},
        expected_output=True,
        expected_post_state={"partition_count": 4}
    ),
    Example(
        name="acquire_fail",
        description="Deny when at limit",
        pre_state={"partition_count": 5},
        inputs={},
        expected_output=False,
        expected_post_state={"partition_count": 5}
    ),
]


# =============================================================================
# REFERENCE IMPLEMENTATIONS
# =============================================================================

BUGGY_CODE = """
def try_acquire(self) -> bool:
    # BUG: Uses <= instead of <, allows one over limit
    if self.partition_count <= 5:
        self.partition_count = self.partition_count + 1
        return True
    return False
"""

CORRECT_CODE = """
def try_acquire(self) -> bool:
    if self.partition_count < 5:
        self.partition_count = self.partition_count + 1
        return True
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
        tags=["circuit-breaker", "bulkhead", "isolation"]
    )
