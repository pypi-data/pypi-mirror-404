# Problem Categories

rotalabs-verity includes 50+ pre-defined problem specifications for distributed systems primitives.

## Categories

| Category | Prefix | Description |
|----------|--------|-------------|
| [Consensus](consensus.md) | `cn` | Leader election, voting protocols |
| [Coordination](coordination.md) | `co` | Locks, semaphores, barriers |
| [Transactions](transactions.md) | `tx` | 2PC, Saga, event sourcing |
| [Circuit Breakers](circuit-breakers.md) | `cb` | Failure handling patterns |
| [Rate Limiting](rate-limiting.md) | `rl` | Throttling algorithms |
| [Replication](replication.md) | `rp` | Data replication patterns |

## Loading Problems

```python
from rotalabs_verity.problems import get_problem, list_problems

# List all problems
all_problems = list_problems()

# Load specific problem
problem = get_problem("cn001_leader_election")
```

## Problem Structure

Each problem includes:

- **name**: Unique identifier
- **description**: What the code should do
- **state_vars**: Internal state variables
- **input_vars**: Input parameters
- **output_var**: Return value specification
- **properties**: Formal properties to verify
- **examples**: Test cases for quick validation
