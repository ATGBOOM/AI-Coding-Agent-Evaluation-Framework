"""
Configuration settings for the evaluation framework.

Contains API keys, model settings, evaluation thresholds, and design principles.
"""

import os
from dataclasses import dataclass
from typing import List


@dataclass
class GroqConfig:
    """Configuration for Groq API."""
    api_key: str = os.getenv("GROQ_API_KEY", "")
    model: str = "mixtral-8x7b-32768"
    temperature: float = 0.1
    max_tokens: int = 2048
    timeout: int = 30


@dataclass
class EvaluationConfig:
    """Configuration for evaluation criteria."""

    # Correctness thresholds
    pass_at_k: int = 1

    # Explainability criteria
    confidence_levels: List[str] = None
    require_explanation: bool = True

    # Design principles
    max_function_lines: int = 15
    design_principles: List[str] = None

    def __post_init__(self):
        if self.confidence_levels is None:
            self.confidence_levels = ["High", "Medium", "Low"]

        if self.design_principles is None:
            self.design_principles = [
                "descriptive_naming",
                "single_responsibility",
                "small_functions",
                "tdd",
                "logging_ready",
                "edge_cases_handled"
            ]


@dataclass
class SandboxConfig:
    """Configuration for code execution sandbox."""
    timeout: int = 5
    memory_limit_mb: int = 256
    enable_network: bool = False
    allowed_imports: List[str] = None

    def __post_init__(self):
        if self.allowed_imports is None:
            self.allowed_imports = [
                "math", "itertools", "collections",
                "heapq", "bisect", "functools", "typing"
            ]


# Global configuration instances
groq_config = GroqConfig()
eval_config = EvaluationConfig()
sandbox_config = SandboxConfig()


# Data paths
HUMANEVAL_DATASET = "openai_humaneval"
RESULTS_DIR = "data"
RESULTS_FILE = "data/results.csv"
