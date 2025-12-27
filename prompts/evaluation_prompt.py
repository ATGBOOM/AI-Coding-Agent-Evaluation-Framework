"""
Prompt templates for LLM coding agent evaluation.

Defines structured output format requiring:
- Confidence: High/Medium/Low
- Approach: Explanation of solution strategy
- Tests: Test cases to validate solution
- Solution: Final implementation
"""


EVALUATION_PROMPT_TEMPLATE = """You are an expert Python developer. Solve the following coding problem.

IMPORTANT: Structure your response with these exact sections:

## Confidence: [High/Medium/Low]

## Approach:
[Explain your solution strategy]

## Tests:
```python
# Write test cases here
```

## Solution:
```python
{prompt}
# Your implementation here
```

Problem:
{problem_description}

Function signature:
```python
{function_signature}
```

Requirements:
- Use descriptive variable and function names
- Keep functions small (<15 lines)
- Follow single responsibility principle
- Handle edge cases
- Write clean, production-ready code
- No print statements (use logging-ready patterns)
"""


def create_evaluation_prompt(
    problem_description: str,
    function_signature: str,
    prompt: str
) -> str:
    """
    Create a structured evaluation prompt for the LLM.

    Args:
        problem_description: The problem statement
        function_signature: Function signature to implement
        prompt: The code prompt/starter

    Returns:
        Formatted prompt string
    """
    pass


def parse_structured_response(response: str) -> dict:
    """
    Parse LLM response into structured components.

    Args:
        response: Raw LLM response text

    Returns:
        Dictionary with keys: confidence, approach, tests, solution

    Raises:
        ValueError: If response doesn't match expected structure
    """
    pass


def validate_response_structure(response: str) -> bool:
    """
    Validate that response contains all required sections.

    Args:
        response: Raw LLM response text

    Returns:
        True if valid structure, False otherwise
    """
    pass
