"""
Pydantic models for structured LLM responses.

These models ensure the LLM returns data in a consistent, parseable format
with all required fields for evaluation.
"""

from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class ConfidenceLevel(str, Enum):
    """Confidence level for the LLM's solution."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class LLMSolutionResponse(BaseModel):
    """Structured response from LLM for code generation tasks."""

    thought: str = Field(
        description="Brief line of thought explaining the approach to solve the problem"
    )

    confidence: ConfidenceLevel = Field(
        description="Confidence level in the solution (High, Medium, or Low)"
    )

    solution: str = Field(
        description="The complete Python code solution following design principles: "
                    "1) Descriptive naming, 2) Single responsibility, "
                    "3) Small functions (<15 lines), 4) No print statements (use logging), "
                    "5) Edge case handling"
    )

    test_cases: Optional[str] = Field(
        default=None,
        description="Test cases for the solution (TDD approach). "
                    "Include edge cases and typical test scenarios using assert statements."
    )

    class Config:
        """Pydantic config."""
        use_enum_values = True
