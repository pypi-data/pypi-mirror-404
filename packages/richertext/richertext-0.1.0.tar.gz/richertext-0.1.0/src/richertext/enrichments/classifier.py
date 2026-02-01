"""Classification enrichment."""

from __future__ import annotations

import json
import re


class ClassifierEnrichment:
    """Classify records into categories using LLM."""

    def __init__(
        self,
        name: str,
        prompt_template: str,
        categories: list[str],
        input_columns: list[str],
        output_column: str = None,
        include_reasoning: bool = False,
        reasoning_max_length: int = 200,
    ):
        self._name = name
        self.prompt_template = prompt_template
        self.categories = categories
        self.input_columns = input_columns
        self._output_column = output_column or f"{name}_category"
        self.include_reasoning = include_reasoning
        self.reasoning_max_length = reasoning_max_length
        self._reasoning_column = f"{self._output_column}_reasoning"

    @property
    def name(self) -> str:
        return self._name

    @property
    def output_columns(self) -> list[str]:
        if self.include_reasoning:
            return [self._output_column, self._reasoning_column]
        return [self._output_column]

    def enrich(self, row: dict, provider) -> dict:
        """Classify the row into one of the defined categories."""
        # Build context from input columns
        context = {col: row.get(col, "") for col in self.input_columns}

        # Format prompt
        prompt = self.prompt_template.format(**context)
        categories_str = ", ".join(self.categories)

        if self.include_reasoning:
            system = f"""You are a classifier. Choose ONE category from: {categories_str}

Respond with a JSON object containing:
1. "category": the selected category (must be exactly one of the options above)
2. "reasoning": brief explanation of why this category was selected (max {self.reasoning_max_length} characters)

Example:
{{"category": "Yes", "reasoning": "This organization would benefit because..."}}"""
        else:
            system = f"""You are a classifier. Respond with ONLY one of these categories: {categories_str}
Do not include any explanation or additional text."""

        response = provider.complete(prompt, system=system)

        if self.include_reasoning:
            # Parse JSON response
            try:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    result = json.loads(response)

                category = str(result.get("category", "")).strip()
                reasoning = str(result.get("reasoning", ""))
            except json.JSONDecodeError:
                category = response.strip()
                reasoning = ""

            # Validate response is in categories
            if category not in self.categories:
                for cat in self.categories:
                    if cat.lower() in category.lower():
                        category = cat
                        break
                else:
                    category = "Unknown"

            return {
                self._output_column: category,
                self._reasoning_column: reasoning,
            }
        else:
            category = response.strip()

            # Validate response is in categories
            if category not in self.categories:
                for cat in self.categories:
                    if cat.lower() in category.lower():
                        category = cat
                        break
                else:
                    category = "Unknown"

            return {self._output_column: category}
