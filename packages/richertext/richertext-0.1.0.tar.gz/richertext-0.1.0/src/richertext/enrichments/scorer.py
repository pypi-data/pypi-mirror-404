"""Scoring/ranking enrichment."""

from __future__ import annotations

import json
import re


class ScorerEnrichment:
    """Score records on a single criterion using LLM."""

    def __init__(
        self,
        name: str,
        prompt_template: str,
        input_columns: list[str],
        output_column: str = None,
        scale_min: int = 1,
        scale_max: int = 10,
        include_reasoning: bool = False,
        reasoning_max_length: int = 200,
    ):
        self._name = name
        self.prompt_template = prompt_template
        self.input_columns = input_columns
        self._output_column = output_column or f"{name}_score"
        self._reasoning_column = f"{self._output_column}_reasoning"
        self.scale_min = scale_min
        self.scale_max = scale_max
        self.include_reasoning = include_reasoning
        self.reasoning_max_length = reasoning_max_length

    @property
    def name(self) -> str:
        return self._name

    @property
    def output_columns(self) -> list[str]:
        if self.include_reasoning:
            return [self._output_column, self._reasoning_column]
        return [self._output_column]

    def enrich(self, row: dict, provider) -> dict:
        """Score the row based on the prompt."""
        # Build context from input columns
        context = {col: row.get(col, "") for col in self.input_columns}

        # Format prompt
        prompt = self.prompt_template.format(**context)

        if self.include_reasoning:
            system = f"""You are an evaluator. Score the following on a scale from {self.scale_min} to {self.scale_max}.

Respond with a JSON object containing:
1. "score": the numeric score
2. "reasoning": brief explanation for this score (max {self.reasoning_max_length} characters)

Example: {{"score": 7, "reasoning": "This scored 7 because..."}}"""
        else:
            system = f"""You are an evaluator. Score the following on a scale from {self.scale_min} to {self.scale_max}.

Respond with ONLY a JSON object containing the score.
Example: {{"score": 7}}"""

        response = provider.complete(prompt, system=system)

        # Parse JSON response
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
            else:
                parsed = json.loads(response)

            score = parsed.get("score", "")
            reasoning = parsed.get("reasoning", "") if self.include_reasoning else ""
        except json.JSONDecodeError:
            score = ""
            reasoning = ""

        if self.include_reasoning:
            return {
                self._output_column: score,
                self._reasoning_column: reasoning,
            }
        return {self._output_column: score}
