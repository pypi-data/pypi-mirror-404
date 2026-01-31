"""Tests for problem specification types."""

import pytest
import z3
from rotalabs_verity.core import (
    ProblemSpec,
    StateVariable,
    InputVariable,
    Property,
    Example,
)


class TestProblemSpec:
    def test_create_z3_variables(self):
        """Problem should create correct Z3 variables."""
        spec = ProblemSpec(
            problem_id="TEST-001",
            name="Test",
            category="test",
            difficulty="easy",
            description="Test problem",
            method_signature="def test(self, x: int) -> bool",
            state_variables=[
                StateVariable("count", "int", "A counter"),
            ],
            input_variables=[
                InputVariable("x", "int", "Input value"),
            ],
            output_type="bool",
            properties=[]
        )

        pre, post, inputs, output = spec.create_z3_variables()

        assert "count" in pre
        assert "count" in post
        assert "x" in inputs
        assert z3.is_bool(output)

    def test_create_z3_variables_real(self):
        """Problem with real-valued variables."""
        spec = ProblemSpec(
            problem_id="TEST-002",
            name="Test Real",
            category="test",
            difficulty="easy",
            description="Test with real values",
            method_signature="def test(self, t: float) -> bool",
            state_variables=[
                StateVariable("tokens", "real", "Token count"),
                StateVariable("last_update", "real", "Last update time"),
            ],
            input_variables=[
                InputVariable("timestamp", "real", "Current time"),
            ],
            output_type="bool",
            properties=[]
        )

        pre, post, inputs, output = spec.create_z3_variables()

        assert "tokens" in pre
        assert "last_update" in pre
        assert "timestamp" in inputs
        assert z3.is_real(pre["tokens"])
        assert z3.is_real(inputs["timestamp"])

    def test_get_property(self):
        """Should retrieve property by name."""
        prop = Property(
            name="non_negative",
            description="Must be non-negative",
            formula="□(x >= 0)",
            encode=lambda pre, post, inp, out: post["x"] >= 0
        )

        spec = ProblemSpec(
            problem_id="TEST-003",
            name="Test",
            category="test",
            difficulty="easy",
            description="Test",
            method_signature="def test(self) -> bool",
            state_variables=[StateVariable("x", "int", "X")],
            input_variables=[],
            output_type="bool",
            properties=[prop]
        )

        found = spec.get_property("non_negative")
        assert found is not None
        assert found.name == "non_negative"

        not_found = spec.get_property("nonexistent")
        assert not_found is None


class TestStateVariable:
    def test_with_bounds(self):
        """StateVariable with bounds."""
        sv = StateVariable(
            name="count",
            var_type="int",
            description="A counter",
            bounds=(0, 100),
            initial_value=50
        )

        assert sv.name == "count"
        assert sv.var_type == "int"
        assert sv.bounds == (0, 100)
        assert sv.initial_value == 50

    def test_frozen(self):
        """StateVariable should be hashable."""
        sv = StateVariable("x", "int", "desc")
        hash(sv)


class TestExample:
    def test_creation(self):
        """Example should store all fields."""
        ex = Example(
            name="basic",
            description="Basic example",
            pre_state={"count": 10},
            inputs={"amount": 3},
            expected_output=True,
            expected_post_state={"count": 7}
        )

        assert ex.name == "basic"
        assert ex.pre_state == {"count": 10}
        assert ex.inputs == {"amount": 3}
        assert ex.expected_output == True
        assert ex.expected_post_state == {"count": 7}
