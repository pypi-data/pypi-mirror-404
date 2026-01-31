"""Tests for repair synthesizer."""

import pytest
from rotalabs_verity.ce2p import synthesize_repair, RepairSuggestion
from rotalabs_verity.ce2p.abducer import parse_property_bound
from rotalabs_verity.core import Counterexample, ProblemSpec, StateVariable


class TestSynthesizeRepair:
    def test_synthesize_guard_for_decrement(self):
        """Synthesize guard for decrement operation."""
        cx = Counterexample(
            pre_state={"tokens": 0.5},
            inputs={"timestamp": 1.0},
            post_state={"tokens": -0.5},
            output=True
        )

        repair = synthesize_repair(
            fault_line=2,
            fault_statement="self.tokens -= 1",
            property_formula="□(tokens >= 0)",
            counterexample=cx
        )

        assert repair is not None
        assert repair.insert_before_line == 2
        assert "self.tokens" in repair.guard_condition or "tokens" in repair.guard_condition
        assert "pass" in repair.action_if_false or "Skip" in repair.action_if_false

    def test_converts_to_python(self):
        """Guard should be valid Python."""
        cx = Counterexample(
            pre_state={"count": 5},
            inputs={"amount": 10},
            post_state={"count": -5},
            output=True
        )

        repair = synthesize_repair(
            fault_line=3,
            fault_statement="self.count -= amount",
            property_formula="□(count >= 0)",
            counterexample=cx
        )

        assert repair is not None
        # Guard should be valid Python expression
        assert ">=" in repair.guard_condition or ">" in repair.guard_condition

    def test_handles_regular_assignment(self):
        """Handle regular assignment (not augmented)."""
        cx = Counterexample(
            pre_state={"value": 10},
            inputs={"x": 5},
            post_state={"value": 5},
            output=True
        )

        repair = synthesize_repair(
            fault_line=2,
            fault_statement="self.value = self.value - x",
            property_formula="□(value >= 0)",
            counterexample=cx
        )

        assert repair is not None

    def test_fallback_on_complex_statement(self):
        """Fallback for complex statements."""
        cx = Counterexample(
            pre_state={"x": 10},
            inputs={},
            post_state={"x": -5},
            output=True
        )

        # Even complex statements should return something
        repair = synthesize_repair(
            fault_line=5,
            fault_statement="self.x = min(self.x - 10, 100)",
            property_formula="□(x >= 0)",
            counterexample=cx
        )

        assert repair is not None

    def test_resolves_symbolic_bound_from_spec(self):
        """Symbolic bounds should be resolved to actual values from state variable bounds."""
        # Create a minimal spec with state variable bounds
        spec = ProblemSpec(
            problem_id="TEST-001",
            name="Test",
            category="test",
            difficulty="easy",
            description="Test problem",
            method_signature="def test(self) -> int",
            state_variables=[
                StateVariable(
                    name="votes",
                    var_type="int",
                    description="Vote count",
                    bounds=(0, 5),  # Upper bound is 5
                    initial_value=0
                )
            ],
            input_variables=[],
            output_type="int",
            properties=[],
            examples=[],
        )

        # Without spec, symbolic bound should remain symbolic
        var, bound_type, bound_val = parse_property_bound("□(votes <= max_votes)")
        assert bound_val == "max_votes"  # Still symbolic

        # With spec, symbolic bound should be resolved to 5
        var, bound_type, bound_val = parse_property_bound("□(votes <= max_votes)", spec)
        assert bound_val == 5  # Resolved to actual bound

    def test_generates_numeric_guard_with_spec(self):
        """Guard should use numeric bound when spec is provided."""
        spec = ProblemSpec(
            problem_id="TEST-001",
            name="Test",
            category="test",
            difficulty="easy",
            description="Test problem",
            method_signature="def test(self) -> int",
            state_variables=[
                StateVariable(
                    name="votes",
                    var_type="int",
                    description="Vote count",
                    bounds=(0, 5),
                    initial_value=0
                )
            ],
            input_variables=[],
            output_type="int",
            properties=[],
            examples=[],
        )

        cx = Counterexample(
            pre_state={"votes": 5},
            inputs={},
            post_state={"votes": 6},
            output=True
        )

        repair = synthesize_repair(
            fault_line=3,
            fault_statement="self.votes = self.votes + 1",
            property_formula="□(votes <= max_votes)",
            counterexample=cx,
            spec=spec
        )

        assert repair is not None
        # Should use numeric bound 5, not symbolic "max_votes"
        assert "5" in repair.guard_condition
        assert "max_votes" not in repair.guard_condition
