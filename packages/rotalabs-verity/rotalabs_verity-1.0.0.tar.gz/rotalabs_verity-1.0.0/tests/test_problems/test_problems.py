"""Tests for benchmark problems."""

import pytest
from rotalabs_verity.problems import (
    get_problem,
    list_problems,
    list_by_category,
    list_by_difficulty,
)
from rotalabs_verity.verifier import verify
from rotalabs_verity.core import VerificationStatus


class TestRegistry:
    def test_list_problems(self):
        """Registry lists all problems."""
        problems = list_problems()
        assert "RL-001" in problems
        assert "RL-003" in problems
        assert "CB-001" in problems
        assert "CO-002" in problems
        assert "TX-005" in problems

    def test_get_problem(self):
        """Get problem by ID."""
        spec = get_problem("RL-001")
        assert spec is not None
        assert spec.problem_id == "RL-001"
        assert spec.name == "Token Bucket Rate Limiter"

    def test_unknown_problem(self):
        """Unknown problem returns None."""
        spec = get_problem("UNKNOWN-999")
        assert spec is None

    def test_list_by_category(self):
        """Filter problems by category."""
        rl_problems = list_by_category("rate_limiting")
        assert "RL-001" in rl_problems
        assert "RL-003" in rl_problems

    def test_list_by_difficulty(self):
        """Filter problems by difficulty."""
        easy = list_by_difficulty("easy")
        assert "RL-003" in easy
        assert "CO-002" in easy
        assert "TX-005" in easy


class TestRL001TokenBucket:
    def test_spec_complete(self):
        """Token bucket spec has all required fields."""
        spec = get_problem("RL-001")
        assert spec.problem_id == "RL-001"
        assert len(spec.state_variables) >= 2
        assert len(spec.properties) >= 2
        assert len(spec.examples) >= 2
        assert spec.buggy_code != ""
        assert spec.correct_code != ""

    def test_buggy_code_fails(self):
        """Buggy code should fail verification."""
        spec = get_problem("RL-001")
        result = verify(spec.buggy_code, spec)
        assert result.status == VerificationStatus.COUNTEREXAMPLE

    def test_correct_code_passes(self):
        """Correct code should pass verification."""
        spec = get_problem("RL-001")
        result = verify(spec.correct_code, spec)
        assert result.status == VerificationStatus.VERIFIED


class TestRL003LeakyBucket:
    def test_spec_complete(self):
        """Leaky bucket spec has all required fields."""
        spec = get_problem("RL-003")
        assert spec.problem_id == "RL-003"
        assert spec.difficulty == "easy"
        assert len(spec.properties) >= 2

    def test_buggy_code_fails(self):
        """Buggy code should fail verification."""
        spec = get_problem("RL-003")
        result = verify(spec.buggy_code, spec)
        assert result.status == VerificationStatus.COUNTEREXAMPLE

    def test_correct_code_passes(self):
        """Correct code should pass verification."""
        spec = get_problem("RL-003")
        result = verify(spec.correct_code, spec)
        assert result.status == VerificationStatus.VERIFIED


class TestCB001CircuitBreaker:
    def test_spec_complete(self):
        """Circuit breaker spec has all required fields."""
        spec = get_problem("CB-001")
        assert spec.problem_id == "CB-001"
        assert spec.category == "circuit_breaker"
        assert len(spec.properties) >= 2

    def test_buggy_code_fails(self):
        """Buggy code should fail verification."""
        spec = get_problem("CB-001")
        result = verify(spec.buggy_code, spec)
        assert result.status == VerificationStatus.COUNTEREXAMPLE

    def test_correct_code_passes(self):
        """Correct code should pass verification."""
        spec = get_problem("CB-001")
        result = verify(spec.correct_code, spec)
        assert result.status == VerificationStatus.VERIFIED


class TestCO002Semaphore:
    def test_spec_complete(self):
        """Semaphore spec has all required fields."""
        spec = get_problem("CO-002")
        assert spec.problem_id == "CO-002"
        assert spec.difficulty == "easy"
        assert len(spec.properties) >= 2

    def test_buggy_code_fails(self):
        """Buggy code should fail verification."""
        spec = get_problem("CO-002")
        result = verify(spec.buggy_code, spec)
        assert result.status == VerificationStatus.COUNTEREXAMPLE

    def test_correct_code_passes(self):
        """Correct code should pass verification."""
        spec = get_problem("CO-002")
        result = verify(spec.correct_code, spec)
        assert result.status == VerificationStatus.VERIFIED


class TestTX005Idempotent:
    def test_spec_complete(self):
        """Idempotent spec has all required fields."""
        spec = get_problem("TX-005")
        assert spec.problem_id == "TX-005"
        assert spec.difficulty == "easy"
        assert len(spec.properties) >= 2

    def test_buggy_code_fails(self):
        """Buggy code should fail verification."""
        spec = get_problem("TX-005")
        result = verify(spec.buggy_code, spec)
        assert result.status == VerificationStatus.COUNTEREXAMPLE

    def test_correct_code_passes(self):
        """Correct code should pass verification."""
        spec = get_problem("TX-005")
        result = verify(spec.correct_code, spec)
        assert result.status == VerificationStatus.VERIFIED
