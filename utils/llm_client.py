"""
LLM client for interacting with Groq API.

Handles API calls, retries, and response parsing.
"""

from typing import Optional
import time
from groq import Groq
from groq.types.chat import ChatCompletion


class GroqClient:
    """Client for Groq API interactions."""

    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.3-70b-versatile",
        temperature: float = 0.1,
        max_tokens: int = 2048,
        timeout: int = 30
    ):
        """
        Initialize Groq API client.

        Args:
            api_key: Groq API key
            model: Model identifier
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self._client: Optional[Groq] = None

    def initialize(self):
        """Initialize the Groq client connection."""
        if self._client is None:
            self._client = Groq(
                api_key=self.api_key,
                timeout=self.timeout,
            )

    def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate completion from Groq API.

        Args:
            prompt: Input prompt
            temperature: Override temperature
            max_tokens: Override max tokens

        Returns:
            Generated text response

        Raises:
            Exception: If API call fails
        """
        if self._client is None:
            self.initialize()

        try:
            response: ChatCompletion = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature if temperature is not None else self.temperature,
                max_tokens=max_tokens if max_tokens is not None else self.max_tokens,
            )

            return response.choices[0].message.content or ""

        except Exception as e:
            raise Exception(f"Groq API call failed: {str(e)}") from e

    def generate_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
        backoff_factor: float = 2.0
    ) -> str:
        """
        Generate with exponential backoff retry.

        Args:
            prompt: Input prompt
            max_retries: Maximum retry attempts
            backoff_factor: Backoff multiplier

        Returns:
            Generated text response

        Raises:
            Exception: If all retries fail
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                return self.generate(prompt)
            except Exception as e:
                last_exception = e

                if attempt < max_retries - 1:
                    sleep_time = backoff_factor ** attempt
                    print(f"Attempt {attempt + 1} failed. Retrying in {sleep_time}s...")
                    time.sleep(sleep_time)
                else:
                    print(f"All {max_retries} attempts failed.")

        raise Exception(f"Failed after {max_retries} retries") from last_exception

    def batch_generate(
        self,
        prompts: list[str],
        batch_size: int = 5
    ) -> list[str]:
        """
        Generate completions for multiple prompts.

        Args:
            prompts: List of input prompts
            batch_size: Number of concurrent requests

        Returns:
            List of generated responses
        """
        results = []

        for i in range(0, len(prompts), batch_size):
            batch = prompts[i:i + batch_size]

            for prompt in batch:
                try:
                    response = self.generate_with_retry(prompt)
                    results.append(response)
                except Exception as e:
                    print(f"Failed to generate for prompt: {prompt[:50]}... Error: {e}")
                    results.append("")

                # Small delay to avoid rate limiting
                time.sleep(0.1)

        return results

    def estimate_cost(self, num_requests: int, avg_tokens: int) -> float:
        """
        Estimate API cost for evaluation run.

        Args:
            num_requests: Number of API calls
            avg_tokens: Average tokens per request

        Returns:
            Estimated cost in USD
        """
        # Groq pricing (as of 2024, adjust as needed)
        # These are approximate values - check Groq's current pricing
        cost_per_million_tokens = {
            "mixtral-8x7b-32768": 0.27,
            "llama2-70b-4096": 0.70,
            "gemma-7b-it": 0.10,
        }

        model_cost = cost_per_million_tokens.get(self.model, 0.27)
        total_tokens = num_requests * avg_tokens
        estimated_cost = (total_tokens / 1_000_000) * model_cost

        return estimated_cost

