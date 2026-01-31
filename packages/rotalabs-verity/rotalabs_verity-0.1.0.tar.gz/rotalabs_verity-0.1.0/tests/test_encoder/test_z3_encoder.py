"""Tests for Z3 encoder."""

import pytest
import z3
from rotalabs_verity.encoder import encode_method, encode_with_bounds, EncodingResult, ParseError
from rotalabs_verity.core import ProblemSpec, StateVariable, InputVariable, Property


@pytest.fixture
def simple_spec():
    """Simple counter specification."""
    return ProblemSpec(
        problem_id="TEST-001",
        name="Simple Counter",
        category="test",
        difficulty="easy",
        description="A counter that can be decremented",
        method_signature="def decrement(self, amount: int) -> bool",
        state_variables=[
            StateVariable("count", "int", "Current count", bounds=(0, 100)),
        ],
        input_variables=[
            InputVariable("amount", "int", "Amount to decrement", bounds=(1, 10)),
        ],
        output_type="bool",
        properties=[]
    )


@pytest.fixture
def token_bucket_spec():
    """Token bucket specification."""
    return ProblemSpec(
        problem_id="RL-001",
        name="Token Bucket",
        category="rate_limiting",
        difficulty="medium",
        description="Token bucket rate limiter",
        method_signature="def allow(self, timestamp: float) -> bool",
        state_variables=[
            StateVariable("tokens", "real", "Token count", bounds=(0, 100)),
            StateVariable("last_update", "real", "Last update time", bounds=(0, None)),
        ],
        input_variables=[
            InputVariable("timestamp", "real", "Request time", bounds=(0, None)),
        ],
        output_type="bool",
        properties=[]
    )


class TestEncodeMethod:
    def test_simple_return(self, simple_spec):
        """Encode simple return."""
        code = '''
def decrement(self, amount: int) -> bool:
    return True
'''
        result = encode_method(code, simple_spec)

        assert result is not None
        assert "count" in result.pre_state
        assert "count" in result.post_state
        assert "amount" in result.inputs

    def test_assignment(self, simple_spec):
        """Encode assignment and verify semantics."""
        code = '''
def decrement(self, amount: int) -> bool:
    self.count = self.count - amount
    return True
'''
        result = encode_method(code, simple_spec)

        solver = z3.Solver()
        solver.add(result.transition)
        solver.add(result.pre_state["count"] == 10)
        solver.add(result.inputs["amount"] == 3)

        assert solver.check() == z3.sat
        model = solver.model()

        # count_post should be 7
        post_val = model.eval(result.post_state["count"])
        assert post_val.as_long() == 7

    def test_conditional(self, simple_spec):
        """Encode conditional and verify both branches."""
        code = '''
def decrement(self, amount: int) -> bool:
    if self.count >= amount:
        self.count = self.count - amount
        return True
    return False
'''
        result = encode_method(code, simple_spec)

        solver = z3.Solver()
        solver.add(result.transition)

        # Case 1: count >= amount (should succeed)
        solver.push()
        solver.add(result.pre_state["count"] == 10)
        solver.add(result.inputs["amount"] == 3)
        assert solver.check() == z3.sat
        model = solver.model()
        assert model.eval(result.output) == True
        assert model.eval(result.post_state["count"]).as_long() == 7
        solver.pop()

        # Case 2: count < amount (should fail)
        solver.push()
        solver.add(result.pre_state["count"] == 2)
        solver.add(result.inputs["amount"] == 5)
        assert solver.check() == z3.sat
        model = solver.model()
        assert model.eval(result.output) == False
        solver.pop()

    def test_token_bucket_buggy(self, token_bucket_spec):
        """Encode buggy token bucket (always decrements)."""
        code = '''
def allow(self, timestamp: float) -> bool:
    self.tokens = self.tokens - 1
    return True
'''
        result = encode_method(code, token_bucket_spec)

        solver = z3.Solver()
        solver.add(result.transition)

        # With tokens = 0.5, this should result in tokens = -0.5
        solver.add(result.pre_state["tokens"] == 0.5)
        solver.add(result.pre_state["last_update"] == 0)
        solver.add(result.inputs["timestamp"] == 1.0)

        assert solver.check() == z3.sat
        model = solver.model()

        # tokens_post should be -0.5 (the bug!)
        post_tokens = model.eval(result.post_state["tokens"])
        # Z3 returns a RatNumRef for reals
        assert float(post_tokens.as_fraction()) == -0.5

    def test_token_bucket_correct(self, token_bucket_spec):
        """Encode correct token bucket."""
        code = '''
def allow(self, timestamp: float) -> bool:
    if self.tokens >= 1:
        self.tokens = self.tokens - 1
        return True
    return False
'''
        result = encode_method(code, token_bucket_spec)

        solver = z3.Solver()
        solver.add(result.transition)

        # With tokens = 0.5, should not decrement
        solver.push()
        solver.add(result.pre_state["tokens"] == 0.5)
        solver.add(result.pre_state["last_update"] == 0)
        solver.add(result.inputs["timestamp"] == 1.0)

        assert solver.check() == z3.sat
        model = solver.model()

        # tokens_post should still be 0.5
        post_tokens = model.eval(result.post_state["tokens"])
        assert float(post_tokens.as_fraction()) == 0.5
        assert model.eval(result.output) == False
        solver.pop()

        # With tokens = 5, should decrement
        solver.push()
        solver.add(result.pre_state["tokens"] == 5)
        solver.add(result.pre_state["last_update"] == 0)
        solver.add(result.inputs["timestamp"] == 1.0)

        assert solver.check() == z3.sat
        model = solver.model()

        post_tokens = model.eval(result.post_state["tokens"])
        assert float(post_tokens.as_fraction()) == 4
        assert model.eval(result.output) == True
        solver.pop()


class TestEncodeWithBounds:
    def test_includes_bounds(self, simple_spec):
        """Encode with bounds constraints."""
        code = '''
def decrement(self, amount: int) -> bool:
    self.count = self.count - amount
    return True
'''
        result = encode_with_bounds(code, simple_spec)

        solver = z3.Solver()
        solver.add(result.transition)

        # Try to find solution outside bounds
        solver.push()
        solver.add(result.pre_state["count"] == -5)  # Outside bounds (0, 100)

        # Should be unsat because bounds are enforced
        assert solver.check() == z3.unsat
        solver.pop()

        # Within bounds should work
        solver.push()
        solver.add(result.pre_state["count"] == 50)
        solver.add(result.inputs["amount"] == 5)

        assert solver.check() == z3.sat
        solver.pop()
