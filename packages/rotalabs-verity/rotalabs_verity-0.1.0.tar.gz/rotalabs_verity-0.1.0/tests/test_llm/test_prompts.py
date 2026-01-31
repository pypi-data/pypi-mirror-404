"""Tests for prompt builder."""

import pytest
from rotalabs_verity.llm import PromptBuilder
from rotalabs_verity.core import (
    StateVariable,
    InputVariable,
    Property,
    ProblemSpec,
    Example,
    Counterexample,
    PropertyViolation,
    TraceStep,
    StructuredFeedback,
)


@pytest.fixture
def sample_spec():
    """Sample problem specification."""
    def encode_prop(pre, post, inputs, output):
        return post["count"] >= 0

    return ProblemSpec(
        problem_id="TEST-001",
        name="Counter",
        category="test",
        difficulty="easy",
        description="A simple counter that can be decremented",
        method_signature="def decrement(self, amount: int) -> bool",
        state_variables=[
            StateVariable(
                name="count",
                var_type="int",
                description="Current count value",
                bounds=(0, 100)
            )
        ],
        input_variables=[
            InputVariable(
                name="amount",
                var_type="int",
                description="Amount to subtract",
                bounds=(1, 50)
            )
        ],
        output_type="bool",
        properties=[
            Property(
                name="non_negative",
                description="Count must stay non-negative",
                formula="□(count >= 0)",
                encode=encode_prop
            )
        ],
        examples=[
            Example(
                name="Basic decrement",
                description="Decrement count by 5",
                pre_state={"count": 10},
                inputs={"amount": 5},
                expected_output=True,
                expected_post_state={"count": 5}
            )
        ]
    )


@pytest.fixture
def sample_feedback():
    """Sample CE2P feedback."""
    return StructuredFeedback(
        property_violated=PropertyViolation(
            property_name="non_negative",
            property_description="Count must stay non-negative",
            property_formula="□(count >= 0)"
        ),
        counterexample=Counterexample(
            pre_state={"count": 5},
            inputs={"amount": 10},
            post_state={"count": -5},
            output=True
        ),
        execution_trace=[
            TraceStep(
                line_number=2,
                source_code="self.count = self.count - amount",
                state_before={"count": 5},
                state_after={"count": -5},
                is_fault=True
            ),
            TraceStep(
                line_number=3,
                source_code="return True",
                state_before={"count": -5},
                state_after={"count": -5},
                is_fault=False
            )
        ],
        fault_line=2,
        root_cause="Property 'non_negative' was violated.",
        suggested_fix="Add a guard: if self.count >= amount",
        repair_guard="self.count >= amount"
    )


class TestBuildInitialPrompt:
    def test_includes_description(self, sample_spec):
        """Initial prompt includes problem description."""
        prompt = PromptBuilder.build_initial_prompt(sample_spec)
        assert sample_spec.description in prompt

    def test_includes_signature(self, sample_spec):
        """Initial prompt includes method signature."""
        prompt = PromptBuilder.build_initial_prompt(sample_spec)
        assert sample_spec.method_signature in prompt

    def test_includes_state_variables(self, sample_spec):
        """Initial prompt includes state variables."""
        prompt = PromptBuilder.build_initial_prompt(sample_spec)
        assert "count" in prompt
        assert "int" in prompt

    def test_includes_properties(self, sample_spec):
        """Initial prompt includes properties."""
        prompt = PromptBuilder.build_initial_prompt(sample_spec)
        assert "non_negative" in prompt
        assert "□(count >= 0)" in prompt

    def test_includes_examples(self, sample_spec):
        """Initial prompt includes examples."""
        prompt = PromptBuilder.build_initial_prompt(sample_spec)
        assert "Basic decrement" in prompt

    def test_includes_requirements(self, sample_spec):
        """Initial prompt includes Python subset requirements."""
        prompt = PromptBuilder.build_initial_prompt(sample_spec)
        assert "min, max, abs" in prompt
        assert "Do NOT use" in prompt


