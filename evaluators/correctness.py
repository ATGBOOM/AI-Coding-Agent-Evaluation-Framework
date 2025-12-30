"""
Correctness evaluator for LLM-generated code.

Evaluates pass@k metric, test pass rate, and functional correctness
against HumanEval test cases.
"""

import math
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from utils.test_executor import TestExecutor, TestResult


@dataclass
class CorrectnessResult:
    """Result from correctness evaluation."""
    passed: bool
    num_passed: int
    num_failed: int
    total_tests: int
    test_pass_rate: float
    pass_at_1: float
    errors: List[str]
    test_result: Optional[TestResult] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'passed': self.passed,
            'num_passed': self.num_passed,
            'num_failed': self.num_failed,
            'total_tests': self.total_tests,
            'test_pass_rate': self.test_pass_rate,
            'pass_at_1': self.pass_at_1,
            'errors': self.errors,
            'timeout': self.test_result.timeout if self.test_result else False
        }


@dataclass
class AggregatedMetrics:
    """Aggregated correctness metrics across multiple tasks."""
    total_tasks: int
    tasks_passed: int
    tasks_failed: int
    overall_pass_rate: float
    average_test_pass_rate: float
    pass_at_k: Dict[int, float]  # k -> pass@k score
    individual_results: List[CorrectnessResult]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'total_tasks': self.total_tasks,
            'tasks_passed': self.tasks_passed,
            'tasks_failed': self.tasks_failed,
            'overall_pass_rate': self.overall_pass_rate,
            'average_test_pass_rate': self.average_test_pass_rate,
            'pass_at_k': self.pass_at_k
        }


