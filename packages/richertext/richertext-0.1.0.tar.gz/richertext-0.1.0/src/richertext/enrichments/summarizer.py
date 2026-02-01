"""Summarization enrichment."""

from __future__ import annotations


class SummarizerEnrichment:
    """Generate summaries from text fields using LLM."""

    def __init__(
        self,
        name: str,
        prompt_template: str,
        input_columns: list[str],
        output_column: str = None,
        max_length: int = 200,
    ):
        self._name = name
        self.prompt_template = prompt_template
        self.input_columns = input_columns
        self._output_column = output_column or f"{name}_summary"
        self.max_length = max_length

    @property
    def name(self) -> str:
        return self._name

    @property
    def output_columns(self) -> list[str]:
        return [self._output_column]

    def enrich(self, row: dict, provider) -> dict:
        """Generate a summary for the row."""
        # Build context from input columns
        context = {col: row.get(col, "") for col in self.input_columns}

        # Format prompt
        prompt = self.prompt_template.format(**context)

        system = f"""You are a summarizer. Write a concise summary in {self.max_length} characters or less.
Be direct and factual. Do not include preamble like "This organization..." - just state the key points."""

        response = provider.complete(prompt, system=system)
        summary = response.strip()

        return {self._output_column: summary}
