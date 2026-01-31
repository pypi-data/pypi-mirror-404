"""
rotalabs-verify: Verified code synthesis with Z3.

Formally verify LLM-generated code using neuro-symbolic synthesis with
Z3 SMT solver. Implements the CEGIS (Counterexample-Guided Inductive Synthesis)
loop with CE2P (Counterexample-to-Program) feedback.

Basic usage:
    ```python
    from rotalabs_verity import verify, ProblemSpec, VerificationStatus

    # Verify code against a specification
    result = verify(code, spec)
    if result.status == VerificationStatus.VERIFIED:
        print("Code is correct!")
    elif result.status == VerificationStatus.COUNTEREXAMPLE:
        print(f"Found bug: {result.counterexample}")
    ```

With LLM synthesis:
    ```python
    from rotalabs_verity import synthesize, CEGISSynthesizer
    from rotalabs_verity.llm import OpenAIClient

    llm = OpenAIClient(model="gpt-4")
    result = synthesize(spec, llm)
    if result.status == SynthesisStatus.SUCCESS:
        print(f"Generated verified code:\\n{result.code}")
    ```
"""

from rotalabs_verity._version import __version__

# CE2P Feedback
from rotalabs_verity.ce2p.feedback import generate_feedback
from rotalabs_verity.core.problem import (
    Example,
    InputVariable,
    ProblemSpec,
    Property,
    StateVariable,
)
from rotalabs_verity.core.python_subset import SubsetValidator, SubsetViolation

# Core types
from rotalabs_verity.core.types import (
    Counterexample,
    PropertyViolation,
    StructuredFeedback,
    SynthesisResult,
    SynthesisStatus,
    TraceStep,
    VerificationResult,
    VerificationStatus,
)
from rotalabs_verity.encoder.parser import ParseError
from rotalabs_verity.encoder.symbolic import EncodingError

# Encoder
from rotalabs_verity.encoder.z3_encoder import (
    EncodingResult,
    encode_method,
    encode_with_bounds,
)

# Synthesis
from rotalabs_verity.synthesis.cegis import (
    CEGISConfig,
    CEGISState,
    CEGISSynthesizer,
    synthesize,
)

# Verifier
from rotalabs_verity.verifier.verifier import verify, verify_with_trace

__all__ = [
    # Version
    "__version__",
    # Core types - verification
    "VerificationStatus",
    "SynthesisStatus",
    "Counterexample",
    "PropertyViolation",
    "VerificationResult",
    "SynthesisResult",
    "TraceStep",
    "StructuredFeedback",
    # Core types - problem specification
    "StateVariable",
    "InputVariable",
    "Property",
    "Example",
    "ProblemSpec",
    # Subset validation
    "SubsetValidator",
    "SubsetViolation",
    # Encoder
    "EncodingResult",
    "encode_method",
    "encode_with_bounds",
    "ParseError",
    "EncodingError",
    # Verifier
    "verify",
    "verify_with_trace",
    # CE2P
    "generate_feedback",
    # Synthesis
    "CEGISConfig",
    "CEGISState",
    "CEGISSynthesizer",
    "synthesize",
]
