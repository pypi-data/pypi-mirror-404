"""Tests for verifier."""

import pytest
from rotalabs_verity.verifier import verify
from rotalabs_verity.core import (
    ProblemSpec,
    StateVariable,
    InputVariable,
    Property,
    VerificationStatus,
)


@pytest.fixture
def simple_counter_spec():
    """Simple counter specification."""
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
    """Token bucket rate limiter specification."""
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
                encode=lambda pre, post, inp, out: post["tokens"] >= 0
            )
        ],
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


class TestVerifier:
    def test_correct_code_verifies(self, simple_counter_spec):
        """Correct code should verify."""
        result = verify(simple_counter_spec.correct_code, simple_counter_spec)

        assert result.status == VerificationStatus.VERIFIED
        assert result.counterexample is None
        assert result.property_violated is None

    def test_buggy_code_counterexample(self, simple_counter_spec):
        """Buggy code should produce counterexample."""
        result = verify(simple_counter_spec.buggy_code, simple_counter_spec)

        assert result.status == VerificationStatus.COUNTEREXAMPLE
        assert result.property_violated is not None
        assert result.property_violated.property_name == "non_negative"
        assert result.counterexample is not None
        assert result.counterexample.post_state["count"] < 0

    def test_counterexample_has_valid_structure(self, simple_counter_spec):
        """Counterexample should have all required fields."""
        result = verify(simple_counter_spec.buggy_code, simple_counter_spec)

        cx = result.counterexample
        assert "count" in cx.pre_state
        assert "count" in cx.post_state
        assert "amount" in cx.inputs
        assert cx.output is not None

    def test_parse_error(self, simple_counter_spec):
        """Invalid syntax should return parse error."""
        result = verify("def broken(", simple_counter_spec)

        assert result.status == VerificationStatus.PARSE_ERROR
        assert result.error_message is not None

    def test_encoding_error(self, simple_counter_spec):
        """Unsupported code should return encoding error."""
        code = '''
def decrement(self, amount: int) -> bool:
    x = [1, 2, 3]
    return True
'''
        result = verify(code, simple_counter_spec)

        assert result.status in (VerificationStatus.ENCODING_ERROR, VerificationStatus.PARSE_ERROR)
        assert result.error_message is not None

    def test_token_bucket_buggy(self, token_bucket_spec):
        """Buggy token bucket should produce counterexample."""
        result = verify(token_bucket_spec.buggy_code, token_bucket_spec)

        assert result.status == VerificationStatus.COUNTEREXAMPLE
        assert result.counterexample is not None

        # The counterexample should show tokens going negative
        cx = result.counterexample
        assert cx.post_state["tokens"] < 0

    def test_token_bucket_correct(self, token_bucket_spec):
        """Correct token bucket should verify."""
        result = verify(token_bucket_spec.correct_code, token_bucket_spec)

        assert result.status == VerificationStatus.VERIFIED

    def test_multiple_properties(self):
        """Test with multiple properties."""
        spec = ProblemSpec(
            problem_id="TEST-002",
            name="Multi Property",
            category="test",
            difficulty="easy",
            description="Test with multiple properties",
            method_signature="def update(self, x: int) -> bool",
            state_variables=[
                StateVariable("value", "int", "Value", bounds=(0, 100)),
            ],
            input_variables=[
                InputVariable("x", "int", "Input", bounds=(0, 50)),
            ],
            output_type="bool",
            properties=[
                Property(
                    name="non_negative",
                    description="Value must be non-negative",
                    formula="□(value >= 0)",
                    encode=lambda pre, post, inp, out: post["value"] >= 0
                ),
                Property(
                    name="bounded",
                    description="Value must not exceed 100",
                    formula="□(value <= 100)",
                    encode=lambda pre, post, inp, out: post["value"] <= 100
                ),
            ]
        )

        # Code that satisfies both properties
        good_code = '''
def update(self, x: int) -> bool:
    self.value = min(self.value + x, 100)
    return True
'''
        result = verify(good_code, spec)
        assert result.status == VerificationStatus.VERIFIED

        # Code that violates bounded property
        bad_code = '''
def update(self, x: int) -> bool:
    self.value = self.value + x
    return True
'''
        result = verify(bad_code, spec)
        assert result.status == VerificationStatus.COUNTEREXAMPLE
        assert result.property_violated.property_name == "bounded"

    def test_verification_time_recorded(self, simple_counter_spec):
        """Verification time should be recorded."""
        result = verify(simple_counter_spec.correct_code, simple_counter_spec)

        assert result.verification_time_ms > 0


