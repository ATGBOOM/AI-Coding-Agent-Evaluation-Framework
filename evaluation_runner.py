"""
Evaluation runner for LLM coding agent evaluation.

Handles the orchestration of loading problems, generating solutions,
and comparing results against canonical solutions.
"""

import os
from typing import Dict, Optional
from dotenv import load_dotenv

from dataset.humanEvalDataset import HumanEvalDataset
from utils.llm_client import GroqClient


class EvaluationRunner:
    """Orchestrates the evaluation of LLM coding agents."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the evaluation runner.

        Args:
            api_key: Groq API key (if None, loads from environment)
        """
        load_dotenv()

        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment or provided")

        self.dataset = HumanEvalDataset()
        self.llm_client = GroqClient(
            api_key=self.api_key,
            model=os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile'),
            temperature=float(os.getenv('GROQ_TEMPERATURE', '0.1')),
            max_tokens=int(os.getenv('GROQ_MAX_TOKENS', '2048'))
        )
        self.llm_client.initialize()

    def generate_solution(self, task_id: int) -> Dict[str, str]:
        """
        Generate a solution for a given task.

        Args:
            task_id: The task ID to generate a solution for

        Returns:
            Dictionary containing task info, LLM response, and canonical solution
        """
        problem = self.dataset.getSingleProblem(task_id)
        prompt = problem['prompt']

        # Create a clear instruction for the LLM
        instruction = (
            f"Complete the following Python function. "
            f"Only provide the implementation code, no explanations:\n\n{prompt}"
        )

        # Generate solution using LLM
        llm_response = self.llm_client.generate_with_retry(instruction)

        return {
            'task_id': task_id,
            'prompt': prompt,
            'llm_solution': llm_response,
            'canonical_solution': problem['canonical_solution'],
            'entry_point': problem['entry_point'],
            'test': problem['test']
        }

    def format_result(self, result: Dict[str, str]) -> str:
        """
        Format evaluation result for display.

        Args:
            result: Dictionary containing evaluation result

        Returns:
            Formatted string for display
        """
        separator = "=" * 80

        formatted = f"""
{separator}
TASK ID: {result['task_id']}
{separator}

PROBLEM PROMPT:
{result['prompt']}

{separator}
LLM GENERATED SOLUTION:
{separator}
{result['llm_solution']}

{separator}
CANONICAL SOLUTION:
{separator}
{result['canonical_solution']}

{separator}
"""
        return formatted

    def run_single_evaluation(self, task_id: int = 0) -> None:
        """
        Run evaluation on a single task and display results.

        Args:
            task_id: The task ID to evaluate (default: 0)
        """
        print(f"\nRunning evaluation for task {task_id}...")
        result = self.generate_solution(task_id)
        print(self.format_result(result))

    def run_batch_evaluation(self, start_id: int = 0, end_id: int = 5) -> None:
        """
        Run evaluation on multiple tasks.

        Args:
            start_id: Starting task ID
            end_id: Ending task ID (exclusive)
        """
        results = []

        for task_id in range(start_id, end_id):
            print(f"\nEvaluating task {task_id}...")
            try:
                result = self.generate_solution(task_id)
                results.append(result)
                print(self.format_result(result))
            except Exception as e:
                print(f"Error evaluating task {task_id}: {e}")

        return results
