"""CE2P module - Counterexample-to-Prompt translation."""

from rotalabs_verity.ce2p.abducer import (
    RepairSuggestion,
    synthesize_repair,
)
from rotalabs_verity.ce2p.executor import (
    ConcreteExecutor,
    ExecutionTrace,
    execute_on_counterexample,
)
from rotalabs_verity.ce2p.feedback import (
    generate_feedback,
)
from rotalabs_verity.ce2p.localizer import (
    FaultLocation,
    extract_property_variables,
    localize_fault,
)

__all__ = [
    # Executor
    "ExecutionTrace",
    "ConcreteExecutor",
    "execute_on_counterexample",
    # Localizer
    "FaultLocation",
    "localize_fault",
    "extract_property_variables",
    # Abducer
    "RepairSuggestion",
    "synthesize_repair",
    # Feedback
    "generate_feedback",
]
