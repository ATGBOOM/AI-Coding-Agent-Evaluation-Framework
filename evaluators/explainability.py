"""
Explainability evaluator for LLM responses.

Evaluates:
1. Confidence level (High/Medium/Low)
2. Quality of explanations
"""

import os
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
import re
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from models.llm_response import LLMEvaluationResponse


class ConfidenceLevel(Enum):
    """Confidence levels for LLM responses."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    UNKNOWN = "Unknown"

@dataclass
class ExplainabilityResult:
    """Result from explainability evaluation."""
    confidence_level: ConfidenceLevel
    thought: str
    approach_quality: float
    has_tests: bool
    completeness: str
    completeness_dict: Dict[bool, list[str]]
    completeness_score: int
    explainability_score: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'confidence_level': self.confidence_level,
            'thought': self.thought,
            'approach_quality': self.approach_quality,
            'has_tests': self.has_tests,
            'completeness': self.completeness,
            'completeness_dict': self.completeness_dict,
            'completeness_score': self.completeness_score,
            'explainability_score': self.explainability_score
        }

@dataclass
class LLMEvaluator:
    def __init__(self, api_key: Optional[str] = None):
        load_dotenv()

        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment or provided")

        self.llm = ChatGroq(
            api_key=self.api_key,
            model=os.getenv('GROQ_EVAL_MODEL', 'openai/gpt-oss-120b'),
            temperature=float(os.getenv('GROQ_TEMPERATURE', '0.1')),
            max_tokens=int(os.getenv('GROQ_MAX_TOKENS', '2048'))
        )

        self.structured_llm = self.llm.with_structured_output(LLMEvaluationResponse)


    def evaluate_explainability(self, explanation: str, code: str, tests: str):

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are an expert evaluator of code explanations. Respond ONLY with valid JSON"),
            ("user", """Evaluate the following explanation and code for completeness and clarity:

Code:
{code}             

Tests:
{tests}

Explanation:
{explanation}
""")
        ])
        formatted_prompt = prompt_template.format_messages(
            code=code,
            tests=tests,
            explanation=explanation,
        )
        response: LLMEvaluationResponse = self.structured_llm.invoke(formatted_prompt)
        print(response)
        return response
    
class ExplainabilityEvaluator:
    """Evaluates explainability of LLM responses."""

    def __init__(self, require_approach: bool = True):
        """
        Initialize explainability evaluator.

        Args:
            require_approach: Whether approach explanation is required
        """
        self.require_approach = require_approach

    def evaluate(
            self,
            solution: str,
            thought: str,
            test_cases: str,
            confidence: str,
            completeness: str
        ) -> ExplainabilityResult:
        """
        Evaluate explainability of response.

        Args:
            thought: LLM's line of thought
            test_cases: LLM's generated test cases
            confidence: LLM's confidence level text
            completeness: Explanation text

        Returns:
            Dictionary with:
                - confidence_level: ConfidenceLevel
                - has_approach: bool
                - approach_quality: float (0-1)
                - has_tests: bool
                - explainability_score: float (0-1)
        """
        completeness_dict = self.evaluate_completeness(completeness)
        llm = LLMEvaluator()
        result = llm.evaluate_explainability(
            explanation=completeness,
            code=solution,
            tests=test_cases
        )

        return ExplainabilityResult(
            confidence_level=self.extract_confidence(confidence),
            thought=thought,
            has_tests=bool(test_cases),
            completeness=completeness,
            completeness_dict=completeness_dict,
            completeness_score=len(completeness_dict[True])/(len(completeness_dict[False]) + len(completeness_dict[True])) * 100,
        )

    def extract_confidence(self, confidence: str) -> ConfidenceLevel:
        """
        Extract confidence level from text.

        Args:
            confidence_text: Raw confidence text

        Returns:
            ConfidenceLevel enum
        """
        confidence_text = confidence.strip().lower()
        if "high" in confidence_text:
            return ConfidenceLevel.HIGH
        elif "medium" in confidence_text:
            return ConfidenceLevel.MEDIUM
        elif "low" in confidence_text:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.UNKNOWN

    def evaluate_completeness(self, completeness_text: str) -> Dict[bool, list[str]]:
        """
        Evaluate completeness of explanation.

        Args:
            completeness_text: Explanation text

        Returns:
            Dictionary indicating presence of key aspects
        """
        # Simple heuristic: count number of key aspects mentioned
        score = 0.0

        key_aspect_patterns = {
            "algorithm": r"\balgorithm(s)?\b",
            "variables": r"\bvariable(s)?\b",
            "functions": r"\bfunction(s)?\b",
            "constraints": r"\bconstraint(s)?\b",
            "assumptions": r"\bassum(e|es|ed|ing|ption|ptions)\b",
            "edge cases": r"\bedge[-\s]?case(s)?\b",
        }

        found = {True: [], False: []}
        for name, pattern in key_aspect_patterns.items():
            if re.search(pattern, completeness_text, re.IGNORECASE):
                found[True].append(name)
            else:
                found[False].append(name)
        return found

    def score_approach_quality(self, approach_text: str) -> float:
        """
        Score quality of approach explanation.

        Args:
            approach_text: Approach explanation text

        Returns:
            Quality score between 0 and 1
        """
        pass

    def calculate_explainability_score(
        self,
        confidence_level: ConfidenceLevel,
        has_approach: bool,
        approach_quality: float,
        has_tests: bool
    ) -> float:
        """
        Calculate overall explainability score.

        Args:
            confidence_level: Extracted confidence level
            has_approach: Whether approach is provided
            approach_quality: Quality score of approach
            has_tests: Whether tests are provided

        Returns:
            Overall score between 0 and 1
        """
        pass
