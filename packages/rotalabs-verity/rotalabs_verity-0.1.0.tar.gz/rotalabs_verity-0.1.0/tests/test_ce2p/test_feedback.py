"""Tests for feedback generator."""

import pytest
from rotalabs_verity.ce2p import generate_feedback
from rotalabs_verity.core import (
    Counterexample,
    PropertyViolation,
    VerificationResult,
    VerificationStatus,
)


class TestGenerateFeedback:
    def test_generates_complete_feedback(self):
        """Generate complete feedback from verification result."""
        code = '''
def allow(self, timestamp: float) -> bool:
    self.tokens = self.tokens - 1
    return True
'''

        result = VerificationResult(
            status=VerificationStatus.COUNTEREXAMPLE,
            property_violated=PropertyViolation(
                property_name="non_negative",
                property_description="Tokens must be non-negative",
                property_formula="□(tokens >= 0)"
            ),
            counterexample=Counterexample(
                pre_state={"tokens": 0.5},
                inputs={"timestamp": 1.0},
                post_state={"tokens": -0.5},
                output=True
            )
        )

        feedback = generate_feedback(code, result)

        assert feedback is not None
        assert feedback.property_violated.property_name == "non_negative"
        assert feedback.counterexample == result.counterexample
        assert len(feedback.execution_trace) > 0
        assert feedback.fault_line > 0
        assert len(feedback.root_cause) > 0
        assert len(feedback.suggested_fix) > 0

    def test_marks_fault_in_trace(self):
        """Fault step should be marked in trace."""
        code = '''
def allow(self, timestamp: float) -> bool:
    self.tokens = self.tokens - 1
    return True
'''

        result = VerificationResult(
            status=VerificationStatus.COUNTEREXAMPLE,
            property_violated=PropertyViolation(
                property_name="non_negative",
                property_description="Tokens must be non-negative",
                property_formula="□(tokens >= 0)"
            ),
            counterexample=Counterexample(
                pre_state={"tokens": 0.5},
                inputs={"timestamp": 1.0},
                post_state={"tokens": -0.5},
                output=True
            )
        )

        feedback = generate_feedback(code, result)

        assert feedback is not None
        assert any(step.is_fault for step in feedback.execution_trace)

    def test_includes_suggested_fix(self):
        """Feedback should include suggested fix."""
        code = '''
def allow(self, timestamp: float) -> bool:
    self.tokens = self.tokens - 1
    return True
'''

        result = VerificationResult(
            status=VerificationStatus.COUNTEREXAMPLE,
            property_violated=PropertyViolation(
                property_name="non_negative",
                property_description="Tokens must be non-negative",
                property_formula="□(tokens >= 0)"
            ),
            counterexample=Counterexample(
                pre_state={"tokens": 0.5},
                inputs={"timestamp": 1.0},
                post_state={"tokens": -0.5},
                output=True
            )
        )

        feedback = generate_feedback(code, result)

        assert feedback is not None
        assert "if" in feedback.suggested_fix.lower() or "guard" in feedback.suggested_fix.lower()

    def test_returns_none_for_verified(self):
        """Return None when no counterexample."""
        result = VerificationResult(status=VerificationStatus.VERIFIED)

        feedback = generate_feedback("def f(self): pass", result)

        assert feedback is None

    def test_novel_problem(self):
        """Test on completely novel problem."""
        code = '''
def withdraw(self, amount: int) -> bool:
    self.balance = self.balance - amount
    return True
'''

        result = VerificationResult(
            status=VerificationStatus.COUNTEREXAMPLE,
            property_violated=PropertyViolation(
                property_name="no_overdraft",
                property_description="Balance must stay positive",
                property_formula="□(balance >= 0)"
            ),
            counterexample=Counterexample(
                pre_state={"balance": 50},
                inputs={"amount": 100},
                post_state={"balance": -50},
                output=True
            )
        )

        feedback = generate_feedback(code, result)

        assert feedback is not None
        assert "balance" in feedback.root_cause.lower()
        assert feedback.fault_line > 0


class TestFeedbackContent:
    def test_root_cause_mentions_property(self):
        """Root cause should mention violated property."""
        code = '''
def method(self, x: int) -> bool:
    self.value = self.value - x
    return True
'''

        result = VerificationResult(
            status=VerificationStatus.COUNTEREXAMPLE,
            property_violated=PropertyViolation(
                property_name="stays_positive",
                property_description="Value must stay positive",
                property_formula="□(value >= 0)"
            ),
            counterexample=Counterexample(
                pre_state={"value": 10},
                inputs={"x": 20},
                post_state={"value": -10},
                output=True
            )
        )

        feedback = generate_feedback(code, result)

        assert feedback is not None
        assert "stays_positive" in feedback.root_cause

    def test_root_cause_mentions_values(self):
        """Root cause should mention the state change."""
        code = '''
def method(self, x: int) -> bool:
    self.count = self.count - x
    return True
'''

        result = VerificationResult(
            status=VerificationStatus.COUNTEREXAMPLE,
            property_violated=PropertyViolation(
                property_name="non_negative",
                property_description="Count must be non-negative",
                property_formula="□(count >= 0)"
            ),
            counterexample=Counterexample(
                pre_state={"count": 5},
                inputs={"x": 10},
                post_state={"count": -5},
                output=True
            )
        )

        feedback = generate_feedback(code, result)

        assert feedback is not None
        assert "5" in feedback.root_cause
        assert "-5" in feedback.root_cause
