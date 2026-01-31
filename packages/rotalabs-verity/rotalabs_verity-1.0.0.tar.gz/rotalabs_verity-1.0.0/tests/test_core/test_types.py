"""Tests for core types."""

import pytest
from rotalabs_verity.core import (
    Counterexample,
    VerificationResult,
    VerificationStatus,
    PropertyViolation,
)


class TestCounterexample:
    def test_to_dict(self):
        """Counterexample should flatten correctly."""
        cx = Counterexample(
            pre_state={"x": 1, "y": 2},
            inputs={"z": 3},
            post_state={"x": 4, "y": 5},
            output=True
        )

        d = cx.to_dict()

        assert d["x_pre"] == 1
        assert d["y_pre"] == 2
        assert d["z"] == 3
        assert d["x_post"] == 4
        assert d["y_post"] == 5
        assert d["output"] == True

    def test_frozen(self):
        """Counterexample should be immutable (frozen)."""
        cx = Counterexample(
            pre_state={"x": 1},
            inputs={},
            post_state={"x": 2},
            output=True
        )

        # Should be immutable - can't reassign fields
        with pytest.raises(AttributeError):
            cx.output = False

    def test_to_dict_with_floats(self):
        """Counterexample with float values."""
        cx = Counterexample(
            pre_state={"tokens": 0.5, "last_update": 0.0},
            inputs={"timestamp": 1.0},
            post_state={"tokens": -0.5, "last_update": 1.0},
            output=True
        )

        d = cx.to_dict()

        assert d["tokens_pre"] == 0.5
        assert d["tokens_post"] == -0.5
        assert d["timestamp"] == 1.0
        assert d["output"] == True


class TestVerificationResult:
    def test_verified(self):
        """Verified result should have no counterexample."""
        result = VerificationResult(status=VerificationStatus.VERIFIED)

        assert result.status == VerificationStatus.VERIFIED
        assert result.counterexample is None
        assert result.property_violated is None

    def test_counterexample(self):
        """Counterexample result should have violation details."""
        result = VerificationResult(
            status=VerificationStatus.COUNTEREXAMPLE,
            property_violated=PropertyViolation("p", "desc", "formula"),
            counterexample=Counterexample({}, {}, {}, None)
        )

        assert result.status == VerificationStatus.COUNTEREXAMPLE
        assert result.property_violated is not None
        assert result.counterexample is not None

    def test_encoding_error(self):
        """Encoding error result."""
        result = VerificationResult(
            status=VerificationStatus.ENCODING_ERROR,
            error_message="Lists not supported"
        )

        assert result.status == VerificationStatus.ENCODING_ERROR
        assert result.error_message is not None


class TestPropertyViolation:
    def test_creation(self):
        """PropertyViolation should store all fields."""
        pv = PropertyViolation(
            property_name="non_negative",
            property_description="Count must never go negative",
            property_formula="□(count >= 0)"
        )

        assert pv.property_name == "non_negative"
        assert pv.property_description == "Count must never go negative"
        assert pv.property_formula == "□(count >= 0)"

    def test_frozen(self):
        """PropertyViolation should be hashable."""
        pv = PropertyViolation("name", "desc", "formula")
        hash(pv)
