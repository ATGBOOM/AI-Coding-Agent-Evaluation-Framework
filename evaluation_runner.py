"""
Evaluation runner for LLM coding agent evaluation.

Handles the orchestration of loading problems, generating solutions,
and comparing results against canonical solutions.
"""

import os
from typing import Dict, Optional
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from dataset.humanEvalDataset import HumanEvalDataset
from models.llm_response import LLMSolutionResponse


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
""")
        ])

        # Format the prompt
        formatted_prompt = prompt_template.format_messages(
            design_principles=design_principles,
            problem_prompt=prompt_text
        )

        # Generate structured response
        response: LLMSolutionResponse = self.structured_llm.invoke(formatted_prompt)

        return {
            'task_id': task_id,
            'prompt': prompt_text,
            'thought': response.thought,
            'confidence': response.confidence,
            'llm_solution': response.solution,
            'test_cases': response.test_cases,
            'canonical_solution': problem['canonical_solution'],
            'entry_point': problem['entry_point'],
            'test': problem['test']
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
