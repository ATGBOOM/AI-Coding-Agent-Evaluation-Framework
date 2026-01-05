"""
Evaluation runner for LLM coding agent evaluation.

Handles the orchestration of loading problems, generating solutions,
and comparing results against canonical solutions.
"""

import os
from typing import Dict, Optional, List
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from dataset.humanEvalDataset import HumanEvalDataset
from models.llm_response import LLMSolutionResponse
from utils.test_executor import TestExecutor, TestResult
from evaluators.correctness import CorrectnessEvaluator, CorrectnessResult
from evaluators.explainability import ExplainabilityEvaluator


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

        # Initialize LangChain ChatGroq with structured output
        self.llm = ChatGroq(
            api_key=self.api_key,
            model=os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile'),
            temperature=float(os.getenv('GROQ_TEMPERATURE', '0.1')),
            max_tokens=int(os.getenv('GROQ_MAX_TOKENS', '2048'))
        )

        # Create structured output chain
        self.structured_llm = self.llm.with_structured_output(LLMSolutionResponse)

        # Initialize test executor
        self.test_executor = TestExecutor(timeout=5)

        # Initialize correctness evaluator
        self.correctness_evaluator = CorrectnessEvaluator(timeout=5)

        # Initialize explainability evaluator
        self.explainability_evaluator = ExplainabilityEvaluator()

    def generate_solution(self, task_id: int) -> Dict:
        """
        Generate a solution for a given task.

        Args:
            task_id: The task ID to generate a solution for

        Returns:
            Dictionary containing task info, LLM response, and canonical solution
        """
        problem = self.dataset.getSingleProblem(task_id)
        prompt_text = problem['prompt']

        # Create a comprehensive prompt that follows design principles
        design_principles = """
Design Principles to Follow:
1. Descriptive Naming: Use clear, descriptive variable and function names
2. Single Responsibility: Each function should do one thing well
3. Small Functions: Keep functions under 15 lines
4. Test-Driven Development: Write test cases for your solution
5. Logging Ready: Never use print() statements; use proper logging or return values
6. Edge Cases: Handle edge cases with proper validation and error handling
"""

        # Create the prompt template
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are an expert Python developer who writes clean, well-tested code following best practices."),
            ("user", """Complete the following Python coding task.

{design_principles}

Problem:
{problem_prompt}

Provide your solution with:
1. A brief line of thought explaining your approach
2. Your confidence level (High, Medium, or Low)
3. The complete solution code following all design principles
4. Test cases to validate the solution (using assert statements)
5. An explanation of your solution, covering algorithm choice, key variables/functions, constraints and assumptions, and edge case consideration
""")
        ])

        # Format the prompt
        formatted_prompt = prompt_template.format_messages(
            design_principles=design_principles,
            problem_prompt=prompt_text
        )

        # Generate structured response
        response: LLMSolutionResponse = self.structured_llm.invoke(formatted_prompt)

        # Run canonical solution against test cases to validate tests
        print("\nValidating canonical solution against test cases...")
        canonical_result = self.test_executor.validate_canonical_solution(
            canonical_solution=problem['canonical_solution'],
            test_code=problem['test'],
            entry_point=problem['entry_point'],
            prompt=prompt_text
        )

        # Evaluate LLM solution correctness against dataset test cases
        print("Evaluating LLM solution against dataset test cases...")
        llm_correctness_result = self.correctness_evaluator.evaluate(
            solution_code=response.solution,
            test_code=problem['test'],
            entry_point=problem['entry_point']
        )

        # For backwards compatibility, keep the original test result
        llm_dataset_result = llm_correctness_result.test_result

        # Evaluate LLM solution against LLM-generated test cases
        llm_tests_result = None
        llm_tests_correctness = None
        if response.test_cases:
            print("Evaluating LLM solution against LLM-generated test cases...")
            llm_tests_correctness = self.correctness_evaluator.evaluate_with_llm_tests(
                solution_code=response.solution,
                llm_test_cases=response.test_cases
            )
            llm_tests_result = llm_tests_correctness.test_result

        # Evaluate explainability
        explainability_result = self.explainability_evaluator.evaluate(
            thought=response.thought,
            confidence=response.confidence,
            completeness=response.completeness
        )

        return {
            'task_id': task_id,
            'prompt': prompt_text,
            'llm_solution': response.solution,
            'test_cases': response.test_cases,
            'canonical_solution': problem['canonical_solution'],
            'entry_point': problem['entry_point'],
            'test': problem['test'],
            'canonical_test_result': canonical_result,
            'llm_dataset_test_result': llm_dataset_result,
            'llm_tests_result': llm_tests_result,
            'correctness_result': llm_correctness_result,
            'llm_tests_correctness': llm_tests_correctness,
            'explainability_result': explainability_result 
        }

    def format_result(self, result: Dict) -> str:
        """
        Format evaluation result for display.

        Args:
            result: Dictionary containing evaluation result

        Returns:
            Formatted string for display
        """
        separator = "=" * 80

        # Format correctness metrics
        def format_correctness(correctness: Optional[CorrectnessResult]) -> str:
            if not correctness:
                return "  Not evaluated"

            status = "✓ PASSED" if correctness.passed else "✗ FAILED"
            result_str = f"  Status: {status}\n"
            result_str += f"  Tests Passed: {correctness.num_passed}/{correctness.total_tests}\n"
            result_str += f"  Test Pass Rate: {correctness.test_pass_rate:.2f}%\n"
            result_str += f"  Pass@1: {correctness.pass_at_1:.2f}"

            if not correctness.passed and correctness.errors:
                result_str += f"\n  Errors: {'; '.join(correctness.errors[:2])}"  # Show first 2 errors

            if correctness.test_result and correctness.test_result.timeout:
                result_str += "\n  (Execution timed out)"

            return result_str

        formatted = f"""
{separator}
TASK ID: {result['task_id']}
{separator}

PROBLEM PROMPT:
{result['prompt']}

{separator}
EXPLAINABILITY
{separator}
Line of Thought: {result['thought']}
Confidence Level: {result['confidence']}

{separator}
CORRECTNESS METRICS
{separator}
Dataset Test Correctness:
{format_correctness(result.get('correctness_result'))}

LLM-Generated Test Correctness:
{format_correctness(result.get('llm_tests_correctness'))}

Canonical Solution Validation:
  Status: {'✓ PASSED' if result.get('canonical_test_result') and result['canonical_test_result'].passed else '✗ FAILED' if result.get('canonical_test_result') else 'Not run'}

{separator}
LLM GENERATED SOLUTION:
{separator}
{result['llm_solution']}

{separator}
LLM GENERATED TEST CASES:
{separator}
{result['test_cases'] if result['test_cases'] else 'No test cases provided'}

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

    def run_batch_evaluation(self, start_id: int = 0, end_id: int = 164) -> List[Dict]:
        """
        Run evaluation on multiple tasks and aggregate correctness metrics.

        Args:
            start_id: Starting task ID
            end_id: Ending task ID (exclusive)

        Returns:
            List of evaluation results
        """
        results = []
        correctness_results = []

        for task_id in range(start_id, end_id):
            print(f"\nEvaluating task {task_id}...")
            try:
                result = self.generate_solution(task_id)
                results.append(result)
                print(self.format_result(result))

                # Collect correctness results for aggregation
                if result.get('correctness_result'):
                    correctness_results.append(result['correctness_result'])

            except Exception as e:
                print(f"Error evaluating task {task_id}: {e}")

        # Aggregate and display correctness metrics
        if correctness_results:
            print("\n" + "=" * 80)
            print("BATCH EVALUATION COMPLETE")
            print("=" * 80)

            # Calculate aggregated metrics with different k values
            aggregated_metrics = self.correctness_evaluator.aggregate_results(
                results=correctness_results,
                k_values=[1] + ([5, 10] if len(correctness_results) >= 5 else [])
            )

            # Display aggregated metrics
            print(self.correctness_evaluator.format_aggregated_metrics(aggregated_metrics))

        return results
