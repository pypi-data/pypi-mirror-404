"""
Core types for Verity.

This module contains ONLY shared data structures.
No logic, no Z3, no parsing - just dataclasses and enums.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# =============================================================================
# Verification Results
# =============================================================================

class VerificationStatus(Enum):
    """Result of verification."""
    VERIFIED = "verified"              # Code satisfies all properties
    COUNTEREXAMPLE = "counterexample"  # Found inputs that violate property
    UNKNOWN = "unknown"                # Solver couldn't decide (timeout, etc.)
    ENCODING_ERROR = "encoding_error"  # Code couldn't be encoded to Z3
    PARSE_ERROR = "parse_error"        # Code couldn't be parsed


@dataclass(frozen=True)
class Counterexample:
    """
    Concrete values that violate a property.

    All values are Python primitives (int, float, bool, str).
    """
    pre_state: dict[str, Any]      # State before execution (self.x values)
    inputs: dict[str, Any]         # Method inputs
    post_state: dict[str, Any]     # State after execution
    output: Any                    # Return value

    def to_dict(self) -> dict[str, Any]:
        """Flatten to single dict for prompts."""
        result = {}
        for k, v in self.pre_state.items():
            result[f"{k}_pre"] = v
        for k, v in self.inputs.items():
            result[k] = v
        for k, v in self.post_state.items():
            result[f"{k}_post"] = v
        result["output"] = self.output
        return result


@dataclass(frozen=True)
class PropertyViolation:
    """Details of which property was violated."""
    property_name: str
    property_description: str
    property_formula: str  # Human-readable (e.g., "□(tokens >= 0)")


@dataclass
class VerificationResult:
    """Complete result of verification."""
    status: VerificationStatus
    property_violated: PropertyViolation | None = None
    counterexample: Counterexample | None = None
    error_message: str | None = None
    verification_time_ms: float = 0.0


# =============================================================================
# Synthesis Results
# =============================================================================

class SynthesisStatus(Enum):
    """Result of synthesis attempt."""
    SUCCESS = "success"       # Found verified implementation
    FAILED = "failed"         # Exhausted attempts without success
    TIMEOUT = "timeout"       # Exceeded time limit
    ERROR = "error"           # System error


@dataclass
class SynthesisResult:
    """Complete result of synthesis."""
    status: SynthesisStatus
    code: str | None = None         # Final code (if successful)
    iterations: int = 0             # Number of CEGIS iterations
    total_time_ms: float = 0.0
    verification_results: list[VerificationResult] = field(default_factory=list)
    error_message: str | None = None


# =============================================================================
# CE2P Feedback
# =============================================================================

@dataclass
class TraceStep:
    """Single step in execution trace."""
    line_number: int
    source_code: str
    state_before: dict[str, Any]
    state_after: dict[str, Any]
    is_fault: bool = False


@dataclass
class StructuredFeedback:
    """
    CE2P output: structured feedback for LLM.

    All fields are derived algorithmically - no templates.
    """
    property_violated: PropertyViolation
    counterexample: Counterexample
    execution_trace: list[TraceStep]
    fault_line: int
    root_cause: str          # Generated from trace analysis
    suggested_fix: str       # Generated from abductive repair
    repair_guard: str        # The condition that should be checked
