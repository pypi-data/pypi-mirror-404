# Getting Started

## Installation

```bash
# Core package (verification only)
pip install rotalabs-verity

# With OpenAI/Anthropic for synthesis
pip install rotalabs-verity[llm]

# With Ollama for local models
pip install rotalabs-verity[ollama]

# Everything
pip install rotalabs-verity[all]
```

## Basic Verification

Verify code against a formal specification:

```python
from rotalabs_verity import (
    verify,
    ProblemSpec,
    InputVariable,
    StateVariable,
    Property,
    VerificationStatus,
)

# Define the problem specification
spec = ProblemSpec(
    name="max_of_two",
    description="Return the maximum of two integers",
    input_vars=[
        InputVariable("a", "int"),
        InputVariable("b", "int"),
    ],
    output_var=StateVariable("result", "int"),
    properties=[
        Property("result >= a", "Result >= first input"),
        Property("result >= b", "Result >= second input"),
        Property("result == a or result == b", "Result is one of the inputs"),
    ],
)

# Code to verify
code = '''
def max_of_two(a, b):
    if a >= b:
        return a
    return b
'''

# Run verification
result = verify(code, spec)

if result.status == VerificationStatus.VERIFIED:
    print("All properties verified!")
elif result.status == VerificationStatus.COUNTEREXAMPLE:
    print(f"Found counterexample: {result.counterexample}")
```

## CEGIS Synthesis

Automatically synthesize verified code using LLMs:

```python
from rotalabs_verity import synthesize, CEGISSynthesizer, CEGISConfig
from rotalabs_verity.llm import OpenAIClient

# Initialize LLM client
llm = OpenAIClient(model="gpt-4")

# Configure CEGIS
config = CEGISConfig(
    max_iterations=10,
    timeout_seconds=60,
)

# Synthesize verified code
result = synthesize(spec, llm, config=config)

if result.verified:
    print(f"Generated verified code:\n{result.code}")
    print(f"Iterations: {result.iterations}")
```

## Using Pre-defined Problems

Load and use built-in problem specifications:

```python
from rotalabs_verity.problems import get_problem, list_problems

# List all available problems
for category, problems in list_problems().items():
    print(f"{category}: {problems}")

# Load a specific problem
problem = get_problem("cn001_leader_election")
print(problem.description)
print(problem.properties)
```

## Understanding Counterexamples

When verification fails, you get a structured counterexample:

```python
from rotalabs_verity import verify_with_trace

result = verify_with_trace(code, spec)

if result.counterexample:
    ce = result.counterexample
    print(f"Input values: {ce.inputs}")
    print(f"Expected output: {ce.expected}")
    print(f"Actual output: {ce.actual}")

    # Execution trace
    for step in result.trace:
        print(f"Line {step.line}: {step.statement}")
        print(f"  State: {step.state}")
```

## CE2P Feedback

Generate structured feedback from counterexamples to guide LLM repair:

```python
from rotalabs_verity import generate_feedback

feedback = generate_feedback(result, spec)
print(feedback.explanation)
print(feedback.suggested_fix)
print(feedback.localized_error)
```