class TestCounterexampleExtraction:
    def test_integer_values(self, simple_counter_spec):
        """Counterexample should have integer values for int variables."""
        result = verify(simple_counter_spec.buggy_code, simple_counter_spec)

        cx = result.counterexample
        assert isinstance(cx.pre_state["count"], int)
        assert isinstance(cx.inputs["amount"], int)
        assert isinstance(cx.post_state["count"], int)

    def test_real_values(self, token_bucket_spec):
        """Counterexample should have float values for real variables."""
        result = verify(token_bucket_spec.buggy_code, token_bucket_spec)

        cx = result.counterexample
        assert isinstance(cx.pre_state["tokens"], float)
        assert isinstance(cx.inputs["timestamp"], float)
        assert isinstance(cx.post_state["tokens"], float)

    def test_boolean_output(self, simple_counter_spec):
        """Output should be boolean for bool return type."""
        result = verify(simple_counter_spec.buggy_code, simple_counter_spec)

        cx = result.counterexample
        assert isinstance(cx.output, bool)


class TestNovelProblems:
    """Test verification on novel problems not in benchmark."""

    def test_novel_bank_account(self):
        """Novel problem: bank account with no overdraft."""
        spec = ProblemSpec(
            problem_id="NOVEL-001",
            name="Bank Account",
            category="novel",
            difficulty="easy",
            description="Bank account that cannot go negative",
            method_signature="def withdraw(self, amount: float) -> bool",
            state_variables=[
                StateVariable("balance", "real", "Account balance", bounds=(0, 10000)),
            ],
            input_variables=[
                InputVariable("amount", "real", "Withdrawal amount", bounds=(0, 1000)),
            ],
            output_type="bool",
            properties=[
                Property(
                    name="no_overdraft",
                    description="Balance must stay non-negative",
                    formula="□(balance >= 0)",
                    encode=lambda pre, post, inp, out: post["balance"] >= 0
                )
            ]
        )

        buggy_code = '''
def withdraw(self, amount: float) -> bool:
    self.balance = self.balance - amount
    return True
'''
        correct_code = '''
def withdraw(self, amount: float) -> bool:
    if self.balance >= amount:
        self.balance = self.balance - amount
        return True
    return False
'''

        # Buggy code should produce counterexample
        result = verify(buggy_code, spec)
        assert result.status == VerificationStatus.COUNTEREXAMPLE
        assert result.counterexample.post_state["balance"] < 0

        # Correct code should verify
        result = verify(correct_code, spec)
        assert result.status == VerificationStatus.VERIFIED

    def test_novel_inventory(self):
        """Novel problem: inventory management."""
        spec = ProblemSpec(
            problem_id="NOVEL-002",
            name="Inventory",
            category="novel",
            difficulty="easy",
            description="Inventory that cannot go negative",
            method_signature="def sell(self, quantity: int) -> bool",
            state_variables=[
                StateVariable("stock", "int", "Items in stock", bounds=(0, 1000)),
            ],
            input_variables=[
                InputVariable("quantity", "int", "Quantity to sell", bounds=(1, 100)),
            ],
            output_type="bool",
            properties=[
                Property(
                    name="stock_non_negative",
                    description="Stock must stay non-negative",
                    formula="□(stock >= 0)",
                    encode=lambda pre, post, inp, out: post["stock"] >= 0
                )
            ]
        )

        buggy_code = '''
def sell(self, quantity: int) -> bool:
    self.stock = self.stock - quantity
    return True
'''
        correct_code = '''
def sell(self, quantity: int) -> bool:
    if self.stock >= quantity:
        self.stock = self.stock - quantity
        return True
    return False
'''

        # Should work without any code changes to Verity
        result = verify(buggy_code, spec)
        assert result.status == VerificationStatus.COUNTEREXAMPLE

        result = verify(correct_code, spec)
        assert result.status == VerificationStatus.VERIFIED
