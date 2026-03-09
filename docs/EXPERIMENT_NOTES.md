## Recommended Run Log Format

- Run timestamp: 2026-03-03 17:28:33 (run_id: `20260303_172833`)
- Run directory: `outputs/runs/20260303_172833`
- Mode: `dry-run`
- Model: `dry-run-simulator`
- Trials per variant: `3`
- Dataset files:
  - `data/synthetic_prompts.jsonl`
  - `data/realworld_prompts_sample.jsonl`
- Notable configuration changes:
  - Used default sampling params (`temperature=0.7`, `top_p=1.0`, `max_tokens=256`, `seed=7`)
  - Deterministic dry-run provider (no external API calls)

## Observations to Capture

- Which ambiguity types produced the largest interpretation drift?
  - Highest drifts were very large in multiple categories, especially:
    - `syn_conflict_03:v3` drift `0.9455`
    - `syn_missing_01:v2` drift `0.9219`
    - `real_conflict_01:v3` drift `0.8998`
    - `real_vague_01:v2` drift `0.8693`
  - Conclusion: all three ambiguity types can cause major interpretation drift; conflict and missing were especially strong in this run.

- Which signals were most stable across repeated trials?
  - `refusal_flag_consistency` was `1.0` for all rows (most stable signal).
  - `contains_apology_consistency` and `contains_questions_consistency` were often `0.6667` to `1.0` (moderately stable).

- Did missing constraints, vague goals, and conflicting requirements behave differently?
  - Yes. Missing/conflict often showed higher drift spikes in some items.
  - Vague prompts also showed high drift in several cases (e.g., `real_vague_01` variants), but with more mixed stability across items.

- Were any outputs obviously degenerate, templated, or refusal-like?
  - Outputs were clearly templated by design (dry-run simulator format patterns).
  - No refusal-like behavior observed (`refusal_flag_consistency=1.0`).

## Evidence Links

- Summary JSON: `outputs/runs/20260303_172833/summary.json`
- Summary CSV: `outputs/runs/20260303_172833/summary.csv`
- Plot: `outputs/runs/20260303_172833/plots/metric_vs_variant.png`
- Any manual spot checks:
  - `outputs/runs/20260303_172833/responses.jsonl` (checked `syn_missing_01` and `real_conflict_01` examples)
  - `outputs/runs/20260303_172833/run_config.json`
