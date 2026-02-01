"""Multi-label classification enrichment."""

from __future__ import annotations

import json
import re


class LabelerEnrichment:
    """Apply multiple labels to records using LLM."""

    def __init__(
        self,
        name: str,
        prompt_template: str,
        labels: list[str],
        input_columns: list[str],
        output_column: str = None,
        include_reasoning: bool = False,
        reasoning_max_length: int = 200,
    ):
        self._name = name
        self.prompt_template = prompt_template
        self.labels = labels
        self.input_columns = input_columns
        self._output_column = output_column or f"{name}_labels"
        self._reasoning_column = f"{self._output_column}_reasoning"
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
        """Apply labels to the row."""
        # Build context from input columns
        context = {col: row.get(col, "") for col in self.input_columns}

        # Format prompt
        prompt = self.prompt_template.format(**context)
        labels_str = "\n".join(f"- {label}" for label in self.labels)

        if self.include_reasoning:
            system = f"""You are a labeler. Select ALL labels that apply from this list:
{labels_str}

Respond with a JSON object containing:
1. "labels": array of applicable labels in alphabetical order
2. "reasoning": brief explanation of why each label was selected (max {self.reasoning_max_length} characters)

Example:
{{"labels": ["Label A", "Label B"], "reasoning": "Label A applies because... Label B applies because..."}}

If no labels apply:
{{"labels": [], "reasoning": "None of the labels apply because..."}}"""
        else:
            system = f"""You are a labeler. Select ALL labels that apply from this list:
{labels_str}

Respond with a JSON object containing:
- "labels": array of applicable labels in alphabetical order

Example:
{{"labels": ["Label A", "Label B"]}}

If no labels apply:
{{"labels": []}}"""

        response = provider.complete(prompt, system=system)

        # Parse JSON response
        try:
            # Try to extract JSON object from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(response)

            selected_labels = result.get("labels", [])
            reasoning = result.get("reasoning", "") if self.include_reasoning else ""

            # Validate labels are in our list
            selected_labels = [l for l in selected_labels if l in self.labels]
            # Sort alphabetically
            selected_labels.sort()
        except json.JSONDecodeError:
            selected_labels = []
            reasoning = ""

        # Join labels with semicolon for CSV
        labels_text = "; ".join(selected_labels) if selected_labels else ""

        if self.include_reasoning:
            return {
                self._output_column: labels_text,
                self._reasoning_column: reasoning,
            }
        return {self._output_column: labels_text}
