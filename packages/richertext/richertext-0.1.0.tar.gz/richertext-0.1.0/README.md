# RicherText

**Turn raw CSV data into enriched insights using LLMs.** Classify, label, score, summarize, and analyze your data at scale.

```
Before:                              After:
┌─────────────────────────────┐      ┌─────────────────────────────────────────────────────────┐
│ title        │ description  │      │ title        │ seniority │ department │ skills         │
├─────────────────────────────┤  →   ├─────────────────────────────────────────────────────────┤
│ Sr Engineer  │ Python, AWS  │      │ Sr Engineer  │ senior    │ engineering│ python;aws     │
│ Sales Rep    │ Outbound...  │      │ Sales Rep    │ entry     │ sales      │ communication  │
└─────────────────────────────┘      └─────────────────────────────────────────────────────────┘
```

**100 records × 8 enrichments = 800 LLM calls in ~8 seconds** with automatic rate limiting and resume capability.

---

## Quick Start

### 1. Install

```bash
pip install richertext
```

### 2. Set your API key

```bash
export GOOGLE_API_KEY="your-gemini-api-key"

# Or add to .env file (auto-loaded by richertext)
echo 'GOOGLE_API_KEY=your-gemini-api-key' >> .env
```

Get a free API key at [Google AI Studio](https://makersuite.google.com/app/apikey).

### 3. Initialize and run

```bash
richertext init my-project
cd my-project
richertext run input/job_postings_10.csv --config taskflows/job_postings_tasks.yaml -v
```

That's it. Check `output/job_postings_10_enriched.csv` for results.

---

## What You Get

The init command creates a complete working example:

```
my-project/
├── .env                              # Your API key goes here
├── taskflows/
│   └── job_postings_tasks.yaml       # Enrichment configuration
├── prompts/
│   └── job_postings_prompts.yaml     # Prompt templates
├── input/
│   ├── job_postings_10.csv           # 10 sample records
│   └── job_postings_100.csv          # 100 sample records
├── output/                           # Enriched results
└── docs/                             # Documentation
    ├── README.md
    ├── TUTORIAL.md
    └── ENRICHMENTS.md
```

The sample taskflow enriches job postings with:

| Enrichment | Type | Output |
|------------|------|--------|
| seniority | classifier | `entry`, `mid`, `senior`, `executive` |
| department | classifier | `engineering`, `sales`, `hr`, etc. |
| skills | labeler | `python;aws;sql` (multiple) |
| experience_required | scorer | `7` (1-10 scale) |
| technical_complexity | scorer | `8` (1-10 scale) |
| salary_estimate | scorer | `6` (1-10 scale) |
| candidate_profile | summarizer | "Ideal candidate is..." |
| remote_friendly | classifier | `remote`, `hybrid`, `onsite`, `unclear` (inline prompt) |

---

## Use Cases

- **Lead scoring** - Classify prospects by fit, urgency, budget
- **Customer feedback** - Sentiment, topics, urgency detection
- **Content categorization** - Auto-tag articles, support tickets, documents
- **Resume screening** - Skills extraction, experience level, role fit
- **Product reviews** - Sentiment, feature mentions, competitor comparisons
- **Survey analysis** - Theme extraction, satisfaction scoring

---

## Configuration

### Taskflow Structure

```yaml
# taskflows/job_postings_tasks.yaml
provider:
  type: gemini
  model: gemini-2.5-flash-lite  # Fast and cheap

prompts_file: ../prompts/job_postings_prompts.yaml  # External prompts

enrichments:
  - name: sentiment
    type: classifier
    prompt_key: sentiment_prompt      # References job_postings_prompts.yaml
    categories: [positive, negative, neutral]
    input_columns: [review_text]

  - name: themes
    type: labeler
    labels: [pricing, quality, support, shipping]
    input_columns: [review_text]
    prompt: |                         # Or inline prompt
      What themes appear in this review?

      {review_text}
```

### Enrichment Types

| Type | What it does | Output |
|------|--------------|--------|
| `classifier` | Pick ONE category | `sentiment_category` |
| `labeler` | Pick MULTIPLE labels | `themes_labels` (semicolon-separated) |
| `summarizer` | Condense text | `summary_summary` |
| `scorer` | Rate on a scale (1-10) | `quality_score` |
| `reasoner` | Free-form analysis | `analysis_analysis` |

### Prompts File

```yaml
# prompts/job_postings_prompts.yaml
sentiment_prompt: |
  Classify the sentiment of this review:

  {review_text}

summary_prompt: |
  Summarize in 1-2 sentences:

  {review_text}
```

Use `{column_name}` to inject CSV columns into prompts.

---

## Python API

For programmatic use without config files:

```python
from richertext import classify, summarize, score, label, reason

# Single-record functions
result = classify("I love this product!", categories=["positive", "negative"])
print(result["category"])  # "positive"

summary = summarize("Long article text here...", max_length=100)

clarity = score("Evaluate this essay", prompt="Rate the clarity of: {text}")
# 8

labels = label("Tech news about AI", labels=["tech", "politics", "sports"])
# {"labels": ["tech"]}

analysis = reason("Q3 revenue: $2.1M, down 5% YoY")
# Free-form analysis text
```

### Batch Processing

```python
from richertext import enrich_csv, enrich_records

# From CSV file
enrich_csv("reviews.csv", config="taskflows/sentiment.yaml")

# From list of dicts (custom loading)
records = [
    {"id": 1, "text": "Great product!"},
    {"id": 2, "text": "Terrible experience"},
]
enriched = enrich_records(records, config="taskflows/sentiment.yaml")

# With resume capability (restart interrupted jobs)
enriched = enrich_records(
    records,
    config="taskflows/sentiment.yaml",
    output_path="output/enriched.csv",
    pk_field="id"  # Skip already-processed records
)
```

---

## Features

### Automatic Rate Limiting

Built-in token bucket rate limiting respects Gemini API limits:

| Model | Limit | Burst |
|-------|-------|-------|
| gemini-2.5-flash-lite | 4,000 RPM | 360 req |
| gemini-2.5-flash | 1,000 RPM | 90 req |
| gemini-2.5-pro | 150 RPM | 13 req |

No 429 errors. No manual throttling.

### Parallel Processing

Worker count is automatically calculated based on the model's rate limit:

| Model | Rate Limit | Default Workers |
|-------|------------|-----------------|
| gemini-2.5-flash-lite | 4,000 RPM | 133 workers |
| gemini-2.5-flash | 1,000 RPM | 33 workers |
| gemini-2.5-pro | 150 RPM | 5 workers |

Override with `--workers` if needed:

```bash
richertext run data.csv --config job_postings_tasks.yaml --workers 50
```

### Resume Capability

Interrupted? Just re-run the same command. RicherText reads the output file, extracts the `--pk-field` values already processed, and skips those records:

```bash
# First run - processes 50 records, then interrupted (Ctrl+C)
richertext run data.csv --config job_postings_tasks.yaml --pk-field id
# Output: output/data_enriched.csv (50 rows)

# Second run - reads output file, skips 50 already done, continues with remaining
richertext run data.csv --config job_postings_tasks.yaml --pk-field id
# Output: appends to output/data_enriched.csv
```

The `--pk-field` must match a column in your CSV (default: `id`).

### Chaining Enrichments

You can reference output from earlier enrichments in later ones. This is not automatic - you must explicitly include the output column in `input_columns`:

```yaml
enrichments:
  - name: language
    type: classifier
    categories: [english, spanish, french]
    input_columns: [text]
    output_column: detected_language  # Creates 'detected_language' column

  - name: summary
    type: summarizer
    input_columns: [text, detected_language]  # Explicitly include previous output
    prompt: |
      Summarize this {detected_language} text:

      {text}
```

---

## CLI Reference

```bash
# Initialize new project
richertext init [project_name]

# Run enrichment
richertext run <input.csv> --config <taskflow.yaml> [options]

Options:
  -c, --config FILE      Taskflow config (required)
  -o, --output FILE      Output path (default: output/<input>_enriched.csv)
  -v, --verbose          Show progress
  -w, --workers N        Parallel workers (default: auto based on model)
  --pk-field FIELD       Primary key for resume (default: id)
```

---

## Troubleshooting

**"No API key found"**
```bash
export GOOGLE_API_KEY="your-key"
# Or add to .env file
```

**"Prompts file not found"**
- Path is relative to the taskflow location
- Use `../prompts/job_postings_prompts.yaml` if prompts dir is sibling to taskflows

**Rate limit errors**
- The built-in rate limiter should prevent these
- If you see 429s, reduce `--workers`

**Resuming doesn't skip records**
- Make sure `--pk-field` matches a column in your CSV
- Check that output file exists from previous run

---

## License

MIT
