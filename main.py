"""
Main entry point for LLM Coding Agent Evaluation Framework.

This module orchestrates the evaluation of LLM coding agents using the HumanEval benchmark.
Evaluates agents across three dimensions:
1. Correctness - pass@1 against HumanEval tests
2. Explainability - confidence level and explanation presence
3. Design adherence - 6 design principles
"""

import argparse

from evaluation_runner import EvaluationRunner


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Evaluate LLM coding agents on HumanEval benchmark"
    )
    parser.add_argument(
        "--task-id",
        type=int,
        default=0,
        help="Task ID to evaluate (default: 0)"
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Run batch evaluation on multiple tasks"
    )
    parser.add_argument(
        "--start-id",
        type=int,
        default=0,
        help="Starting task ID for batch evaluation (default: 0)"
    )
    parser.add_argument(
        "--end-id",
        type=int,
        default=5,
        help="Ending task ID for batch evaluation (default: 5)"
    )

    args = parser.parse_args()

    try:
        # Initialize the evaluation runner
        runner = EvaluationRunner()

        if args.batch:
            # Run batch evaluation
            print(f"\nRunning batch evaluation from task {args.start_id} to {args.end_id-1}")
            runner.run_batch_evaluation(args.start_id, args.end_id)
        else:
            # Run single task evaluation
            runner.run_single_evaluation(args.task_id)

    except Exception as e:
        print(f"Error during evaluation: {e}")
        raise


if __name__ == "__main__":
    main()
