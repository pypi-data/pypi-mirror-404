"""Problems module - benchmark problem specifications."""

from rotalabs_verity.core import ProblemSpec

# Registry
_registry: dict[str, ProblemSpec] = {}


def register(spec: ProblemSpec) -> None:
    """Register a problem specification."""
    _registry[spec.problem_id] = spec


def get_problem(problem_id: str) -> ProblemSpec | None:
    """Get a problem by ID."""
    return _registry.get(problem_id)


def list_problems() -> list[str]:
    """List all registered problem IDs."""
    return sorted(_registry.keys())


def list_by_category(category: str) -> list[str]:
    """List problems by category."""
    return [pid for pid, spec in _registry.items() if spec.category == category]


def list_by_difficulty(difficulty: str) -> list[str]:
    """List problems by difficulty."""
    return [pid for pid, spec in _registry.items() if spec.difficulty == difficulty]


# Import and register all problems
# Rate Limiting
# Circuit Breaker
from rotalabs_verity.problems.cb import (
    cb001_circuit_breaker,
    cb002_bulkhead,
    cb003_retry_backoff,
    cb004_timeout_handler,
    cb005_health_check,
    cb006_load_shedder,
    cb007_fallback_handler,
    cb008_graceful_degradation,
)

# Consensus
from rotalabs_verity.problems.cn import (
    cn001_leader_election,
    cn002_bully_election,
    cn003_ring_election,
    cn004_raft_election,
    cn005_paxos_proposer,
    cn006_paxos_acceptor,
    cn007_view_change,
    cn008_membership,
    cn009_lease_manager,
)

# Coordination
from rotalabs_verity.problems.co import (
    co001_distributed_lock,
    co002_semaphore,
    co003_rwlock,
    co004_barrier,
    co005_countdown_latch,
    co006_phaser,
    co007_event_flag,
    co008_future,
)
from rotalabs_verity.problems.rl import (
    rl001_token_bucket,
    rl002_sliding_window,
    rl003_leaky_bucket,
    rl004_fixed_window,
    rl005_concurrent_limiter,
    rl006_adaptive_limiter,
    rl007_burst_limiter,
    rl008_quota_limiter,
)

# Replication
from rotalabs_verity.problems.rp import (
    rp001_primary_backup,
    rp002_chain_replication,
    rp003_quorum_read,
    rp004_quorum_write,
    rp005_anti_entropy,
    rp006_gossip,
    rp007_vector_clock,
    rp008_version_vector,
    rp009_read_repair,
)

# Transaction
from rotalabs_verity.problems.tx import (
    tx001_two_phase_commit,
    tx002_saga,
    tx003_outbox,
    tx004_tcc,
    tx005_idempotent,
    tx006_wal,
    tx007_compensating,
    tx008_event_sourcing,
)


def _init_registry():
    """Register all problems."""
    # Rate Limiting
    register(rl001_token_bucket.get_spec())
    register(rl002_sliding_window.get_spec())
    register(rl003_leaky_bucket.get_spec())
    register(rl004_fixed_window.get_spec())
    register(rl005_concurrent_limiter.get_spec())
    register(rl006_adaptive_limiter.get_spec())
    register(rl007_burst_limiter.get_spec())
    register(rl008_quota_limiter.get_spec())

    # Circuit Breaker
    register(cb001_circuit_breaker.get_spec())
    register(cb002_bulkhead.get_spec())
    register(cb003_retry_backoff.get_spec())
    register(cb004_timeout_handler.get_spec())
    register(cb005_health_check.get_spec())
    register(cb006_load_shedder.get_spec())
    register(cb007_fallback_handler.get_spec())
    register(cb008_graceful_degradation.get_spec())

    # Coordination
    register(co001_distributed_lock.get_spec())
    register(co002_semaphore.get_spec())
    register(co003_rwlock.get_spec())
    register(co004_barrier.get_spec())
    register(co005_countdown_latch.get_spec())
    register(co006_phaser.get_spec())
    register(co007_event_flag.get_spec())
    register(co008_future.get_spec())

    # Transaction
    register(tx001_two_phase_commit.get_spec())
    register(tx002_saga.get_spec())
    register(tx003_outbox.get_spec())
    register(tx004_tcc.get_spec())
    register(tx005_idempotent.get_spec())
    register(tx006_wal.get_spec())
    register(tx007_compensating.get_spec())
    register(tx008_event_sourcing.get_spec())

    # Consensus
    register(cn001_leader_election.get_spec())
    register(cn002_bully_election.get_spec())
    register(cn003_ring_election.get_spec())
    register(cn004_raft_election.get_spec())
    register(cn005_paxos_proposer.get_spec())
    register(cn006_paxos_acceptor.get_spec())
    register(cn007_view_change.get_spec())
    register(cn008_membership.get_spec())
    register(cn009_lease_manager.get_spec())

    # Replication
    register(rp001_primary_backup.get_spec())
    register(rp002_chain_replication.get_spec())
    register(rp003_quorum_read.get_spec())
    register(rp004_quorum_write.get_spec())
    register(rp005_anti_entropy.get_spec())
    register(rp006_gossip.get_spec())
    register(rp007_vector_clock.get_spec())
    register(rp008_version_vector.get_spec())
    register(rp009_read_repair.get_spec())


_init_registry()


__all__ = [
    "register",
    "get_problem",
    "list_problems",
    "list_by_category",
    "list_by_difficulty",
]
