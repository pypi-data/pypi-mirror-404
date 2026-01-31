"""Core types for Verity."""

from rotalabs_verity.core.problem import (
    Example,
    InputVariable,
    ProblemSpec,
    Property,
    StateVariable,
)
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

__all__ = [
    # Verification
    "VerificationStatus",
    "Counterexample",
    "PropertyViolation",
    "VerificationResult",
    # Synthesis
    "SynthesisStatus",
    "SynthesisResult",
    # CE2P
    "TraceStep",
    "StructuredFeedback",
    # Problem
    "StateVariable",
    "InputVariable",
    "Property",
    "Example",
    "ProblemSpec",
]