class CorrectnessEvaluator:
    """Evaluates code correctness using HumanEval test suite."""

    def __init__(self, timeout: int = 5):
        """
        Initialize correctness evaluator.

        Args:
            timeout: Maximum execution time for tests (seconds)
        """
        self.timeout = timeout
        self.test_executor = TestExecutor(timeout=timeout)

    def evaluate(
        self,
        solution_code: str,
        test_code: str,
        entry_point: str
    ) -> CorrectnessResult:
        """
        Evaluate solution correctness against test cases.

        Uses TestExecutor to run functional correctness tests.

        Args:
            solution_code: Generated solution code
            test_code: Test case code (HumanEval format)
            entry_point: Function name to test

        Returns:
            CorrectnessResult with evaluation metrics
        """
        # Run solution against test cases using TestExecutor
        test_result = self.test_executor.validate_llm_solution(
            llm_solution=solution_code,
            test_code=test_code,
            entry_point=entry_point
        )

        # Calculate metrics
        total_tests = test_result.num_passed + test_result.num_failed
        test_pass_rate = test_result.success_rate

        # For single execution, pass@1 is simply whether it passed
        pass_at_1 = 1.0 if test_result.passed else 0.0

        return CorrectnessResult(
            passed=test_result.passed,
            num_passed=test_result.num_passed,
            num_failed=test_result.num_failed,
            total_tests=total_tests,
            test_pass_rate=test_pass_rate,
            pass_at_1=pass_at_1,
            errors=test_result.errors,
            test_result=test_result
        )

    def evaluate_with_llm_tests(
        self,
        solution_code: str,
        llm_test_cases: str
    ) -> CorrectnessResult:
        """
        Evaluate solution against LLM-generated test cases.

        Args:
            solution_code: Solution code to test
            llm_test_cases: LLM-generated test cases

        Returns:
            CorrectnessResult with evaluation metrics
        """
        # Run solution against LLM-generated test cases
        test_result = self.test_executor.run_llm_generated_tests(
            solution_code=solution_code,
            llm_test_cases=llm_test_cases
        )

        # Calculate metrics
        total_tests = test_result.num_passed + test_result.num_failed
        test_pass_rate = test_result.success_rate
        pass_at_1 = 1.0 if test_result.passed else 0.0

        return CorrectnessResult(
            passed=test_result.passed,
            num_passed=test_result.num_passed,
            num_failed=test_result.num_failed,
            total_tests=total_tests,
            test_pass_rate=test_pass_rate,
            pass_at_1=pass_at_1,
            errors=test_result.errors,
            test_result=test_result
        )

    def run_test_case(
        self,
        solution_code: str,
        test_code: str,
        entry_point: str
    ) -> tuple[bool, str]:
        """
        Run a single test case.

        Args:
            solution_code: Solution to test
            test_code: Test case code
            entry_point: Function name

        Returns:
            Tuple of (passed, error_message)
        """
        test_result = self.test_executor.validate_llm_solution(
            llm_solution=solution_code,
            test_code=test_code,
            entry_point=entry_point
        )

        error_msg = test_result.errors[0] if test_result.errors else ""
        return test_result.passed, error_msg

    def calculate_pass_at_k(
        self,
        n: int,
        c: int,
        k: int
    ) -> float:
        """
        Calculate pass@k metric using the unbiased estimator.

        Formula from "Evaluating Large Language Models Trained on Code" (Chen et al. 2021):
        pass@k = 1 - C(n-c, k) / C(n, k)

        Args:
            n: Total number of samples generated
            c: Number of correct samples
            k: Number of samples to evaluate (k <= n)

        Returns:
            pass@k score between 0 and 1
        """
        if n < k:
            raise ValueError(f"k ({k}) cannot be greater than n ({n})")

        if c == 0:
            return 0.0

        if k == 0:
            return 0.0

        # Special case: if c >= k, at least one correct sample will be in any k samples
        if c >= k:
            return 1.0

        # Calculate using combination formula
        # pass@k = 1 - C(n-c, k) / C(n, k)
        try:
            numerator = math.comb(n - c, k)
            denominator = math.comb(n, k)
            return 1.0 - (numerator / denominator)
        except (ValueError, ZeroDivisionError):
            # Fallback: simple success rate
            return c / n

    def aggregate_results(
        self,
        results: List[CorrectnessResult],
        k_values: List[int] = [1, 5, 10]
    ) -> AggregatedMetrics:
        """
        Aggregate correctness results across multiple tasks.

        Args:
            results: List of CorrectnessResult from individual tasks
            k_values: List of k values to calculate pass@k for

        Returns:
            AggregatedMetrics with overall statistics
        """
        if not results:
            return AggregatedMetrics(
                total_tasks=0,
                tasks_passed=0,
                tasks_failed=0,
                overall_pass_rate=0.0,
                average_test_pass_rate=0.0,
                pass_at_k={},
                individual_results=[]
            )

        total_tasks = len(results)
        tasks_passed = sum(1 for r in results if r.passed)
        tasks_failed = total_tasks - tasks_passed
        overall_pass_rate = (tasks_passed / total_tasks * 100) if total_tasks > 0 else 0.0

        # Calculate average test pass rate across all tasks
        average_test_pass_rate = sum(r.test_pass_rate for r in results) / total_tasks

        # Calculate pass@k for different k values
        pass_at_k = {}
        n_samples = total_tasks
        c_correct = tasks_passed

        for k in k_values:
            if k <= n_samples:
                pass_at_k[k] = self.calculate_pass_at_k(n_samples, c_correct, k)

        return AggregatedMetrics(
            total_tasks=total_tasks,
            tasks_passed=tasks_passed,
            tasks_failed=tasks_failed,
            overall_pass_rate=overall_pass_rate,
            average_test_pass_rate=average_test_pass_rate,
            pass_at_k=pass_at_k,
            individual_results=results
        )

    def format_aggregated_metrics(self, metrics: AggregatedMetrics) -> str:
        """
        Format aggregated metrics for display.

        Args:
            metrics: AggregatedMetrics to format

        Returns:
            Formatted string for display
        """
        separator = "=" * 80

        formatted = f"""
{separator}
AGGREGATED CORRECTNESS METRICS
{separator}

Total Tasks: {metrics.total_tasks}
Tasks Passed: {metrics.tasks_passed}
Tasks Failed: {metrics.tasks_failed}
Overall Pass Rate: {metrics.overall_pass_rate:.2f}%
Average Test Pass Rate: {metrics.average_test_pass_rate:.2f}%

Pass@k Metrics:
"""

        for k, score in sorted(metrics.pass_at_k.items()):
            formatted += f"  pass@{k}: {score:.4f} ({score * 100:.2f}%)\n"

        formatted += f"\n{separator}\n"

        return formatted
