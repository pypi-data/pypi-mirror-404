"""Pipeline runner - orchestrates enrichments."""

import csv
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable, Iterator, Optional


class PipelineRunner:
    """Orchestrates enrichment pipeline execution."""

    def __init__(
        self,
        provider,
        enrichments: list,
        log_func: Optional[Callable[[str], None]] = None,
        max_workers: int = 130,
    ):
        self.provider = provider
        self.enrichments = enrichments
        self.log_func = log_func
        self.max_workers = max_workers

    def _enrich_record(self, row: dict) -> dict:
        """Process a single record through all enrichments."""
        pk = row.get("ein", row.get("pk", "unknown"))
        if self.log_func:
            self.log_func(f"Processing {pk}...")

        enriched_row = dict(row)
        for enrichment in self.enrichments:
            try:
                if self.log_func:
                    self.log_func(f"  [{pk}] Running {enrichment.name}...")
                result = enrichment.enrich(enriched_row, self.provider)
                enriched_row.update(result)
            except Exception as e:
                if self.log_func:
                    self.log_func(f"  [{pk}] Error in {enrichment.name}: {e}")
                # Fill with empty values on error
                for col in enrichment.output_columns:
                    enriched_row[col] = ""

        if self.log_func:
            self.log_func(f"  [{pk}] Done.")

        return enriched_row

    def run(
        self,
        records: Iterator[dict],
        output_path: Path,
        input_fields: list,
    ) -> None:
        """
        Run all enrichments on input records and write to output CSV.

        Args:
            records: Iterator of input row dicts
            output_path: Path for output CSV
            input_fields: Original input column names
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Compute output fields: input + all enrichment outputs
        output_fields = list(input_fields)
        for enrichment in self.enrichments:
            output_fields.extend(enrichment.output_columns)

        # Convert iterator to list for parallel processing
        records_list = list(records)
        total_records = len(records_list)

        if self.log_func:
            self.log_func(f"Processing {total_records} records with {self.max_workers} workers...")

        # Track if we need to write header
        write_header = not output_path.exists()

        # Timing
        start_time = time.time()
        completed = 0

        # Process records in parallel, write in order
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # map() preserves order - results come back in submission order
            results = executor.map(self._enrich_record, records_list)

            # Write results as they complete (in order)
            with open(output_path, "a", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=output_fields, extrasaction="ignore")
                if write_header:
                    writer.writeheader()

                for enriched_row in results:
                    writer.writerow(enriched_row)
                    f.flush()
                    completed += 1

                    # Progress update every 10 records or at end
                    if self.log_func and (completed % 10 == 0 or completed == total_records):
                        elapsed = time.time() - start_time
                        rate = completed / elapsed if elapsed > 0 else 0
                        remaining = (total_records - completed) / rate if rate > 0 else 0
                        self.log_func(f"Progress: {completed}/{total_records} ({rate:.1f} rec/s, ~{remaining:.0f}s remaining)")

        # Final stats
        if self.log_func:
            total_time = time.time() - start_time
            final_rate = total_records / total_time if total_time > 0 else 0
            api_calls = total_records * len(self.enrichments)
            api_rate = api_calls / total_time if total_time > 0 else 0
            self.log_func(f"Completed {total_records} records in {total_time:.1f}s ({final_rate:.2f} rec/s, {api_rate:.1f} API calls/s)")
