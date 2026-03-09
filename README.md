# How Language Models Handle Ambiguous Instructions

This repository contains the coding framework for the Georgia Tech CS 4365/6365 IEC Spring 2026 solo project by Alok Patel. It tests how language model outputs vary when prompts are ambiguous because they are missing constraints, use vague goals, or contain conflicting requirements.

The pipeline is intentionally small and reproducible:

1. Load JSONL prompt datasets with controlled variants.
2. Run repeated trials in deterministic `dry-run` mode or `api` mode.
3. Log each response with prompt hashes, sampling metadata, and extracted signals.
4. Analyze within-variant stability and across-variant interpretation drift.
5. Save machine-readable summaries plus a simple plot under `outputs/runs/`.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python src/run_experiments.py --mode dry-run --trials 3
python src/analyze_outputs.py --run outputs/runs/latest
```

Optional dataset validation:

```bash
python src/generate_variants.py
```

## Key Files

- `data/`: synthetic and summarized real-world prompt datasets
- `src/run_experiments.py`: experiment runner
- `src/analyze_outputs.py`: metric computation and plot generation
- `INSTRUCTIONS.md`: AI-oriented setup and reproduction guide
- `docs/CHECKPOINT2_FEEDBACK_LLM.md`: checkpoint feedback template

## Output Summary

Each run writes to `outputs/runs/<timestamp>/`:

- `responses.jsonl`
- `run_config.json`
- `summary.json`
- `summary.csv`
- `plots/metric_vs_variant.png`

`outputs/runs/latest/` is refreshed to mirror the newest run for convenience.
