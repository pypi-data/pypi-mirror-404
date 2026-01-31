"""
Shared test fixtures.
"""

import pytest
import z3
from rotalabs_verity.core import (
    ProblemSpec,
    StateVariable,
    InputVariable,
    Property,
    Example,
    Counterexample,
    PropertyViolation,
    VerificationResult,
    VerificationStatus,
)


@pytest.fixture
def simple_counter_spec():
    """Simple counter problem for testing."""
    return ProblemSpec(
        problem_id="TEST-001",
        name="Simple Counter",
        category="test",
        difficulty="easy",
        description="A counter that can be decremented but must stay non-negative.",
        method_signature="def decrement(self, amount: int) -> bool",
        state_variables=[
            StateVariable("count", "int", "Current count", bounds=(0, 100)),
        ],
        input_variables=[
            InputVariable("amount", "int", "Amount to decrement", bounds=(1, 10)),
        ],
        output_type="bool",
        properties=[
            Property(
                name="non_negative",
                description="Count must never go negative",
                formula="□(count >= 0)",
                encode=lambda pre, post, inp, out: post["count"] >= 0
            )
        ],
        examples=[
            Example(
                name="basic",
                description="Decrement when sufficient",
                pre_state={"count": 10},
                inputs={"amount": 3},
                expected_output=True,
                expected_post_state={"count": 7}
            )
        ],
        buggy_code='''
def decrement(self, amount: int) -> bool:
    self.count = self.count - amount
    return True
''',
        correct_code='''
def decrement(self, amount: int) -> bool:
    if self.count >= amount:
        self.count = self.count - amount
        return True
    return False
'''
    )


@pytest.fixture
def token_bucket_spec():
    """Token bucket problem for testing."""
    def prop_non_negative(pre, post, inp, out):
        return post["tokens"] >= 0

    return ProblemSpec(
        problem_id="RL-001",
        name="Token Bucket",
        category="rate_limiting",
        difficulty="medium",
        description="Token bucket rate limiter.",
        method_signature="def allow(self, timestamp: float) -> bool",
        state_variables=[
            StateVariable("tokens", "real", "Token count", bounds=(0, 100)),
            StateVariable("last_update", "real", "Last update time", bounds=(0, None)),
        ],
        input_variables=[
            InputVariable("timestamp", "real", "Request time", bounds=(0, None)),
        ],
        output_type="bool",
        properties=[
            Property(
                name="tokens_non_negative",
                description="Tokens must be non-negative",
                formula="□(tokens >= 0)",
                encode=prop_non_negative
            )
        ],
        examples=[],
        buggy_code='''
def allow(self, timestamp: float) -> bool:
    self.tokens = self.tokens - 1
    return True
''',
        correct_code='''
def allow(self, timestamp: float) -> bool:
    if self.tokens >= 1:
        self.tokens = self.tokens - 1
        return True
    return False
'''
    )


@pytest.fixture
def buggy_counter_result(simple_counter_spec):
    """Verification result for buggy counter."""
    return VerificationResult(
        status=VerificationStatus.COUNTEREXAMPLE,
        property_violated=PropertyViolation(
            property_name="non_negative",
            property_description="Count must never go negative",
            property_formula="□(count >= 0)"
        ),
        counterexample=Counterexample(
            pre_state={"count": 5},
            inputs={"amount": 10},
            post_state={"count": -5},
            output=True
        )
    )


class MockLLM:
    """Mock LLM for testing."""

    def __init__(self, responses: list[str]):
        self.responses = responses
        self.calls = []
        self._index = 0

    def generate(self, prompt: str, **kwargs):
        self.calls.append(prompt)
        response = self.responses[min(self._index, len(self.responses) - 1)]
        self._index += 1

        from rotalabs_verity.llm.client import LLMResponse
        return LLMResponse(
            content=response,
            model="mock",
            tokens_used=100,
            latency_ms=10.0
        )


@pytest.fixture
def mock_llm():
    """Factory for mock LLM."""
    def _create(responses):
        return MockLLM(responses)
    return _create
