# Checkpoint 2 Feedback Template

This document is a repository-side template for checkpoint feedback. It separates verifiable evidence from any automated commentary.

## Submission Metadata

- Project: How Language Models Handle Ambiguous Instructions
- Course: Georgia Tech CS 4365/6365 IEC Spring 2026
- Student: Alok Patel
- Group: Solo
- Checkpoint: 2
- Repository URL: 'https://github.com/Apatel777/CS4365-llm-ambiguity'
- Evidence run directory: https://github.com/Apatel777/CS4365-llm-ambiguity/tree/main/outputs/runs
## Rubric Alignment

### Scope

- Claimed deliverables present:
  -Data: https://github.com/Apatel777/CS4365-llm-ambiguity/blob/main/data/realworld_prompts_sample.jsonl
  -Data: https://github.com/Apatel777/CS4365-llm-ambiguity/blob/main/data/synthetic_prompts.jsonl

### Match

- Does repository content match the checkpoint ask?
  -
- Evidence links:
  - `README.md`: https://github.com/Apatel777/CS4365-llm-ambiguity/blob/main/README.md
  - `INSTRUCTIONS.md`: https://github.com/Apatel777/CS4365-llm-ambiguity/blob/main/INSTRUCTIONS.md
  - `outputs/runs/<timestamp>/summary.json`: https://github.com/Apatel777/CS4365-llm-ambiguity/blob/main/outputs/runs/20260303_172833/summary.json

### Factual

- Were claims backed by repository evidence rather than unsupported statements?
  - `<TA or reviewer notes>`
- Any mismatches or missing artifacts:
  - `<fill after review>`

## TA Feedback Paste Area

Paste TA comments here verbatim after grading.

## LLM-Generated Feedback
LLM-Generated Feedback (Plan / Match / Factual)
Plan
The project presents a clear and feasible plan focused on evaluating LLM behavior under ambiguous instructions using controlled prompt variants. The current implementation supports reproducible experimentation with structured datasets, deterministic dry-run mode, consistent logging, and analysis outputs. The scope is appropriate for a solo checkpoint and has a clear path toward deeper empirical evaluation in later stages.

Match
Progress aligns well with the planned milestones for this phase. The repository now includes the expected core artifacts: prompt datasets, runner scripts, analysis scripts, documentation, and generated outputs from an executed run. This demonstrates movement from planning-only work to an operational experiment pipeline and baseline evidence generation.

Factual
Claims are supported by repository evidence, including runnable code, output logs, summaries, and plots. The project includes explicit reproduction instructions and checkpoint-oriented documentation (INSTRUCTIONS.md, README.md, output artifacts), which improves verifiability for reviewers. Conclusions are currently baseline-level and should remain framed as initial findings until expanded API-mode runs are completed.

Evidence used for this feedback

data/synthetic_prompts.jsonl
data/realworld_prompts_sample.jsonl
src/run_experiments.py
src/analyze_outputs.py
outputs/runs/latest/responses.jsonl
outputs/runs/latest/summary.json
outputs/runs/latest/summary.csv
outputs/runs/latest/plots/metric_vs_variant.png
README.md
INSTRUCTIONS.md

Confidence / caveats
Moderate-to-high confidence for implementation and reproducibility claims; lower confidence for broad behavioral conclusions until additional non-dry-run experiments are run and compared.