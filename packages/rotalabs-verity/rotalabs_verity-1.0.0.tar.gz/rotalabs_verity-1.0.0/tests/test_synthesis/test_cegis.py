"""Tests for CEGIS synthesis loop."""

import pytest
from unittest.mock import Mock

from rotalabs_verity.synthesis import synthesize, CEGISConfig, CEGISSynthesizer
from rotalabs_verity.core import (
    SynthesisStatus,
    VerificationStatus,
    ProblemSpec,
    StateVariable,
    InputVariable,
    Property,
)


class MockLLM:
    """Mock LLM for testing."""

    def __init__(self, responses: list[str]):
        self.responses = responses
        self.call_count = 0

    def generate(self, prompt, **kwargs):
        response = self.responses[min(self.call_count, len(self.responses) - 1)]
        self.call_count += 1

        mock_response = Mock()
        mock_response.content = response
        return mock_response


@pytest.fixture
def simple_spec():
    """Simple counter spec for testing."""
    def encode_non_negative(pre, post, inputs, output):
        return post["count"] >= 0

    return ProblemSpec(
        problem_id="TEST-001",
        name="Simple Counter",
        category="test",
        difficulty="easy",
        description="A counter that can be decremented but never go negative",
        method_signature="def decrement(self, x: int) -> bool",
        state_variables=[
            StateVariable(
                name="count",
                var_type="int",
                description="Current count",
                bounds=(0, 100)
            )
        ],
        input_variables=[
            InputVariable(
                name="x",
                var_type="int",
                description="Amount to decrement",
                bounds=(1, 50)
            )
        ],
        output_type="bool",
        properties=[
            Property(
                name="non_negative",
                description="Count must stay non-negative",
                formula="□(count >= 0)",
                encode=encode_non_negative
            )
        ],
        examples=[]
    )


class TestSynthesizeSuccess:
    def test_success_first_try(self, simple_spec):
        """Synthesis succeeds on first attempt with correct code."""
        correct_code = '''
def decrement(self, x: int) -> bool:
    if self.count >= x:
        self.count = self.count - x
        return True
    return False
'''

        llm = MockLLM([f"```python\n{correct_code}\n```"])

        result = synthesize(simple_spec, llm, max_iterations=5)

        assert result.status == SynthesisStatus.SUCCESS
        assert result.iterations == 1
        assert "if self.count >= x" in result.code

    def test_success_with_repair(self, simple_spec):
        """Synthesis succeeds after repair."""
        buggy_code = '''
def decrement(self, x: int) -> bool:
    self.count = self.count - x
    return True
'''

        correct_code = '''
def decrement(self, x: int) -> bool:
    if self.count >= x:
        self.count = self.count - x
        return True
    return False
'''

        llm = MockLLM([
            f"```python\n{buggy_code}\n```",  # First attempt (buggy)
            f"```python\n{correct_code}\n```"  # Second attempt (fixed)
        ])

        result = synthesize(simple_spec, llm, max_iterations=5)

        assert result.status == SynthesisStatus.SUCCESS
        assert result.iterations == 2


class TestSynthesisFailure:
    def test_max_iterations_exceeded(self, simple_spec):
        """Synthesis fails when max iterations exceeded."""
        buggy_code = '''
def decrement(self, x: int) -> bool:
    self.count = self.count - x
    return True
'''

        # LLM keeps returning buggy code
        llm = MockLLM([f"```python\n{buggy_code}\n```"] * 10)

        result = synthesize(simple_spec, llm, max_iterations=3)

        assert result.status == SynthesisStatus.FAILED
        assert result.iterations == 3
        assert "Failed to synthesize" in result.error_message

    def test_handles_encoding_error(self, simple_spec):
        """Synthesis handles code that can't be encoded."""
        # Code with unsupported feature
        bad_code = '''
def decrement(self, x: int) -> bool:
    items = [1, 2, 3]  # Lists not supported
    return True
'''

        good_code = '''
def decrement(self, x: int) -> bool:
    if self.count >= x:
        self.count = self.count - x
        return True
    return False
'''

        llm = MockLLM([
            f"```python\n{bad_code}\n```",  # Returns unsupported code
            f"```python\n{good_code}\n```"  # Returns simplified code
        ])

        result = synthesize(simple_spec, llm, max_iterations=5)

        # Should eventually succeed after simplification
        assert result.status == SynthesisStatus.SUCCESS


class TestCEGISConfig:
    def test_default_config(self):
        """Test default configuration."""
        config = CEGISConfig()
        assert config.max_iterations == 10
        assert config.verification_timeout_ms == 30000
        assert config.use_ce2p == True

    def test_custom_config(self):
        """Test custom configuration."""
        config = CEGISConfig(max_iterations=5, use_ce2p=False)
        assert config.max_iterations == 5
        assert config.use_ce2p == False


class TestCEGISSynthesizer:
    def test_uses_config(self, simple_spec):
        """Synthesizer uses provided config."""
        config = CEGISConfig(max_iterations=2)

        buggy_code = '''
def decrement(self, x: int) -> bool:
    self.count = self.count - x
    return True
'''

        llm = MockLLM([f"```python\n{buggy_code}\n```"] * 10)
        synthesizer = CEGISSynthesizer(llm, config)

        result = synthesizer.synthesize(simple_spec)

        assert result.iterations == 2

    def test_without_ce2p(self, simple_spec):
        """Synthesizer works without CE2P feedback."""
        config = CEGISConfig(use_ce2p=False)

        correct_code = '''
def decrement(self, x: int) -> bool:
    if self.count >= x:
        self.count = self.count - x
        return True
    return False
'''

        llm = MockLLM([f"```python\n{correct_code}\n```"])
        synthesizer = CEGISSynthesizer(llm, config)

        result = synthesizer.synthesize(simple_spec)

        assert result.status == SynthesisStatus.SUCCESS


class TestSynthesisMetrics:
    def test_records_verification_results(self, simple_spec):
        """Synthesis records all verification results."""
        correct_code = '''
def decrement(self, x: int) -> bool:
    if self.count >= x:
        self.count = self.count - x
        return True
    return False
'''

        llm = MockLLM([f"```python\n{correct_code}\n```"])

        result = synthesize(simple_spec, llm, max_iterations=5)

        assert len(result.verification_results) == 1
        assert result.verification_results[0].status == VerificationStatus.VERIFIED

    def test_records_time(self, simple_spec):
        """Synthesis records total time."""
        correct_code = '''
def decrement(self, x: int) -> bool:
    if self.count >= x:
        self.count = self.count - x
        return True
    return False
'''

        llm = MockLLM([f"```python\n{correct_code}\n```"])

        result = synthesize(simple_spec, llm, max_iterations=5)

        assert result.total_time_ms >= 0
