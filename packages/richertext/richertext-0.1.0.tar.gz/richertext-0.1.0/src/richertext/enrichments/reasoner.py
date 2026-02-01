"""Reasoning/analysis enrichment."""

from __future__ import annotations


class ReasonerEnrichment:
    """Generate reasoning and analysis using LLM."""

    def __init__(
        self,
        name: str,
        prompt_template: str,
        input_columns: list[str],
        output_column: str = None,
    ):
        self._name = name
        self.prompt_template = prompt_template
        self.input_columns = input_columns
        self._output_column = output_column or f"{name}_analysis"

    @property
    def name(self) -> str:
        return self._name

    @property
    def output_columns(self) -> list[str]:
        return [self._output_column]

    def enrich(self, row: dict, provider) -> dict:
        """Generate reasoning/analysis for the row."""
        # Build context from input columns
        context = {col: row.get(col, "") for col in self.input_columns}

        # Format prompt
        prompt = self.prompt_template.format(**context)

        system = """You are an analyst. Provide clear, structured reasoning about the data provided.
Be specific and cite evidence from the input. Keep analysis concise but thorough."""

        response = provider.complete(prompt, system=system)
        analysis = response.strip()

        return {self._output_column: analysis}
