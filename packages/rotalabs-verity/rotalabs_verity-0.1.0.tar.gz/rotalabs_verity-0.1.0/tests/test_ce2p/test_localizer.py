"""Tests for fault localizer."""

import pytest
from rotalabs_verity.ce2p import localize_fault, extract_property_variables, FaultLocation
from rotalabs_verity.core import TraceStep, PropertyViolation, Counterexample


class TestLocalizeFault:
    def test_finds_fault_step(self):
        """Localizer should find the fault step."""
        trace = [
            TraceStep(
                line_number=2,
                source_code="self.tokens -= 1",
                state_before={"tokens": 0.5},
                state_after={"tokens": -0.5},
                is_fault=False
            ),
            TraceStep(
                line_number=3,
                source_code="return True",
                state_before={"tokens": -0.5},
                state_after={"tokens": -0.5},
                is_fault=False
            )
        ]

        prop = PropertyViolation(
            property_name="non_negative",
            property_description="Tokens must be non-negative",
            property_formula="□(tokens >= 0)"
        )

        cx = Counterexample(
            pre_state={"tokens": 0.5},
            inputs={"timestamp": 1.0},
            post_state={"tokens": -0.5},
            output=True
        )

        faults = localize_fault(trace, prop, cx)

        assert len(faults) == 1
        assert faults[0].line_number == 2
        assert faults[0].variable_written == "tokens"
        assert faults[0].value_after == -0.5

    def test_ranks_by_proximity(self):
        """Later writes should have higher confidence."""
        trace = [
            TraceStep(
                line_number=2,
                source_code="self.count = 5",
                state_before={"count": 10},
                state_after={"count": 5},
                is_fault=False
            ),
            TraceStep(
                line_number=3,
                source_code="self.count = -1",
                state_before={"count": 5},
                state_after={"count": -1},
                is_fault=False
            )
        ]

        prop = PropertyViolation(
            property_name="non_negative",
            property_description="Count must be non-negative",
            property_formula="□(count >= 0)"
        )

        cx = Counterexample(
            pre_state={"count": 10},
            inputs={},
            post_state={"count": -1},
            output=True
        )

        faults = localize_fault(trace, prop, cx)

        # Second write should have higher confidence
        assert len(faults) == 2
        assert faults[0].line_number == 3  # Later = first (higher confidence)
        assert faults[0].confidence > faults[1].confidence

    def test_ignores_unrelated_writes(self):
        """Writes to unrelated variables should not be flagged."""
        trace = [
            TraceStep(
                line_number=2,
                source_code="self.other = 100",
                state_before={"tokens": 0.5, "other": 0},
                state_after={"tokens": 0.5, "other": 100},
                is_fault=False
            ),
            TraceStep(
                line_number=3,
                source_code="self.tokens -= 1",
                state_before={"tokens": 0.5, "other": 100},
                state_after={"tokens": -0.5, "other": 100},
                is_fault=False
            )
        ]

        prop = PropertyViolation(
            property_name="non_negative",
            property_description="Tokens must be non-negative",
            property_formula="□(tokens >= 0)"
        )

        cx = Counterexample(
            pre_state={"tokens": 0.5, "other": 0},
            inputs={},
            post_state={"tokens": -0.5, "other": 100},
            output=True
        )

        faults = localize_fault(trace, prop, cx)

        # Should only find the tokens write
        assert len(faults) == 1
        assert faults[0].variable_written == "tokens"


class TestExtractPropertyVariables:
    def test_simple_formula(self):
        """Extract from simple formula."""
        vars = extract_property_variables("□(tokens >= 0)")
        assert "tokens" in vars

    def test_multiple_variables(self):
        """Extract multiple variables."""
        vars = extract_property_variables("□(count <= max)")
        assert "count" in vars
        assert "max" in vars

    def test_filters_keywords(self):
        """Should filter out keywords."""
        vars = extract_property_variables("□(x >= 0 and y >= 0)")
        assert "x" in vars
        assert "y" in vars
        assert "and" not in vars

    def test_handles_suffixes(self):
        """Handle _pre and _post suffixes."""
        vars = extract_property_variables("□(count_post >= 0)")
        assert "count_post" in vars