class TestBuildRepairPrompt:
    def test_includes_original_code(self, sample_spec, sample_feedback):
        """Repair prompt includes buggy code."""
        code = "def decrement(self, amount: int) -> bool:\n    self.count -= amount\n    return True"
        prompt = PromptBuilder.build_repair_prompt(sample_spec, code, sample_feedback)
        assert "self.count -= amount" in prompt

    def test_includes_property_violated(self, sample_spec, sample_feedback):
        """Repair prompt includes violated property."""
        code = "def test(): pass"
        prompt = PromptBuilder.build_repair_prompt(sample_spec, code, sample_feedback)
        assert "non_negative" in prompt

    def test_includes_counterexample(self, sample_spec, sample_feedback):
        """Repair prompt includes counterexample values."""
        code = "def test(): pass"
        prompt = PromptBuilder.build_repair_prompt(sample_spec, code, sample_feedback)
        assert "count" in prompt
        assert "-5" in prompt

    def test_includes_execution_trace(self, sample_spec, sample_feedback):
        """Repair prompt includes execution trace."""
        code = "def test(): pass"
        prompt = PromptBuilder.build_repair_prompt(sample_spec, code, sample_feedback)
        assert "Line 2" in prompt
        assert "FAULT" in prompt

    def test_includes_root_cause(self, sample_spec, sample_feedback):
        """Repair prompt includes root cause."""
        code = "def test(): pass"
        prompt = PromptBuilder.build_repair_prompt(sample_spec, code, sample_feedback)
        assert sample_feedback.root_cause in prompt

    def test_includes_suggested_fix(self, sample_spec, sample_feedback):
        """Repair prompt includes suggested fix."""
        code = "def test(): pass"
        prompt = PromptBuilder.build_repair_prompt(sample_spec, code, sample_feedback)
        assert sample_feedback.suggested_fix in prompt


class TestBuildRawRepairPrompt:
    def test_includes_counterexample(self, sample_spec):
        """Raw repair prompt includes counterexample."""
        code = "def test(): pass"
        cx = Counterexample(
            pre_state={"count": 5},
            inputs={"amount": 10},
            post_state={"count": -5},
            output=True
        )
        prompt = PromptBuilder.build_raw_repair_prompt(sample_spec, code, cx)
        # to_dict formats as count_pre, amount, count_post, output
        assert "count_pre" in prompt
        assert "amount" in prompt
        assert "count_post" in prompt

    def test_no_structured_feedback(self, sample_spec):
        """Raw repair prompt does not include structured feedback."""
        code = "def test(): pass"
        cx = Counterexample(
            pre_state={"count": 5},
            inputs={"amount": 10},
            post_state={"count": -5},
            output=True
        )
        prompt = PromptBuilder.build_raw_repair_prompt(sample_spec, code, cx)
        # Should NOT contain CE2P-specific sections
        assert "Root Cause" not in prompt
        assert "Execution Trace" not in prompt


class TestExtractCode:
    def test_extract_from_markdown(self):
        """Extract code from markdown code block."""
        response = """Here's the implementation:

```python
def method(self, x: int) -> bool:
    if self.count >= x:
        self.count -= x
        return True
    return False
```

This should work correctly."""

        code = PromptBuilder.extract_code(response)
        assert "def method" in code
        assert "self.count >= x" in code
        assert "Here's the implementation" not in code

    def test_extract_bare_function(self):
        """Extract code when no markdown block."""
        response = """def method(self, x: int) -> bool:
    self.count -= x
    return True"""

        code = PromptBuilder.extract_code(response)
        assert "def method" in code
        assert "self.count -= x" in code

    def test_extract_strips_whitespace(self):
        """Extract code strips extra whitespace."""
        response = """
```python

def method(self, x: int) -> bool:
    return True

```
"""
        code = PromptBuilder.extract_code(response)
        assert code.startswith("def method")
        assert code.endswith("return True")

    def test_extract_handles_raw_response(self):
        """Extract handles response with no code structure."""
        response = "just some text"
        code = PromptBuilder.extract_code(response)
        assert code == "just some text"
