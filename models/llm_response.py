"""
Pydantic models for structured LLM responses.

These models ensure the LLM returns data in a consistent, parseable format
with all required fields for evaluation.
"""

from typing import Optional, List, Dict, Literal
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

    completeness: str = Field(
        description="Explanation of algorithm choice, key variables/functions, constraints and assumptions, and edge case consideration"
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

class JudgeInfo(BaseModel):
    type: Literal["human", "llm"]
    name: str
    version: Optional[str]

class EvaluationMetadata(BaseModel):
    benchmark: str = "HumanEval"
    problem_id: str
    model_name: str
    model_version: Optional[str]
    run_id: str
    timestamp: str
    judge: JudgeInfo

class PromptTraceability(BaseModel):
    score: int
    max_score: int = 30
    requirement_coverage_percent: int
    missed_requirements: List[str]
    incorrect_mappings: List[Dict[str, str]]
    justification: str

class AssumptionTransparency(BaseModel):
    score: int
    max_score: int = 20
    assumptions_identified: List[Dict]
    hidden_assumptions_detected: List[Dict]
    justification: str

class AlgorithmicRationale(BaseModel):
    score: int
    max_score: int = 20
    algorithm_identified: bool
    algorithm_description_accuracy: Literal[
        "correct", "partially_correct", "incorrect"
    ]
    mentions_complexity: bool
    tradeoffs_discussed: bool
    overclaim_detected: bool
    justification: str

class EdgeCaseAwareness(BaseModel):
    score: int
    max_score: int = 15
    edge_cases_mentioned: List[str]
    edge_cases_in_tests: List[str]
    missed_edge_cases: List[str]
    false_edge_case_claims: List[str]
    justification: str

class ExplanationCodeConsistency(BaseModel):
    score: int
    max_score: int = 15
    contradictions: List[Dict[str, str]]
    phantom_features: List[str]
    behavioral_alignment: Literal["high", "medium", "low"]
    justification: str

class ExplainabilityScores(BaseModel):
    prompt_traceability: PromptTraceability
    assumption_transparency: AssumptionTransparency
    algorithmic_rationale: AlgorithmicRationale
    edge_case_awareness: EdgeCaseAwareness
    explanation_code_consistency: ExplanationCodeConsistency

class FinalScores(BaseModel):
    total_explainability_score: int
    max_total_score: int = 100
    normalized_score: float
    explainability_grade: Literal["A", "B", "C", "D", "F"]

class Notes(BaseModel):
    strengths: List[str]
    weaknesses: List[str]
    confidence_level: ConfidenceLevel

class LLMEvaluationResponse(BaseModel):
    evaluation_metadata: EvaluationMetadata
    explainability_scores: ExplainabilityScores
    final_scores: FinalScores
    notes: Notes