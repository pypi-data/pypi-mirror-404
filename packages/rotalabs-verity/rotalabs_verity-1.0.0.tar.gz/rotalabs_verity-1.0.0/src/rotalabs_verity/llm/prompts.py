"""
Prompt construction for synthesis.
"""

import re

from rotalabs_verity.core import Counterexample, ProblemSpec, StructuredFeedback


class PromptBuilder:
    """Builds prompts for LLM synthesis."""

    @staticmethod
    def build_initial_prompt(spec: ProblemSpec) -> str:
        """Build initial synthesis prompt."""
        return f"""You are an expert Python programmer. Implement the following method.

## Task
{spec.description}

## Method Signature
```python
{spec.method_signature}
```

## State Variables
{_format_state_vars(spec)}

## Properties That Must Hold
{_format_properties(spec)}

## Examples
{_format_examples(spec)}

## Requirements
1. Implement ONLY the method body
2. Use only: assignments, if/else, while, for-range, return
3. Use only these built-ins: min, max, abs
4. Do NOT use: lists, dicts, imports, exceptions, classes

## Output
Respond with ONLY the Python method implementation, no explanation.

```python
{spec.method_signature}
    # Your implementation here
```"""

    @staticmethod
    def build_repair_prompt(
        spec: ProblemSpec,
        code: str,
        feedback: StructuredFeedback
    ) -> str:
        """Build repair prompt with CE2P feedback."""
        return f"""Your previous implementation has a bug. Fix it based on the feedback below.

## Original Task
{spec.description}

## Your Previous Code
```python
{code}
```

## Verification Failed
{_format_feedback(feedback)}

## Requirements
1. Fix the bug identified above
2. Keep the same method signature
3. Use only: assignments, if/else, while, for-range, return
4. Use only these built-ins: min, max, abs

## Output
Respond with ONLY the fixed Python method, no explanation.

```python
{spec.method_signature}
    # Your fixed implementation
```"""

    @staticmethod
    def build_raw_repair_prompt(
        spec: ProblemSpec,
        code: str,
        counterexample: Counterexample
    ) -> str:
        """Build repair prompt with raw counterexample (baseline)."""
        return f"""Your previous implementation has a bug. Fix it.

## Original Task
{spec.description}

## Your Previous Code
```python
{code}
```

## Counterexample Found
The following inputs cause a property violation:
{_format_counterexample(counterexample)}

## Requirements
1. Fix the bug
2. Keep the same method signature

## Output
Respond with ONLY the fixed Python method, no explanation.

```python
{spec.method_signature}
    # Your fixed implementation
```"""

    @staticmethod
    def build_ablation_repair_prompt(
        spec: ProblemSpec,
        code: str,
        feedback: StructuredFeedback,
        ablation: str
    ) -> str:
        """Build repair prompt with ablated CE2P feedback.

        Ablation conditions:
        - full: Everything (current CE2P behavior)
        - no_fix: Remove suggested fix
        - no_trace: Remove execution trace
        - no_root_cause: Remove root cause analysis
        - values_only: Structured values, no analysis (isolates formatting from analysis)
        """
        return f"""Your previous implementation has a bug. Fix it based on the feedback below.

## Original Task
{spec.description}

## Your Previous Code
```python
{code}
```

## Verification Failed
{_format_ablation_feedback(feedback, ablation)}

## Requirements
1. Fix the bug identified above
2. Keep the same method signature
3. Use only: assignments, if/else, while, for-range, return
4. Use only these built-ins: min, max, abs

## Output
Respond with ONLY the fixed Python method, no explanation.

```python
{spec.method_signature}
    # Your fixed implementation
```"""

    @staticmethod
    def extract_code(response: str) -> str:
        """Extract Python code from LLM response."""
        # Try to find code block
        code_match = re.search(r'```python\s*(.*?)\s*```', response, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()

        # Try to find def statement
        def_match = re.search(r'(def\s+\w+\s*\([^)]*\).*)', response, re.DOTALL)
        if def_match:
            return def_match.group(1).strip()

        # Return as-is
        return response.strip()


def _format_state_vars(spec: ProblemSpec) -> str:
    """Format state variables for prompt."""
    lines = []
    for sv in spec.state_variables:
        bounds = f" (range: {sv.bounds[0]} to {sv.bounds[1]})" if sv.bounds else ""
        lines.append(f"- self.{sv.name} ({sv.var_type}): {sv.description}{bounds}")
    return "\n".join(lines)


def _format_properties(spec: ProblemSpec) -> str:
    """Format properties for prompt."""
    lines = []
    for p in spec.properties:
        lines.append(f"- {p.name}: {p.description}")
        lines.append(f"  Formula: {p.formula}")
    return "\n".join(lines)


def _format_examples(spec: ProblemSpec) -> str:
    """Format examples for prompt."""
    if not spec.examples:
        return "(No examples provided)"

    lines = []
    for ex in spec.examples:
        lines.append(f"### {ex.name}")
        lines.append(f"Initial state: {ex.pre_state}")
        lines.append(f"Input: {ex.inputs}")
        lines.append(f"Expected output: {ex.expected_output}")
        lines.append(f"Expected state after: {ex.expected_post_state}")
        lines.append("")
    return "\n".join(lines)


def _format_feedback(feedback: StructuredFeedback) -> str:
    """Format CE2P feedback for prompt."""
    lines = [
        "### Property Violated",
        f"Name: {feedback.property_violated.property_name}",
        f"Description: {feedback.property_violated.property_description}",
        f"Formula: {feedback.property_violated.property_formula}",
        "",
        "### Counterexample",
    ]

    cx = feedback.counterexample
    lines.append(f"Pre-state: {cx.pre_state}")
    lines.append(f"Inputs: {cx.inputs}")
    lines.append(f"Post-state: {cx.post_state}")
    lines.append(f"Output: {cx.output}")

    lines.extend([
        "",
        "### Execution Trace",
    ])

    for step in feedback.execution_trace:
        marker = " <-- FAULT" if step.is_fault else ""
        lines.append(f"Line {step.line_number}: {step.source_code}{marker}")

    lines.extend([
        "",
        "### Root Cause",
        feedback.root_cause,
        "",
        "### Suggested Fix",
        feedback.suggested_fix,
    ])

    return "\n".join(lines)


def _format_counterexample(cx: Counterexample) -> str:
    """Format raw counterexample."""
    lines = []
    for k, v in cx.to_dict().items():
        lines.append(f"- {k}: {v}")
    return "\n".join(lines)


def _format_ablation_feedback(feedback: StructuredFeedback, ablation: str) -> str:
    """Format CE2P feedback with ablation.

    Ablation conditions:
    - full: Everything (current CE2P behavior)
    - no_fix: Remove suggested fix
    - no_trace: Remove execution trace
    - no_root_cause: Remove root cause analysis
    - values_only: Structured values, no analysis
    - raw: Only bare counterexample values (no property info, no formatting)
    """
    lines = []

    # Raw condition: only show counterexample values, nothing else
    if ablation == "raw":
        cx = feedback.counterexample
        lines.extend([
            "### Counterexample",
            f"Pre-state: {cx.pre_state}",
            f"Inputs: {cx.inputs}",
            f"Post-state: {cx.post_state}",
            f"Output: {cx.output}",
        ])
        return "\n".join(lines)

    # Property violated (always included except raw)
    lines.extend([
        "### Property Violated",
        f"Name: {feedback.property_violated.property_name}",
        f"Description: {feedback.property_violated.property_description}",
        f"Formula: {feedback.property_violated.property_formula}",
        "",
    ])

    # Counterexample values (always included)
    cx = feedback.counterexample
    lines.extend([
        "### Counterexample",
        f"Pre-state: {cx.pre_state}",
        f"Inputs: {cx.inputs}",
        f"Post-state: {cx.post_state}",
        f"Output: {cx.output}",
        "",
    ])

    # Execution trace (skip if no_trace or values_only)
    if ablation not in ("no_trace", "values_only"):
        lines.append("### Execution Trace")
        for step in feedback.execution_trace:
            marker = " <-- FAULT" if step.is_fault else ""
            lines.append(f"Line {step.line_number}: {step.source_code}{marker}")
        lines.append("")

    # Root cause (skip if no_root_cause or values_only)
    if ablation not in ("no_root_cause", "values_only"):
        lines.extend([
            "### Root Cause",
            feedback.root_cause,
            "",
        ])

    # Suggested fix (skip if no_fix or values_only)
    if ablation not in ("no_fix", "values_only"):
        lines.extend([
            "### Suggested Fix",
            feedback.suggested_fix,
        ])

    return "\n".join(lines)
