"""LLM Provider interface."""

from typing import Protocol


class LLMProvider(Protocol):
    """Protocol for LLM API providers."""

    def complete(self, prompt: str, system: str = "") -> str:
        """
        Send a prompt to the LLM and return the response.

        Args:
            prompt: The user prompt/message
            system: Optional system prompt

        Returns:
            The model's response text
        """
        ...

    @property
    def model_name(self) -> str:
        """Return the model identifier being used."""
        ...
