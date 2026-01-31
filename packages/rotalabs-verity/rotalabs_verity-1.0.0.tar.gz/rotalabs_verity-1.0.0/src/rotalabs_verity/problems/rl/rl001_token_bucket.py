"""
RL-001: Token Bucket Rate Limiter

A rate limiter using the token bucket algorithm.
"""

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

PROBLEM_ID = "RL-001"
NAME = "Token Bucket Rate Limiter"
CATEGORY = "rate_limiting"
DIFFICULTY = "medium"

DESCRIPTION = """
Implement a Token Bucket Rate Limiter.

The token bucket algorithm controls request rate by maintaining a bucket of tokens.
Each request consumes one token. Tokens are replenished at a fixed rate up to capacity.

When a request arrives:
1. Calculate elapsed time since last update
2. Add tokens: tokens += elapsed * rate
3. Cap at capacity: tokens = min(tokens, capacity)
4. Update last_update timestamp
5. If tokens >= 1: consume one token, allow request
6. Otherwise: deny request

Constants available: self.rate (tokens/second), self.capacity (max tokens)
For this problem, assume rate = 10.0 and capacity = 100.0
"""

METHOD_SIGNATURE = "def allow(self, timestamp: float) -> bool"

STATE_VARIABLES = [
    StateVariable(
        name="tokens",
        var_type="real",
        description="Current number of tokens in bucket",
        bounds=(0.0, 100.0),
        initial_value=100.0
    ),
    StateVariable(
        name="last_update",
        var_type="real",
        description="Timestamp of last token update",
        bounds=(0.0, 1000.0),
        initial_value=0.0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="timestamp",
        var_type="real",
        description="Current request timestamp",
        bounds=(0.0, 1000.0)
    ),
]

OUTPUT_TYPE = "bool"


# =============================================================================
# PROPERTIES
# =============================================================================

def _prop_tokens_non_negative(pre, post, inputs, output):
    """Tokens must never go negative."""
    return post["tokens"] >= 0


def _prop_tokens_bounded(pre, post, inputs, output):
    """Tokens must not exceed capacity (capacity=100)."""
    return post["tokens"] <= 100


PROPERTIES = [
    Property(
        name="tokens_non_negative",
        description="Token count must never go negative",
        formula="□(tokens >= 0)",
        encode=_prop_tokens_non_negative
    ),
    Property(
        name="tokens_bounded",
        description="Token count must not exceed capacity",
        formula="□(tokens <= capacity)",
        encode=_prop_tokens_bounded
    ),
]


# =============================================================================
# EXAMPLES
# =============================================================================

EXAMPLES = [
    Example(
        name="basic_allow",
        description="Allow request when tokens available",
        pre_state={"tokens": 10.0, "last_update": 0.0},
        inputs={"timestamp": 0.0},
        expected_output=True,
        expected_post_state={"tokens": 9.0, "last_update": 0.0}
    ),
    Example(
        name="basic_deny",
        description="Deny request when insufficient tokens",
        pre_state={"tokens": 0.5, "last_update": 0.0},
        inputs={"timestamp": 0.0},
        expected_output=False,
        expected_post_state={"tokens": 0.5, "last_update": 0.0}
    ),
]


# =============================================================================
# REFERENCE IMPLEMENTATIONS
# =============================================================================

BUGGY_CODE = """
def allow(self, timestamp: float) -> bool:
    elapsed = timestamp - self.last_update
    self.tokens = self.tokens + elapsed * 10
    self.tokens = min(self.tokens, 100)
    self.last_update = timestamp
    # BUG: Always consumes and allows, even when tokens < 1
    self.tokens = self.tokens - 1
    return True
"""

CORRECT_CODE = """
def allow(self, timestamp: float) -> bool:
    elapsed = timestamp - self.last_update
    if elapsed > 0:
        self.tokens = self.tokens + elapsed * 10
        self.tokens = min(self.tokens, 100)
        self.last_update = timestamp
    if self.tokens >= 1:
        self.tokens = self.tokens - 1
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
        tags=["rate-limiting", "token-bucket", "real-time"]
    )
