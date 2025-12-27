"""
Test executor for safely running code solutions against test cases.

Provides safe execution of both canonical and LLM-generated solutions
against test cases to validate correctness.
"""

import subprocess
import tempfile
import os
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class TestResult:
    """Result from running a solution against test cases."""
    passed: bool
    num_passed: int
    num_failed: int
    errors: List[str]
    output: str
    timeout: bool = False

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        total = self.num_passed + self.num_failed
        return (self.num_passed / total * 100) if total > 0 else 0.0


class TestExecutor:
    """Execute code solutions against test cases safely."""

    def __init__(self, timeout: int = 5):
        """
        Initialize test executor.

        Args:
            timeout: Maximum execution time in seconds
        """
        self.timeout = timeout

    def run_solution_with_tests(
        self,
        solution_code: str,
        test_code: str,
        entry_point: Optional[str] = None
    ) -> TestResult:
        """
        Run a solution against test cases.

        Args:
            solution_code: The solution code to test
            test_code: Test cases to run (including check function)
            entry_point: Entry point function name (optional)

        Returns:
            TestResult with execution details
        """
        # Create combined code with solution + tests
        combined_code = self._combine_code_and_tests(solution_code, test_code)

        # Execute in subprocess
        result = self._execute_code(combined_code)

        return result

    def validate_canonical_solution(
        self,
        canonical_solution: str,
        test_code: str,
        entry_point: str,
        prompt: str = ""
    ) -> TestResult:
        """
        Validate that canonical solution passes all tests.

        For HumanEval format, the canonical_solution is just the function body,
        so we need to combine it with the function signature from the prompt.

        Args:
            canonical_solution: The canonical solution from dataset (function body)
            test_code: Test cases from dataset
            entry_point: Function entry point
            prompt: The problem prompt containing function signature

        Returns:
            TestResult for canonical solution
        """
        # Combine prompt (which has the function signature) with canonical solution
        complete_solution = prompt + canonical_solution

        return self._run_humaneval_test(
            complete_solution,
            test_code,
            entry_point
        )

    def validate_llm_solution(
        self,
        llm_solution: str,
        test_code: str,
        entry_point: str
    ) -> TestResult:
        """
        Validate LLM solution against test cases.

        Args:
            llm_solution: The LLM-generated solution (complete function)
            test_code: Test cases from dataset
            entry_point: Function entry point

        Returns:
            TestResult for LLM solution
        """
        return self._run_humaneval_test(
            llm_solution,
            test_code,
            entry_point
        )

    def _run_humaneval_test(
        self,
        solution_code: str,
        test_code: str,
        entry_point: str
    ) -> TestResult:
        """
        Run solution against HumanEval format test cases.

        HumanEval tests expect a 'candidate' variable assigned to the function.

        Args:
            solution_code: Complete solution code
            test_code: HumanEval test code
            entry_point: Function entry point name

        Returns:
            TestResult
        """
        # Clean the solution code
        solution_code = self._clean_code(solution_code)

        # Create combined code with proper format for HumanEval tests
        combined = f"""
import sys
import traceback

{solution_code}

# Assign the function to 'candidate' for HumanEval tests
candidate = {entry_point}

{test_code}

# Run the check function
try:
    check(candidate)
    print("TESTS_PASSED")
except AssertionError as e:
    print(f"TESTS_FAILED: Assertion failed")
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"TESTS_FAILED: {{type(e).__name__}}: {{str(e)}}")
    traceback.print_exc()
    sys.exit(1)
"""

        return self._execute_code(combined)

    def _combine_code_and_tests(self, solution_code: str, test_code: str) -> str:
        """
        Combine solution code and test code into executable script.

        Args:
            solution_code: Solution code
            test_code: Test code

        Returns:
            Combined executable code
        """
        # Clean the solution code (remove markdown formatting if present)
        solution_code = self._clean_code(solution_code)

        combined = f"""
import sys
import traceback

# Solution code
{solution_code}

# Test code
{test_code}

# Run tests
try:
    check({{}})
    print("TESTS_PASSED")
except Exception as e:
    print(f"TESTS_FAILED: {{type(e).__name__}}: {{str(e)}}")
    traceback.print_exc()
    sys.exit(1)
"""
        return combined

    def _clean_code(self, code: str) -> str:
        """
        Clean code by removing markdown formatting.

        Args:
            code: Code potentially with markdown

        Returns:
            Cleaned code
        """
        # Remove markdown code blocks
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
        elif "```" in code:
            code = code.split("```")[1].split("```")[0]

        return code.strip()

    def _execute_code(self, code: str) -> TestResult:
        """
        Execute code in a subprocess.

        Args:
            code: Code to execute

        Returns:
            TestResult with execution details
        """
        errors = []
        output = ""
        timeout_occurred = False

        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                delete=False
            ) as f:
                f.write(code)
                temp_file = f.name

            try:
                # Run in subprocess
                result = subprocess.run(
                    ['python3', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )

                output = result.stdout + result.stderr

                # Check if tests passed
                if "TESTS_PASSED" in result.stdout:
                    return TestResult(
                        passed=True,
                        num_passed=1,
                        num_failed=0,
                        errors=[],
                        output=output
                    )
                else:
                    # Extract error from output
                    error_msg = result.stderr if result.stderr else result.stdout
                    errors.append(error_msg)
                    return TestResult(
                        passed=False,
                        num_passed=0,
                        num_failed=1,
                        errors=errors,
                        output=output
                    )

            except subprocess.TimeoutExpired:
                timeout_occurred = True
                errors.append(f"Execution timed out after {self.timeout} seconds")
                return TestResult(
                    passed=False,
                    num_passed=0,
                    num_failed=1,
                    errors=errors,
                    output=output,
                    timeout=True
                )

            finally:
                # Clean up temporary file
                if os.path.exists(temp_file):
                    os.remove(temp_file)

        except Exception as e:
            errors.append(f"Execution error: {str(e)}")
            return TestResult(
                passed=False,
                num_passed=0,
                num_failed=1,
                errors=errors,
                output=output
            )

    def run_llm_generated_tests(
        self,
        solution_code: str,
        llm_test_cases: str
    ) -> TestResult:
        """
        Run solution against LLM-generated test cases.

        Args:
            solution_code: Solution code
            llm_test_cases: LLM-generated test cases (assert statements)

        Returns:
            TestResult for LLM tests
        """
        if not llm_test_cases:
            return TestResult(
                passed=False,
                num_passed=0,
                num_failed=0,
                errors=["No test cases provided"],
                output=""
            )

        # Clean solution code
        solution_code = self._clean_code(solution_code)

        # Create executable code with LLM test cases
        combined = f"""
import sys
import traceback

{solution_code}

# LLM-generated test cases
try:
{self._indent_code(llm_test_cases, 4)}
    print("TESTS_PASSED")
except AssertionError as e:
    print(f"TESTS_FAILED: Assertion failed: {{str(e)}}")
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"TESTS_FAILED: {{type(e).__name__}}: {{str(e)}}")
    traceback.print_exc()
    sys.exit(1)
"""

        return self._execute_code(combined)

    def _indent_code(self, code: str, spaces: int) -> str:
        """
        Indent code by specified number of spaces.

        Args:
            code: Code to indent
            spaces: Number of spaces

        Returns:
            Indented code
        """
        indent = ' ' * spaces
        return '\n'.join(indent + line if line.strip() else line
                        for line in code.split('\n'))
