"""Configuration loading and enrichment building."""

import yaml
from pathlib import Path

from ..providers import GeminiProvider
from ..enrichments import (
    ClassifierEnrichment,
    SummarizerEnrichment,
    ScorerEnrichment,
    ReasonerEnrichment,
    LabelerEnrichment,
)


def load_config(config_path: Path) -> dict:
    """Load YAML configuration file."""
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_prompts(prompts_path: Path) -> dict:
    """Load prompts from YAML file."""
    with open(prompts_path) as f:
        return yaml.safe_load(f)


def build_provider(config: dict):
    """Build LLM provider from config."""
    provider_config = config.get("provider", {})
    provider_type = provider_config.get("type", "gemini")
    model = provider_config.get("model")

    if provider_type == "gemini":
        return GeminiProvider(model=model) if model else GeminiProvider()
    else:
        raise ValueError(f"Unknown provider type: {provider_type}. Only 'gemini' is supported.")


def build_enrichments(config: dict, prompts: dict) -> list:
    """Build enrichment instances from config."""
    enrichments = []

    for enrich_config in config.get("enrichments", []):
        enrich_type = enrich_config.get("type")
        name = enrich_config.get("name")

        # Resolve prompt: use prompt_key to look up in prompts, or fall back to inline prompt
        prompt_key = enrich_config.get("prompt_key")
        if prompt_key:
            prompt_template = prompts.get(prompt_key)
            if not prompt_template:
                raise ValueError(f"Prompt key '{prompt_key}' not found in prompts file")
        else:
            prompt_template = enrich_config.get("prompt", "")

        if enrich_type == "classifier":
            enrichments.append(
                ClassifierEnrichment(
                    name=name,
                    prompt_template=prompt_template,
                    categories=enrich_config.get("categories", []),
                    input_columns=enrich_config.get("input_columns", []),
                    output_column=enrich_config.get("output_column"),
                    include_reasoning=enrich_config.get("include_reasoning", False),
                    reasoning_max_length=enrich_config.get("reasoning_max_length", 200),
                )
            )
        elif enrich_type == "summarizer":
            enrichments.append(
                SummarizerEnrichment(
                    name=name,
                    prompt_template=prompt_template,
                    input_columns=enrich_config.get("input_columns", []),
                    output_column=enrich_config.get("output_column"),
                    max_length=enrich_config.get("max_length", 200),
                )
            )
        elif enrich_type == "scorer":
            enrichments.append(
                ScorerEnrichment(
                    name=name,
                    prompt_template=prompt_template,
                    input_columns=enrich_config.get("input_columns", []),
                    output_column=enrich_config.get("output_column"),
                    scale_min=enrich_config.get("scale_min", 1),
                    scale_max=enrich_config.get("scale_max", 10),
                    include_reasoning=enrich_config.get("include_reasoning", False),
                    reasoning_max_length=enrich_config.get("reasoning_max_length", 200),
                )
            )
        elif enrich_type == "reasoner":
            enrichments.append(
                ReasonerEnrichment(
                    name=name,
                    prompt_template=prompt_template,
                    input_columns=enrich_config.get("input_columns", []),
                    output_column=enrich_config.get("output_column"),
                )
            )
        elif enrich_type == "labeler":
            enrichments.append(
                LabelerEnrichment(
                    name=name,
                    prompt_template=prompt_template,
                    labels=enrich_config.get("labels", []),
                    input_columns=enrich_config.get("input_columns", []),
                    output_column=enrich_config.get("output_column"),
                    include_reasoning=enrich_config.get("include_reasoning", False),
                    reasoning_max_length=enrich_config.get("reasoning_max_length", 200),
                )
            )
        else:
            raise ValueError(f"Unknown enrichment type: {enrich_type}")

    return enrichments
