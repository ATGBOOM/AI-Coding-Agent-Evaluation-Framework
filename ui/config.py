"""
Configuration for metrics display in the UI.

This module defines how metrics are displayed and makes it easy to add new metrics.
Each metric has a display configuration that controls its appearance.
"""

from dataclasses import dataclass
from typing import Callable, Any, Optional, List
from enum import Enum


class MetricCategory(Enum):
    """Categories for organizing metrics."""
    CORRECTNESS = "Correctness"
    EXPLAINABILITY = "Explainability"
    DESIGN = "Design"
    PERFORMANCE = "Performance"


class MetricType(Enum):
    """Types of metric displays."""
    PERCENTAGE = "percentage"  # Display as percentage with %
    BINARY = "binary"  # Display as Pass/Fail or Yes/No
    COUNT = "count"  # Display as raw number
    DECIMAL = "decimal"  # Display as decimal number
    TEXT = "text"  # Display as text


@dataclass
class MetricConfig:
    """Configuration for a single metric display."""
    key: str  # Key to access the metric value
    label: str  # Display label
    category: MetricCategory  # Which category it belongs to
    metric_type: MetricType  # How to format the value
    description: str  # Tooltip/help text
    precision: int = 2  # Decimal precision for numbers
    icon: Optional[str] = None  # Emoji/icon to display
    extractor: Optional[Callable[[Any], Any]] = None  # Function to extract value from result

    def format_value(self, value: Any) -> str:
        """
        Format the metric value for display.

        Args:
            value: Raw metric value

        Returns:
            Formatted string for display
        """
        if value is None:
            return "N/A"

        if self.metric_type == MetricType.PERCENTAGE:
            return f"{value:.{self.precision}f}%"
        elif self.metric_type == MetricType.BINARY:
            return "✅ PASS" if value else "❌ FAIL"
        elif self.metric_type == MetricType.COUNT:
            return str(int(value))
        elif self.metric_type == MetricType.DECIMAL:
            return f"{value:.{self.precision}f}"
        elif self.metric_type == MetricType.TEXT:
            return str(value)

        return str(value)


# =============================================================================
# CORRECTNESS METRICS CONFIGURATION
# =============================================================================

CORRECTNESS_METRICS: List[MetricConfig] = [
    MetricConfig(
        key="passed",
        label="Status",
        category=MetricCategory.CORRECTNESS,
        metric_type=MetricType.BINARY,
        description="Whether the solution passed all dataset tests",
        icon="✓",
        extractor=lambda result: result.get('correctness_result').passed if result.get('correctness_result') else None
    ),
    MetricConfig(
        key="pass_at_1",
        label="Pass@1",
        category=MetricCategory.CORRECTNESS,
        metric_type=MetricType.DECIMAL,
        description="Binary pass/fail indicator for single attempt (0.0 or 1.0)",
        precision=2,
        icon="🎯",
        extractor=lambda result: result.get('correctness_result').pass_at_1 if result.get('correctness_result') else None
    ),
    MetricConfig(
        key="test_pass_rate",
        label="Test Pass Rate",
        category=MetricCategory.CORRECTNESS,
        metric_type=MetricType.PERCENTAGE,
        description="Percentage of individual test cases passed",
        precision=1,
        icon="📊",
        extractor=lambda result: result.get('correctness_result').test_pass_rate if result.get('correctness_result') else None
    ),
    MetricConfig(
        key="num_passed",
        label="Tests Passed",
        category=MetricCategory.CORRECTNESS,
        metric_type=MetricType.COUNT,
        description="Number of test cases passed",
        icon="✓",
        extractor=lambda result: result.get('correctness_result').num_passed if result.get('correctness_result') else None
    ),
    MetricConfig(
        key="total_tests",
        label="Total Tests",
        category=MetricCategory.CORRECTNESS,
        metric_type=MetricType.COUNT,
        description="Total number of test cases",
        icon="#",
        extractor=lambda result: result.get('correctness_result').total_tests if result.get('correctness_result') else None
    ),
]

# =============================================================================
# EXPLAINABILITY METRICS CONFIGURATION
# =============================================================================

EXPLAINABILITY_METRICS: List[MetricConfig] = [
    MetricConfig(
        key="confidence",
        label="Confidence Level",
        category=MetricCategory.EXPLAINABILITY,
        metric_type=MetricType.TEXT,
        description="LLM's confidence in the solution (High/Medium/Low)",
        icon="🎓",
        extractor=lambda result: str(result.get('explainability_result').confidence_level) if result.get('explainability_result') else None
    ),
    MetricConfig(
        key="thought",
        label="Has Explanation",
        category=MetricCategory.EXPLAINABILITY,
        metric_type=MetricType.BINARY,
        description="Whether the LLM provided line of thought",
        icon="💭",
        extractor=lambda result: (result.get('explainability_result').thought is not None) if result.get('explainability_result') else False
    ),
    MetricConfig(
        key="has_tests",
        label="Has Test Cases",
        category=MetricCategory.EXPLAINABILITY,
        metric_type=MetricType.BINARY,
        description="Whether the LLM generated test cases",
        icon="🧪",
        extractor=lambda result: result.get('explainability_result').has_tests if result.get('explainability_result') else None
    ),
    MetricConfig(
        key="completeness",
        label="Completeness of Explanation",
        category=MetricCategory.EXPLAINABILITY,
        metric_type=MetricType.PERCENTAGE,
        description="The completeness of the explanation provided",
        icon="✅",
        extractor=lambda result: result.get('explainability_result').completeness_score if result.get('explainability_result') else None
    )
]

# =============================================================================
# AGGREGATED METRICS CONFIGURATION (for batch evaluation)
# =============================================================================

AGGREGATED_METRICS: List[MetricConfig] = [
    MetricConfig(
        key="total_tasks",
        label="Total Tasks",
        category=MetricCategory.CORRECTNESS,
        metric_type=MetricType.COUNT,
        description="Total number of tasks evaluated",
        icon="📋"
    ),
    MetricConfig(
        key="tasks_passed",
        label="Tasks Passed",
        category=MetricCategory.CORRECTNESS,
        metric_type=MetricType.COUNT,
        description="Number of tasks that passed",
        icon="✅"
    ),
    MetricConfig(
        key="overall_pass_rate",
        label="Overall Pass Rate",
        category=MetricCategory.CORRECTNESS,
        metric_type=MetricType.PERCENTAGE,
        description="Percentage of tasks that passed",
        precision=1,
        icon="📈"
    ),
    MetricConfig(
        key="average_test_pass_rate",
        label="Avg Test Pass Rate",
        category=MetricCategory.CORRECTNESS,
        metric_type=MetricType.PERCENTAGE,
        description="Average percentage of tests passed across all tasks",
        precision=1,
        icon="📊"
    ),
]

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_metrics_by_category(category: MetricCategory) -> List[MetricConfig]:
    """
    Get all metrics for a specific category.

    Args:
        category: The metric category to filter by

    Returns:
        List of MetricConfig objects for that category
    """
    all_metrics = CORRECTNESS_METRICS + EXPLAINABILITY_METRICS
    return [m for m in all_metrics if m.category == category]


def get_metric_config(key: str) -> Optional[MetricConfig]:
    """
    Get metric configuration by key.

    Args:
        key: Metric key to look up

    Returns:
        MetricConfig if found, None otherwise
    """
    all_metrics = CORRECTNESS_METRICS + EXPLAINABILITY_METRICS + AGGREGATED_METRICS
    for metric in all_metrics:
        if metric.key == key:
            return metric
    return None
