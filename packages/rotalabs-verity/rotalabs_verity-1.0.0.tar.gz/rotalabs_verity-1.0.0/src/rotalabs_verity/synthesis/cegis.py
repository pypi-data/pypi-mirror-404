"""
CEGIS synthesis loop.
"""

import time
from dataclasses import dataclass, field

from rotalabs_verity.ce2p import generate_feedback
from rotalabs_verity.core import (
    ProblemSpec,
    SynthesisResult,
    SynthesisStatus,
    VerificationResult,
    VerificationStatus,
)
from rotalabs_verity.llm.client import LLMClient
from rotalabs_verity.llm.prompts import PromptBuilder
from rotalabs_verity.verifier import verify


@dataclass
class CEGISConfig:
    """Configuration for CEGIS loop."""
    max_iterations: int = 10
    verification_timeout_ms: int = 30000
    use_ce2p: bool = True  # Use structured feedback (vs raw counterexample)


@dataclass
class CEGISState:
    """State during synthesis."""
    iteration: int = 0
    current_code: str = ""
    verification_results: list[VerificationResult] = field(default_factory=list)
    prompts: list[str] = field(default_factory=list)
    responses: list[str] = field(default_factory=list)


class CEGISSynthesizer:
    """
    CEGIS-based program synthesizer.

    Uses LLM for candidate generation and Z3 for verification.
    CE2P translates counterexamples to structured feedback.
    """

    def __init__(self, llm: LLMClient, config: CEGISConfig | None = None):
        self.llm = llm
        self.config = config or CEGISConfig()

    def synthesize(self, spec: ProblemSpec) -> SynthesisResult:
        """
        Synthesize verified implementation.

        Args:
            spec: Problem specification

        Returns:
            SynthesisResult with status and code
        """
        start_time = time.time()
        state = CEGISState()

        try:
            # Step 1: Initial generation
            initial_prompt = PromptBuilder.build_initial_prompt(spec)
            state.prompts.append(initial_prompt)

            response = self.llm.generate(initial_prompt)
            state.responses.append(response.content)

            state.current_code = PromptBuilder.extract_code(response.content)

            # Step 2: CEGIS loop
            for iteration in range(self.config.max_iterations):
                state.iteration = iteration + 1

                # Verify
                result = verify(
                    state.current_code,
                    spec,
                    timeout_ms=self.config.verification_timeout_ms
                )
                state.verification_results.append(result)

                # Check result
                if result.status == VerificationStatus.VERIFIED:
                    return SynthesisResult(
                        status=SynthesisStatus.SUCCESS,
                        code=state.current_code,
                        iterations=state.iteration,
                        total_time_ms=(time.time() - start_time) * 1000,
                        verification_results=state.verification_results
                    )

                if result.status == VerificationStatus.COUNTEREXAMPLE:
                    # Generate repair prompt
                    if self.config.use_ce2p:
                        feedback = generate_feedback(state.current_code, result, spec=spec)
                        prompt = PromptBuilder.build_repair_prompt(
                            spec, state.current_code, feedback
                        )
                    else:
                        prompt = PromptBuilder.build_raw_repair_prompt(
                            spec, state.current_code, result.counterexample
                        )

                    state.prompts.append(prompt)

                    # Get repair
                    response = self.llm.generate(prompt)
                    state.responses.append(response.content)

                    state.current_code = PromptBuilder.extract_code(response.content)

                elif result.status in (VerificationStatus.ENCODING_ERROR,
                                       VerificationStatus.PARSE_ERROR):
                    # Code couldn't be verified - ask for simpler implementation
                    prompt = self._build_simplify_prompt(spec, state.current_code, result)
                    state.prompts.append(prompt)

                    response = self.llm.generate(prompt)
                    state.responses.append(response.content)

                    state.current_code = PromptBuilder.extract_code(response.content)

                else:
                    # Unknown or timeout
                    return SynthesisResult(
                        status=SynthesisStatus.ERROR,
                        iterations=state.iteration,
                        total_time_ms=(time.time() - start_time) * 1000,
                        verification_results=state.verification_results,
                        error_message=result.error_message
                    )

            # Max iterations exceeded
            return SynthesisResult(
                status=SynthesisStatus.FAILED,
                code=state.current_code,
                iterations=state.iteration,
                total_time_ms=(time.time() - start_time) * 1000,
                verification_results=state.verification_results,
                error_message=f"Failed to synthesize after {self.config.max_iterations} iterations"
            )

        except Exception as e:
            return SynthesisResult(
                status=SynthesisStatus.ERROR,
                iterations=state.iteration,
                total_time_ms=(time.time() - start_time) * 1000,
                verification_results=state.verification_results,
                error_message=str(e)
            )

    def _build_simplify_prompt(
        self,
        spec: ProblemSpec,
        code: str,
        result: VerificationResult
    ) -> str:
        """Build prompt asking for simpler code."""
        return f"""Your code cannot be verified because it uses unsupported features.

## Error
{result.error_message}

## Your Code
```python
{code}
```

## Requirements
You must use ONLY these Python features:
- Simple assignments: x = expr, self.x = expr
- Augmented assignments: x += expr, x -= expr
- Conditionals: if/elif/else
- Loops: while, for x in range(n)
- Returns: return expr
- Built-ins: min, max, abs

Do NOT use:
- Lists, dicts, sets
- Imports
- Exceptions (try/except)
- Classes
- List comprehensions
- Lambda functions

## Task
{spec.description}

## Output
Respond with ONLY the simplified Python method.

```python
{spec.method_signature}
    # Your simplified implementation
```"""


def synthesize(
    spec: ProblemSpec,
    llm: LLMClient,
    max_iterations: int = 10,
    use_ce2p: bool = True
) -> SynthesisResult:
    """
    Convenience function for synthesis.

    Args:
        spec: Problem specification
        llm: LLM client
        max_iterations: Maximum CEGIS iterations
        use_ce2p: Use structured feedback (vs raw counterexample)

    Returns:
        SynthesisResult
    """
    config = CEGISConfig(max_iterations=max_iterations, use_ce2p=use_ce2p)
    synthesizer = CEGISSynthesizer(llm, config)
    return synthesizer.synthesize(spec)
