"""High-level API for richertext.

This module provides simple, easy-to-use functions for common enrichment tasks.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Any, Optional, Union

from .exceptions import ConfigurationError, ProviderError
from .providers import GeminiProvider
from .enrichments import (
    ClassifierEnrichment,
    LabelerEnrichment,
    ReasonerEnrichment,
    ScorerEnrichment,
    SummarizerEnrichment,
)
from .pipeline import PipelineRunner
from .utils import build_enrichments, build_provider, load_config, load_prompts


def _get_default_provider():
    """Auto-detect and return a provider based on available API keys."""
    if os.environ.get("GOOGLE_API_KEY"):
        return GeminiProvider()
    else:
        raise ProviderError(
            "No API key found. Set GOOGLE_API_KEY environment variable."
        )


def classify(
    text: str,
    categories: list[str],
    prompt: Optional[str] = None,
    include_reasoning: bool = False,
    reasoning_max_length: int = 200,
    provider=None,
) -> dict:
    """Classify text into one of the given categories.

    Args:
        text: The text to classify
        categories: List of possible categories
        prompt: Optional custom prompt template (use {text} as placeholder)
        include_reasoning: Whether to include reasoning in the result
        provider: Optional LLM provider (auto-detects if not provided)

    Returns:
        Dict with 'category' and optionally 'reasoning' keys

    Example:
        >>> result = classify("I love this product!", categories=["positive", "negative"])
        >>> print(result["category"])
        positive
    """
    if provider is None:
        provider = _get_default_provider()

    prompt_template = prompt or "Classify the following text:\n\n{text}"

    enrichment = ClassifierEnrichment(
        name="classify",
        prompt_template=prompt_template,
        categories=categories,
        input_columns=["text"],
        include_reasoning=include_reasoning,
        reasoning_max_length=reasoning_max_length,
    )

    row = {"text": text}
    result = enrichment.enrich(row, provider)

    if include_reasoning:
        return {
            "category": result["classify_category"],
            "reasoning": result["classify_category_reasoning"],
        }
    return {"category": result["classify_category"]}


def summarize(
    text: str,
    max_length: int = 200,
    prompt: Optional[str] = None,
    provider=None,
) -> str:
    """Generate a summary of the given text.

    Args:
        text: The text to summarize
        max_length: Maximum length of the summary in characters
        prompt: Optional custom prompt template (use {text} as placeholder)
        provider: Optional LLM provider (auto-detects if not provided)

    Returns:
        The generated summary as a string

    Example:
        >>> summary = summarize("Long article text here...", max_length=100)
        >>> print(summary)
    """
    if provider is None:
        provider = _get_default_provider()

    prompt_template = prompt or "Summarize the following text:\n\n{text}"

    enrichment = SummarizerEnrichment(
        name="summarize",
        prompt_template=prompt_template,
        input_columns=["text"],
        max_length=max_length,
    )

    row = {"text": text}
    result = enrichment.enrich(row, provider)

    return result["summarize_summary"]


def score(
    text: str,
    prompt: Optional[str] = None,
    scale_min: int = 1,
    scale_max: int = 10,
    include_reasoning: bool = False,
    reasoning_max_length: int = 200,
    provider=None,
) -> Union[int, dict]:
    """Score text based on the prompt.

    Args:
        text: The text to score
        prompt: Custom prompt template (use {text} as placeholder)
        scale_min: Minimum score value
        scale_max: Maximum score value
        include_reasoning: Whether to include reasoning in the result
        reasoning_max_length: Maximum characters for reasoning
        provider: Optional LLM provider (auto-detects if not provided)

    Returns:
        The score as an integer, or dict with 'score' and 'reasoning' if reasoning enabled

    Example:
        >>> result = score("Sample text", prompt="Rate the clarity of: {text}")
        >>> print(result)
        8
    """
    if provider is None:
        provider = _get_default_provider()

    prompt_template = prompt or "Evaluate the following text:\n\n{text}"

    enrichment = ScorerEnrichment(
        name="score",
        prompt_template=prompt_template,
        input_columns=["text"],
        scale_min=scale_min,
        scale_max=scale_max,
        include_reasoning=include_reasoning,
        reasoning_max_length=reasoning_max_length,
    )

    row = {"text": text}
    result = enrichment.enrich(row, provider)

    if include_reasoning:
        return {
            "score": result["score_score"],
            "reasoning": result["score_score_reasoning"],
        }
    return result["score_score"]


def label(
    text: str,
    labels: list[str],
    prompt: Optional[str] = None,
    include_reasoning: bool = False,
    reasoning_max_length: int = 200,
    provider=None,
) -> dict:
    """Apply multiple labels to text (multi-label classification).

    Args:
        text: The text to label
        labels: List of possible labels
        prompt: Optional custom prompt template (use {text} as placeholder)
        include_reasoning: Whether to include reasoning in the result
        reasoning_max_length: Maximum characters for reasoning
        provider: Optional LLM provider (auto-detects if not provided)

    Returns:
        Dict with 'labels' (list), and 'reasoning' if enabled

    Example:
        >>> result = label("Breaking news about tech", labels=["news", "tech", "sports"])
        >>> print(result["labels"])
        ["news", "tech"]
    """
    if provider is None:
        provider = _get_default_provider()

    prompt_template = prompt or "Label the following text:\n\n{text}"

    enrichment = LabelerEnrichment(
        name="label",
        prompt_template=prompt_template,
        labels=labels,
        input_columns=["text"],
        include_reasoning=include_reasoning,
        reasoning_max_length=reasoning_max_length,
    )

    row = {"text": text}
    result = enrichment.enrich(row, provider)

    # Parse the semicolon-separated labels back to a list
    labels_str = result["label_labels"]
    labels_list = [l.strip() for l in labels_str.split(";")] if labels_str else []

    if include_reasoning:
        return {
            "labels": labels_list,
            "reasoning": result["label_labels_reasoning"],
        }
    return {"labels": labels_list}


def reason(
    text: str,
    prompt: Optional[str] = None,
    provider=None,
) -> str:
    """Generate reasoning/analysis about the given text.

    Args:
        text: The text to analyze
        prompt: Optional custom prompt template (use {text} as placeholder)
        provider: Optional LLM provider (auto-detects if not provided)

    Returns:
        The analysis as a string

    Example:
        >>> analysis = reason("Data about sales performance...")
        >>> print(analysis)
    """
    if provider is None:
        provider = _get_default_provider()

    prompt_template = prompt or "Analyze the following text:\n\n{text}"

    enrichment = ReasonerEnrichment(
        name="reason",
        prompt_template=prompt_template,
        input_columns=["text"],
    )

    row = {"text": text}
    result = enrichment.enrich(row, provider)

    return result["reason_analysis"]


def enrich_csv(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    config: Optional[Union[str, Path]] = None,
    enrichments: Optional[list[dict]] = None,
    provider_type: Optional[str] = None,
    model: Optional[str] = None,
    workers: Optional[int] = None,
    verbose: bool = False,
) -> Path:
    """Enrich a CSV file with LLM-generated data.

    Args:
        input_path: Path to input CSV file
        output_path: Path for output CSV (default: input_enriched.csv)
        config: Path to YAML config file (alternative to inline enrichments)
        enrichments: List of enrichment configs (alternative to config file)
        provider_type: Provider type: "gemini"
        model: Model name to use
        workers: Number of parallel workers (default: auto-calculated from model rate limit)
        verbose: Whether to print progress

    Returns:
        Path to the output file

    Example with config file:
        >>> enrich_csv("data.csv", config="config.yaml")

    Example with inline enrichments:
        >>> enrich_csv("data.csv", enrichments=[
        ...     {"type": "classifier", "name": "sentiment",
        ...      "categories": ["positive", "negative"],
        ...      "input_columns": ["text"],
        ...      "prompt": "Classify sentiment: {text}"}
        ... ])
    """
    input_path = Path(input_path)

    if not input_path.exists():
        raise ConfigurationError(f"Input file not found: {input_path}")

    # Determine output path
    if output_path is None:
        output_path = input_path.parent / f"{input_path.stem}_enriched.csv"
    else:
        output_path = Path(output_path)

    # Load config or use inline enrichments
    if config is not None:
        config_path = Path(config)
        if not config_path.exists():
            raise ConfigurationError(f"Config file not found: {config_path}")

        config_dict = load_config(config_path)

        # Load prompts if specified
        prompts = {}
        if config_dict.get("prompts_file"):
            prompts_path = config_path.parent / config_dict["prompts_file"]
            if prompts_path.exists():
                prompts = load_prompts(prompts_path)

        # Build provider from config
        provider = build_provider(config_dict)

        # Build enrichments from config
        enrichment_objects = build_enrichments(config_dict, prompts)

    elif enrichments is not None:
        # Build provider from args or auto-detect
        if provider_type:
            if provider_type == "gemini":
                provider = GeminiProvider(model=model) if model else GeminiProvider()
            else:
                raise ConfigurationError(f"Unknown provider type: {provider_type}")
        else:
            provider = _get_default_provider()

        # Build enrichment objects from inline configs
        enrichment_objects = build_enrichments({"enrichments": enrichments}, {})

    else:
        raise ConfigurationError("Either config or enrichments must be provided")

    # Calculate workers based on model rate limit if not specified
    if workers is None:
        workers = GeminiProvider.get_default_workers(provider.model_name)

    # Load input records
    records = []
    with open(input_path, newline="") as f:
        reader = csv.DictReader(f)
        input_fields = list(reader.fieldnames or [])
        for row in reader:
            records.append(row)

    if not records:
        raise ConfigurationError("No records found in input file")

    # Log function
    def log_func(msg):
        if verbose:
            print(msg)

    # Run pipeline
    runner = PipelineRunner(
        provider=provider,
        enrichments=enrichment_objects,
        log_func=log_func if verbose else None,
        max_workers=workers,
    )

    runner.run(
        records=iter(records),
        output_path=output_path,
        input_fields=input_fields,
    )

    return output_path


def enrich_records(
    records: list[dict],
    config: Optional[Union[str, Path]] = None,
    enrichments: Optional[list[dict]] = None,
    output_path: Optional[Union[str, Path]] = None,
    pk_field: Optional[str] = None,
    provider_type: Optional[str] = None,
    model: Optional[str] = None,
    workers: Optional[int] = None,
    verbose: bool = False,
) -> list[dict]:
    """Enrich a list of records with LLM-generated data.

    Use this when you have custom loading logic (e.g., joining multiple CSVs).

    Args:
        records: List of dicts to enrich
        config: Path to YAML config file (alternative to inline enrichments)
        enrichments: List of enrichment configs (alternative to config file)
        output_path: Optional path to write CSV output (if None, just returns records)
        pk_field: Primary key field for resume capability (e.g., "id"). If output_path
            exists and pk_field is set, already-processed records will be skipped.
        provider_type: Provider type: "gemini"
        model: Model name to use
        workers: Number of parallel workers (default: auto-calculated from model rate limit)
        verbose: Whether to print progress

    Returns:
        List of enriched records (dicts). If resuming, includes both previously
        processed records (from file) and newly processed records.

    Example:
        >>> # Custom loading logic
        >>> records = my_custom_loader("orgs.csv", "programs.csv")
        >>>
        >>> # Enrich and get results back
        >>> enriched = enrich_records(records, config="taskflows/taskflow.yaml")
        >>>
        >>> # With resume capability (can restart if interrupted)
        >>> enriched = enrich_records(
        ...     records,
        ...     config="taskflows/taskflow.yaml",
        ...     output_path="output.csv",
        ...     pk_field="id"
        ... )
    """
    if not records:
        raise ConfigurationError("No records provided")

    # Get input fields from first record
    input_fields = list(records[0].keys())

    # Load config or use inline enrichments
    if config is not None:
        config_path = Path(config)
        if not config_path.exists():
            raise ConfigurationError(f"Config file not found: {config_path}")

        config_dict = load_config(config_path)

        # Load prompts if specified
        prompts = {}
        if config_dict.get("prompts_file"):
            prompts_path = config_path.parent / config_dict["prompts_file"]
            if prompts_path.exists():
                prompts = load_prompts(prompts_path)

        # Build provider from config
        provider = build_provider(config_dict)

        # Build enrichments from config
        enrichment_objects = build_enrichments(config_dict, prompts)

    elif enrichments is not None:
        # Build provider from args or auto-detect
        if provider_type:
            if provider_type == "gemini":
                provider = GeminiProvider(model=model) if model else GeminiProvider()
            else:
                raise ConfigurationError(f"Unknown provider type: {provider_type}")
        else:
            provider = _get_default_provider()

        # Build enrichment objects from inline configs
        enrichment_objects = build_enrichments({"enrichments": enrichments}, {})

    else:
        raise ConfigurationError("Either config or enrichments must be provided")

    # Calculate workers based on model rate limit if not specified
    if workers is None:
        workers = GeminiProvider.get_default_workers(provider.model_name)

    # Log function
    def log_func(msg):
        if verbose:
            print(msg)

    # Handle resume: check for already-processed records
    already_processed = []
    processed_pks = set()
    if output_path is not None:
        output_path = Path(output_path)
        if output_path.exists() and pk_field is not None:
            # Read existing output to find already-processed records
            with open(output_path, newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    already_processed.append(row)
                    pk_value = row.get(pk_field, "")
                    if pk_value:
                        processed_pks.add(pk_value)

            if processed_pks and verbose:
                print(f"Resuming: {len(processed_pks)} records already processed")

    # Filter out already-processed records
    if processed_pks and pk_field:
        records_to_process = [r for r in records if r.get(pk_field, "") not in processed_pks]
        if verbose:
            skipped = len(records) - len(records_to_process)
            print(f"Skipping {skipped} already-processed records, {len(records_to_process)} remaining")
    else:
        records_to_process = records

    # If nothing to process, return what we have
    if not records_to_process:
        if verbose:
            print("All records already processed")
        return already_processed

    # If output_path provided, use the pipeline runner (writes to file)
    if output_path is not None:
        runner = PipelineRunner(
            provider=provider,
            enrichments=enrichment_objects,
            log_func=log_func if verbose else None,
            max_workers=workers,
        )
        runner.run(
            records=iter(records_to_process),
            output_path=output_path,
            input_fields=input_fields,
        )
        # Read back all results (existing + new)
        enriched = []
        with open(output_path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                enriched.append(row)
        return enriched

    # Otherwise, process in memory and return
    from concurrent.futures import ThreadPoolExecutor

    def enrich_one(row: dict) -> dict:
        enriched_row = dict(row)
        for enrichment in enrichment_objects:
            try:
                result = enrichment.enrich(enriched_row, provider)
                enriched_row.update(result)
            except Exception as e:
                if verbose:
                    print(f"Error in {enrichment.name}: {e}")
                for col in enrichment.output_columns:
                    enriched_row[col] = ""
        return enriched_row

    if verbose:
        print(f"Processing {len(records)} records with {workers} workers...")

    with ThreadPoolExecutor(max_workers=workers) as executor:
        enriched = list(executor.map(enrich_one, records))

    if verbose:
        print(f"Done. Enriched {len(enriched)} records.")

    return enriched
