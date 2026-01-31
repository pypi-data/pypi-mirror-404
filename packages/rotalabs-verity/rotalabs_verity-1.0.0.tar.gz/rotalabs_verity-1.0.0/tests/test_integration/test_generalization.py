"""
Generalization tests.

These tests verify that Verity works on NOVEL problems not in the benchmark.
If these fail, there's hidden problem-specific logic.
"""

import pytest
import z3
from rotalabs_verity.verifier import verify
from rotalabs_verity.ce2p.feedback import generate_feedback
from rotalabs_verity.core import (
    ProblemSpec,
    StateVariable,
    InputVariable,
    Property,
    VerificationStatus,
    Counterexample,
    PropertyViolation,
    VerificationResult,
)


class TestGeneralization:
    """Tests on completely novel problems."""

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
            ],
            examples=[],
            buggy_code="def withdraw(self, amount: float) -> bool:\n    self.balance = self.balance - amount\n    return True",
            correct_code="def withdraw(self, amount: float) -> bool:\n    if self.balance >= amount:\n        self.balance = self.balance - amount\n        return True\n    return False"
        )

        # Verify buggy code produces counterexample
        result = verify(spec.buggy_code, spec)
        assert result.status == VerificationStatus.COUNTEREXAMPLE

        # Verify correct code passes
        result = verify(spec.correct_code, spec)
        assert result.status == VerificationStatus.VERIFIED

        # Generate feedback for buggy code
        buggy_result = VerificationResult(
            status=VerificationStatus.COUNTEREXAMPLE,
            property_violated=PropertyViolation("no_overdraft", "Balance non-negative", "□(balance >= 0)"),
            counterexample=Counterexample(
                pre_state={"balance": 50.0},
                inputs={"amount": 100.0},
                post_state={"balance": -50.0},
                output=True
            )
        )

        feedback = generate_feedback(spec.buggy_code, buggy_result)
        assert feedback is not None
        assert "balance" in feedback.root_cause.lower()

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
            ],
            examples=[],
            buggy_code="def sell(self, quantity: int) -> bool:\n    self.stock = self.stock - quantity\n    return True",
            correct_code="def sell(self, quantity: int) -> bool:\n    if self.stock >= quantity:\n        self.stock = self.stock - quantity\n        return True\n    return False"
        )

        # Should work without any code changes to Verity
        result = verify(spec.buggy_code, spec)
        assert result.status == VerificationStatus.COUNTEREXAMPLE

        result = verify(spec.correct_code, spec)
        assert result.status == VerificationStatus.VERIFIED

    def test_novel_temperature_controller(self):
        """Novel problem: temperature that must stay in range."""
        def temp_in_range(pre, post, inp, out):
            return z3.And(post["temp"] >= 0, post["temp"] <= 100)

        spec = ProblemSpec(
            problem_id="NOVEL-003",
            name="Temperature Controller",
            category="novel",
            difficulty="medium",
            description="Temperature controller with bounds",
            method_signature="def adjust(self, delta: float) -> bool",
            state_variables=[
                StateVariable("temp", "real", "Current temperature", bounds=(0, 100)),
            ],
            input_variables=[
                InputVariable("delta", "real", "Temperature change", bounds=(-10, 10)),
            ],
            output_type="bool",
            properties=[
                Property(
                    name="temp_in_range",
                    description="Temperature must stay in [0, 100]",
                    formula="□(0 <= temp <= 100)",
                    encode=temp_in_range
                )
            ],
            examples=[],
            buggy_code="def adjust(self, delta: float) -> bool:\n    self.temp = self.temp + delta\n    return True",
            correct_code="def adjust(self, delta: float) -> bool:\n    new_temp = self.temp + delta\n    if new_temp >= 0:\n        if new_temp <= 100:\n            self.temp = new_temp\n            return True\n    return False"
        )

        result = verify(spec.buggy_code, spec)
        assert result.status == VerificationStatus.COUNTEREXAMPLE

        result = verify(spec.correct_code, spec)
        assert result.status == VerificationStatus.VERIFIED

    def test_novel_energy_meter(self):
        """Novel problem: energy meter with consumption limit."""
        spec = ProblemSpec(
            problem_id="NOVEL-004",
            name="Energy Meter",
            category="novel",
            difficulty="easy",
            description="Energy meter that tracks consumption",
            method_signature="def consume(self, watts: int) -> bool",
            state_variables=[
                StateVariable("remaining", "int", "Remaining energy", bounds=(0, 10000)),
            ],
            input_variables=[
                InputVariable("watts", "int", "Energy to consume", bounds=(1, 500)),
            ],
            output_type="bool",
            properties=[
                Property(
                    name="remaining_non_negative",
                    description="Remaining energy must stay non-negative",
                    formula="□(remaining >= 0)",
                    encode=lambda pre, post, inp, out: post["remaining"] >= 0
                )
            ],
            examples=[],
            buggy_code="def consume(self, watts: int) -> bool:\n    self.remaining = self.remaining - watts\n    return True",
            correct_code="def consume(self, watts: int) -> bool:\n    if self.remaining >= watts:\n        self.remaining = self.remaining - watts\n        return True\n    return False"
        )

        result = verify(spec.buggy_code, spec)
        assert result.status == VerificationStatus.COUNTEREXAMPLE

        result = verify(spec.correct_code, spec)
        assert result.status == VerificationStatus.VERIFIED

    def test_no_hardcoded_patterns(self):
        """Verify no problem-specific code in Verity modules."""
        import inspect
        import rotalabs_verity.encoder.z3_encoder as encoder
        import rotalabs_verity.verifier.verifier as verifier
        import rotalabs_verity.ce2p.feedback as ce2p

        sources = [
            inspect.getsource(encoder),
            inspect.getsource(verifier),
            inspect.getsource(ce2p),
        ]

        forbidden = [
            "token_bucket",
            "circuit_breaker",
            "rate_limit",
            "consensus",
            "replication",
            'category ==',
            'problem_id ==',
            "RL-001",
            "CB-001",
        ]

        for source in sources:
            source_lower = source.lower()
            for pattern in forbidden:
                assert pattern.lower() not in source_lower, \
                    f"Found forbidden pattern '{pattern}' in Verity code"
