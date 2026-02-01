"""Enrichment interface."""

from __future__ import annotations

from typing import Protocol


class Enrichment(Protocol):
    """Protocol for enrichment operations."""

    @property
    def name(self) -> str:
        """Enrichment identifier used in config and output columns."""
        ...

    @property
    def output_columns(self) -> list[str]:
        """Column names this enrichment will add to the output."""
        ...

    def enrich(self, row: dict, provider) -> dict:
        """
        Enrich a single row of data.

        Args:
            row: Input row as dict
            provider: LLM provider instance

        Returns:
            Dict with output column names and values
        """
        ...
