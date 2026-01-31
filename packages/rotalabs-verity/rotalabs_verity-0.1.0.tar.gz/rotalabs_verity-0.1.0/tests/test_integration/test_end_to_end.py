"""End-to-end integration tests."""

import pytest
from rotalabs_verity.synthesis.cegis import synthesize
from rotalabs_verity.core import SynthesisStatus


class TestEndToEnd:
    def test_synthesize_correct_first_try(self, simple_counter_spec, mock_llm):
        """LLM returns correct code on first try."""
        llm = mock_llm([f"```python\n{simple_counter_spec.correct_code}\n```"])

        result = synthesize(simple_counter_spec, llm, max_iterations=5)

        assert result.status == SynthesisStatus.SUCCESS
        assert result.iterations == 1

    def test_synthesize_with_repair(self, simple_counter_spec, mock_llm):
        """LLM returns buggy code first, then correct."""
        llm = mock_llm([
            f"```python\n{simple_counter_spec.buggy_code}\n```",
            f"```python\n{simple_counter_spec.correct_code}\n```"
        ])

        result = synthesize(simple_counter_spec, llm, max_iterations=5)

        assert result.status == SynthesisStatus.SUCCESS
        assert result.iterations == 2

    def test_synthesize_max_iterations(self, simple_counter_spec, mock_llm):
        """LLM never returns correct code."""
        llm = mock_llm([f"```python\n{simple_counter_spec.buggy_code}\n```"] * 10)

        result = synthesize(simple_counter_spec, llm, max_iterations=3)

        assert result.status == SynthesisStatus.FAILED
        assert result.iterations == 3

    def test_synthesize_with_ce2p_feedback(self, simple_counter_spec, mock_llm):
        """Verify CE2P feedback is used in repair prompt."""
        llm = mock_llm([
            f"```python\n{simple_counter_spec.buggy_code}\n```",
            f"```python\n{simple_counter_spec.correct_code}\n```"
        ])

        result = synthesize(simple_counter_spec, llm, max_iterations=5, use_ce2p=True)

        assert result.status == SynthesisStatus.SUCCESS
        # Check that the second prompt contains CE2P-style feedback
        assert len(llm.calls) == 2
        repair_prompt = llm.calls[1]
        # CE2P feedback includes execution trace and root cause
        assert "trace" in repair_prompt.lower() or "execution" in repair_prompt.lower() or "violated" in repair_prompt.lower()

    def test_synthesize_without_ce2p(self, simple_counter_spec, mock_llm):
        """Verify raw counterexample is used when CE2P disabled."""
        llm = mock_llm([
            f"```python\n{simple_counter_spec.buggy_code}\n```",
            f"```python\n{simple_counter_spec.correct_code}\n```"
        ])

        result = synthesize(simple_counter_spec, llm, max_iterations=5, use_ce2p=False)

        assert result.status == SynthesisStatus.SUCCESS
        assert len(llm.calls) == 2

    def test_synthesize_tracks_verification_results(self, simple_counter_spec, mock_llm):
        """Synthesis tracks all verification results."""
        llm = mock_llm([
            f"```python\n{simple_counter_spec.buggy_code}\n```",
            f"```python\n{simple_counter_spec.correct_code}\n```"
        ])

        result = synthesize(simple_counter_spec, llm, max_iterations=5)

        # Should have 2 verification results: one counterexample, one verified
        assert len(result.verification_results) == 2

    def test_synthesize_records_time(self, simple_counter_spec, mock_llm):
        """Synthesis records total time."""
        llm = mock_llm([f"```python\n{simple_counter_spec.correct_code}\n```"])

        result = synthesize(simple_counter_spec, llm, max_iterations=5)

        assert result.total_time_ms > 0


class TestEndToEndWithProblems:
    """Tests using registered benchmark problems."""

    def test_synthesize_token_bucket(self, mock_llm):
        """Synthesize token bucket rate limiter."""
        from rotalabs_verity.problems import get_problem

        spec = get_problem("RL-001")
        if spec is None:
            pytest.skip("RL-001 not registered")

        llm = mock_llm([f"```python\n{spec.correct_code}\n```"])

        result = synthesize(spec, llm, max_iterations=5)

        assert result.status == SynthesisStatus.SUCCESS

    def test_synthesize_circuit_breaker(self, mock_llm):
        """Synthesize circuit breaker."""
        from rotalabs_verity.problems import get_problem

        spec = get_problem("CB-001")
        if spec is None:
            pytest.skip("CB-001 not registered")

        llm = mock_llm([f"```python\n{spec.correct_code}\n```"])

        result = synthesize(spec, llm, max_iterations=5)

        assert result.status == SynthesisStatus.SUCCESS
