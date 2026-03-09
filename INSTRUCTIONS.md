# INSTRUCTIONS.md

This file is written for an AI workflow. A future LLM or human reviewer should be able to set up the project, run the experiment pipeline, verify generated artifacts, and extend the dataset without guessing hidden steps.

## Project Purpose

This repository implements a small, reproducible experiment framework for the solo project **How Language Models Handle Ambiguous Instructions**. The pipeline compares response stability across ambiguity types:

- `missing`: prompts omit needed constraints
- `vague`: prompts use underspecified quality goals
- `conflict`: prompts contain competing requirements

The framework supports a deterministic dry-run mode for evidence generation without API access and an API mode for real model calls.

## Repository Map

- `data/synthetic_prompts.jsonl`: 12 synthetic prompt items
- `data/realworld_prompts_sample.jsonl`: 6 summarized real-world-style prompt items
- `src/generate_variants.py`: validates datasets and exports a flat variant inventory
- `src/run_experiments.py`: runs trials and logs per-response JSONL records
- `src/analyze_outputs.py`: computes stability and drift metrics, then writes summaries and a plot
- `src/schema.py`: prompt item validation schema
- `src/utils.py`: shared helpers for JSONL, hashing, signals, and similarity
- `docs/CHECKPOINT2_FEEDBACK_LLM.md`: feedback template with evidence placeholders
- `docs/EXPERIMENT_NOTES.md`: manual note-taking template after each run

## Environment Setup

Use Python 3.10+.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Windows PowerShell activation:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## End-to-End Dry Run

Dry-run mode is the default. It produces deterministic synthetic responses so the pipeline can be demonstrated without any API credentials.

```bash
python src/run_experiments.py --mode dry-run --trials 3
python src/analyze_outputs.py --run outputs/runs/latest
```

Optional dataset inventory export:

```bash
python src/generate_variants.py
```

## API Mode

API mode uses an OpenAI-compatible chat completions endpoint.

1. Set environment variables.

```bash
export OPENAI_API_KEY="your_key_here"
export OPENAI_BASE_URL="https://api.openai.com/v1"
```

Windows PowerShell:

```powershell
$env:OPENAI_API_KEY="your_key_here"
$env:OPENAI_BASE_URL="https://api.openai.com/v1"
```

2. Run the experiment safely with explicit parameters.

```bash
python src/run_experiments.py --mode api --model gpt-4o-mini --trials 3 --temperature 0.7 --top-p 1.0 --max-tokens 256 --seed 7
python src/analyze_outputs.py --run outputs/runs/latest
```

Notes:

- If `OPENAI_API_KEY` is missing, `src/run_experiments.py` exits instead of fabricating results.
- API responses are logged as raw outputs plus extracted signals.
- The provider layer is isolated so another provider can be swapped in later.

## Generated Artifacts

Each run creates a timestamped directory under `outputs/runs/<timestamp>/` and mirrors the latest run into `outputs/runs/latest/`.

Expected generated files:

- `responses.jsonl`: one record per trial and prompt variant
- `run_config.json`: run metadata
- `summary.json`: analysis summary
- `summary.csv`: flat analysis table
- `plots/metric_vs_variant.png`: stability chart

## Output Schema Notes

Each response record in `responses.jsonl` includes:

- `run_id`, `timestamp`, `model_name`
- `prompt_item_id`, `variant_id`
- `prompt_text_hash`, `prompt_text`
- `sampling_params`
- `trial_index`
- `response_text`, `finish_reason`
- `parseable_signals`
- `error_info`

Signals extracted from each response:

- `length`
- `bullet_count`
- `contains_apology`
- `contains_questions`
- `refusal_flag`

## How to Add New Prompt Items

1. Open the appropriate dataset file in `data/`.
2. Add one JSON object per line with the required fields:
   - `id`
   - `source`
   - `task_type`
   - `ambiguity_type`
   - `base_prompt`
   - `variants`
   - `expected_axes`
3. Keep each `id` globally unique.
4. Keep each `variant_id` unique within its item.
5. Validate the dataset:

```bash
python src/generate_variants.py
```

## Reproduce Checkpoint Evidence

Run these exact commands from the repository root:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python src/run_experiments.py --mode dry-run --trials 3
python src/analyze_outputs.py --run outputs/runs/latest
```

Then verify:

- `outputs/runs/latest/responses.jsonl` exists and is non-empty
- `outputs/runs/latest/summary.json` exists
- `outputs/runs/latest/summary.csv` exists
- `outputs/runs/latest/plots/metric_vs_variant.png` exists

## What to Commit

Pre-run files that must exist:

- `data/*.jsonl`
- `src/*.py`
- `docs/*.md`
- `README.md`
- `INSTRUCTIONS.md`
- `requirements.txt`
- `.gitignore`

Generated files to commit after running dry-run checkpoint evidence:

- `outputs/runs/<timestamp>/responses.jsonl`
- `outputs/runs/<timestamp>/run_config.json`
- `outputs/runs/<timestamp>/summary.json`
- `outputs/runs/<timestamp>/summary.csv`
- `outputs/runs/<timestamp>/plots/metric_vs_variant.png`

Shareable evidence links:

- GitHub file links to the timestamped run directory contents
- A GitHub link to `README.md`
- A GitHub link to `INSTRUCTIONS.md`
- A GitHub link to `docs/CHECKPOINT2_FEEDBACK_LLM.md`
