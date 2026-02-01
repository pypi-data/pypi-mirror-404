"""RicherText - LLM-powered CSV enrichment made easy.

Quick Start:
    >>> from richertext import classify, summarize, score, label, reason

    # Single-record functions
    >>> result = classify("I love this!", categories=["positive", "negative"])
    >>> summary = summarize("Long text here...", max_length=100)
    >>> clarity = score("Evaluate this", prompt="Rate clarity: {text}")
    >>> labels = label("News about tech", labels=["news", "tech", "sports"])
    >>> analysis = reason("Data to analyze...")

    # CSV enrichment
    >>> from richertext import enrich_csv
    >>> enrich_csv("data.csv", config="config.yaml")

For more information, see: https://github.com/yourusername/richertext
"""

from ._version import __version__
from .api import classify, summarize, score, label, reason, enrich_csv, enrich_records
from .exceptions import RicherTextError, ConfigurationError, ProviderError

# Re-export key classes for advanced usage
from .providers import GeminiProvider, LLMProvider
from .enrichments import (
    Enrichment,
    ClassifierEnrichment,
    SummarizerEnrichment,
    ScorerEnrichment,
    ReasonerEnrichment,
    LabelerEnrichment,
)
from .pipeline import PipelineRunner

__all__ = [
    # Version
    "__version__",
    # High-level API
    "classify",
    "summarize",
    "score",
    "label",
    "reason",
    "enrich_csv",
    "enrich_records",
    # Exceptions
    "RicherTextError",
    "ConfigurationError",
    "ProviderError",
    # Providers
    "LLMProvider",
    "GeminiProvider",
    # Enrichments
    "Enrichment",
    "ClassifierEnrichment",
    "SummarizerEnrichment",
    "ScorerEnrichment",
    "ReasonerEnrichment",
    "LabelerEnrichment",
    # Pipeline
    "PipelineRunner",
]
