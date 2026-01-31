# rotalabs-verity

Verified code synthesis with Z3 - Formally verify LLM-generated code using neuro-symbolic synthesis.

## Overview

rotalabs-verity implements the CEGIS (Counterexample-Guided Inductive Synthesis) loop with CE2P (Counterexample-to-Program) feedback to formally verify LLM-generated code using the Z3 SMT solver.

## Key Features

- **Formal Verification**: Use Z3 SMT solver to prove code correctness
- **CEGIS Loop**: Iterative synthesis with counterexample-guided refinement
- **CE2P Feedback**: Structured feedback from counterexamples to guide LLM repair
- **Multi-LLM Support**: OpenAI, Anthropic, and Ollama backends
- **50+ Problem Specs**: Distributed systems primitives ready to verify

## Architecture

```
┌─────────────────┐     ┌──────────────────┐
│   LLM Client    │────▶│  Code Generator  │
└─────────────────┘     └────────┬─────────┘
                                 │
                                 ▼
┌─────────────────┐     ┌──────────────────┐
│  Z3 Encoder     │◀────│   Python AST     │
└────────┬────────┘     └──────────────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│   Verifier      │────▶│ VerificationResult│
└────────┬────────┘     └──────────────────┘
         │
    counterexample?
         │
         ▼
┌─────────────────┐
│  CE2P Feedback  │─────▶ back to LLM
└─────────────────┘
```

## Installation

```bash
pip install rotalabs-verity

# With LLM backends
pip install rotalabs-verity[llm]

# With Ollama
pip install rotalabs-verity[ollama]
```

## Quick Start

```python
from rotalabs_verity import verify, ProblemSpec, VerificationStatus

# Define specification
spec = ProblemSpec(
    name="absolute_value",
    description="Return the absolute value of x",
    input_vars=[InputVariable("x", "int")],
    output_var=StateVariable("result", "int"),
    properties=[
        Property("result >= 0", "Result is non-negative"),
        Property("result == x or result == -x", "Result is x or -x"),
    ],
)

# Verify code
code = '''
def absolute_value(x):
    if x < 0:
        return -x
    return x
'''

result = verify(code, spec)
if result.status == VerificationStatus.VERIFIED:
    print("Code is correct!")
```

## Problem Categories

The package includes 50+ pre-defined problem specifications across categories:

| Category | Prefix | Examples |
|----------|--------|----------|
| Consensus | `cn` | Leader election, Paxos, Raft |
| Coordination | `co` | Locks, semaphores, barriers |
| Transactions | `tx` | 2PC, Saga, Outbox |
| Circuit Breakers | `cb` | Breaker, bulkhead, retry |
| Rate Limiting | `rl` | Token bucket, sliding window |
| Replication | `rp` | Primary-backup, quorum |
