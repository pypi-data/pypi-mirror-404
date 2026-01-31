"""
CLI entry point for rotalabs-verify.

Usage:
    rotalabs-verify --list                    # List available problems
    rotalabs-verify RL-001                    # Synthesize solution for problem RL-001
    rotalabs-verify RL-001 --provider anthropic  # Use Anthropic instead of OpenAI
"""

import argparse
import json
import sys

from rotalabs_verity.llm.client import get_client
from rotalabs_verity.problems import get_problem, list_problems
from rotalabs_verity.synthesis.cegis import synthesize


def main():
    parser = argparse.ArgumentParser(
        description="rotalabs-verify: Verified Code Synthesis with Z3",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  rotalabs-verify --list                     List available benchmark problems
  rotalabs-verify RL-001                     Synthesize token bucket rate limiter
  rotalabs-verify RL-001 --provider anthropic   Use Claude instead of GPT-4
  rotalabs-verify RL-001 --no-ce2p           Disable structured feedback
        """
    )
    parser.add_argument("problem_id", nargs="?", help="Problem ID (e.g., RL-001)")
    parser.add_argument("--provider", default="openai", choices=["openai", "anthropic", "ollama"])
    parser.add_argument("--model", help="Model name")
    parser.add_argument("--max-iterations", type=int, default=10)
    parser.add_argument("--no-ce2p", action="store_true", help="Disable CE2P feedback")
    parser.add_argument("--output", help="Output file for results")
    parser.add_argument("--list", action="store_true", help="List available problems")

    args = parser.parse_args()

    # List problems if requested
    if args.list:
        problems = list_problems()
        if problems:
            print("Available problems:")
            for pid in sorted(problems):
                print(f"  {pid}")
        else:
            print("No problems registered. Run Phase 7 to add problems.")
        return

    # Require problem_id if not listing
    if not args.problem_id:
        parser.print_help()
        sys.exit(1)

    # Load problem
    spec = get_problem(args.problem_id)
    if spec is None:
        print(f"Unknown problem: {args.problem_id}", file=sys.stderr)
        print("Use --list to see available problems.", file=sys.stderr)
        sys.exit(1)

    # Create LLM client
    try:
        llm = get_client(args.provider, args.model)
    except ValueError as e:
        print(f"Error creating LLM client: {e}", file=sys.stderr)
        sys.exit(1)

    # Run synthesis
    print(f"Synthesizing {args.problem_id}...")
    print(f"Provider: {args.provider}")
    print(f"CE2P: {'enabled' if not args.no_ce2p else 'disabled'}")
    print()

    result = synthesize(
        spec,
        llm,
        max_iterations=args.max_iterations,
        use_ce2p=not args.no_ce2p
    )

    # Output
    print(f"Status: {result.status.value}")
    print(f"Iterations: {result.iterations}")
    print(f"Time: {result.total_time_ms:.0f}ms")

    if result.code:
        print(f"\nGenerated Code:\n{result.code}")

    if result.error_message:
        print(f"\nError: {result.error_message}")

    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump({
                "problem_id": args.problem_id,
                "status": result.status.value,
                "iterations": result.iterations,
                "time_ms": result.total_time_ms,
                "code": result.code,
                "error": result.error_message
            }, f, indent=2)
        print(f"\nResults saved to {args.output}")

    # Exit with appropriate code
    sys.exit(0 if result.status.value == "success" else 1)


if __name__ == "__main__":
    main()
