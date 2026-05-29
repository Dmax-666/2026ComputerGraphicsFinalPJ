"""LLM provider interface placeholders.

The first milestone uses deterministic Python agents. This module documents the
interface expected from future LLM-backed planners or prompt writers.
"""

from typing import Protocol


class TextGenerationTool(Protocol):
    def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Return a text completion for the provided prompts."""
