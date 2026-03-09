from __future__ import annotations

import argparse
import itertools
import os
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

os.environ.setdefault("MPLCONFIGDIR", str(Path("outputs") / ".mplconfig"))
os.environ.setdefault("XDG_CACHE_HOME", str(Path("outputs") / ".cache"))

import matplotlib
import pandas as pd

from utils import average, difflib_ratio, ensure_dir, jaccard_similarity, load_jsonl, pairwise_average, round_or_none, write_json

matplotlib.use("Agg")
import matplotlib.pyplot as plt


SIGNAL_FIELDS = ("contains_apology", "contains_questions", "refusal_flag")


def successful_texts(records: List[Dict[str, Any]]) -> List[str]:
    return [record["response_text"] for record in records if not record.get("error_info")]


def signal_consistency(records: List[Dict[str, Any]], signal_name: str) -> float | None:
    values = [record["parseable_signals"][signal_name] for record in records if not record.get("error_info")]
    if not values:
        return None
    dominant_count = max(values.count(True), values.count(False))
    return dominant_count / len(values)


def average_cross_variant_similarity(group_a: List[Dict[str, Any]], group_b: List[Dict[str, Any]]) -> Tuple[float | None, float | None]:
    texts_a = successful_texts(group_a)
    texts_b = successful_texts(group_b)
    if not texts_a or not texts_b:
        return None, None

    jaccard_scores: List[float] = []
    difflib_scores: List[float] = []
    for text_a in texts_a:
        for text_b in texts_b:
            jaccard_scores.append(jaccard_similarity(text_a, text_b))
            difflib_scores.append(difflib_ratio(text_a, text_b))
    return average(jaccard_scores), average(difflib_scores)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze response stability across prompt trials and variants.")
    parser.add_argument("--run", required=True, help="Path to a run directory such as outputs/runs/20260303_120000")
    args = parser.parse_args()

    run_dir = Path(args.run)
    responses_path = run_dir / "responses.jsonl"
    if not responses_path.exists():
        raise SystemExit(f"Could not find {responses_path}")

    records = load_jsonl(responses_path)
    if not records:
        raise SystemExit("No response records found to analyze")

    by_variant: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    by_item: Dict[str, Dict[str, List[Dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for record in records:
        key = (record["prompt_item_id"], record["variant_id"])
        by_variant[key].append(record)
        by_item[record["prompt_item_id"]][record["variant_id"]].append(record)

    summary_rows: List[Dict[str, Any]] = []
    item_level_summary: Dict[str, Dict[str, Any]] = {}

    for item_id, variant_groups in by_item.items():
        sorted_variant_ids = sorted(variant_groups.keys())
        baseline_variant_id = sorted_variant_ids[0]
        drift_map: Dict[str, Dict[str, float | None]] = {}

        for variant_id in sorted_variant_ids:
            if variant_id == baseline_variant_id:
                drift_map[variant_id] = {
                    "baseline_variant_id": baseline_variant_id,
                    "cross_variant_jaccard": 1.0,
                    "cross_variant_difflib": 1.0,
                    "interpretation_drift": 0.0,
                }
                continue

            cross_jaccard, cross_difflib = average_cross_variant_similarity(
                variant_groups[baseline_variant_id],
                variant_groups[variant_id],
            )
            drift_map[variant_id] = {
                "baseline_variant_id": baseline_variant_id,
                "cross_variant_jaccard": round_or_none(cross_jaccard),
                "cross_variant_difflib": round_or_none(cross_difflib),
                "interpretation_drift": round_or_none(None if cross_difflib is None else 1 - cross_difflib),
            }

        item_pair_rows = []
        for variant_a, variant_b in itertools.combinations(sorted_variant_ids, 2):
            cross_jaccard, cross_difflib = average_cross_variant_similarity(variant_groups[variant_a], variant_groups[variant_b])
            item_pair_rows.append(
                {
                    "variant_a": variant_a,
                    "variant_b": variant_b,
                    "cross_variant_jaccard": round_or_none(cross_jaccard),
                    "cross_variant_difflib": round_or_none(cross_difflib),
                    "interpretation_drift": round_or_none(None if cross_difflib is None else 1 - cross_difflib),
                }
            )
        item_level_summary[item_id] = {"baseline_variant_id": baseline_variant_id, "variant_pairs": item_pair_rows}

        for variant_id, records_for_variant in sorted(variant_groups.items()):
            texts = successful_texts(records_for_variant)
            row = {
                "prompt_item_id": item_id,
                "variant_id": variant_id,
                "trial_count": len(records_for_variant),
                "successful_trials": len(texts),
                "avg_length": round_or_none(average(record["parseable_signals"]["length"] for record in records_for_variant if not record.get("error_info"))),
                "avg_bullet_count": round_or_none(average(record["parseable_signals"]["bullet_count"] for record in records_for_variant if not record.get("error_info"))),
                "trial_jaccard": round_or_none(pairwise_average(texts, jaccard_similarity)),
                "trial_difflib": round_or_none(pairwise_average(texts, difflib_ratio)),
                "contains_apology_consistency": round_or_none(signal_consistency(records_for_variant, "contains_apology")),
                "contains_questions_consistency": round_or_none(signal_consistency(records_for_variant, "contains_questions")),
                "refusal_flag_consistency": round_or_none(signal_consistency(records_for_variant, "refusal_flag")),
                "ambiguity_type": records_for_variant[0]["ambiguity_type"],
                "task_type": records_for_variant[0]["task_type"],
            }
            row.update(drift_map[variant_id])
            summary_rows.append(row)

    summary_frame = pd.DataFrame(summary_rows).sort_values(["prompt_item_id", "variant_id"])
    summary_csv_path = run_dir / "summary.csv"
    summary_frame.to_csv(summary_csv_path, index=False)

    plots_dir = ensure_dir(run_dir / "plots")
    plt.figure(figsize=(12, 6))
    x_labels = [f"{row['prompt_item_id']}:{row['variant_id']}" for row in summary_rows]
    jaccard_values = [row["trial_jaccard"] if row["trial_jaccard"] is not None else 0 for row in summary_rows]
    difflib_values = [row["trial_difflib"] if row["trial_difflib"] is not None else 0 for row in summary_rows]
    plt.plot(x_labels, jaccard_values, marker="o", label="Trial Jaccard")
    plt.plot(x_labels, difflib_values, marker="s", label="Trial difflib ratio")
    plt.xticks(rotation=90)
    plt.ylabel("Similarity")
    plt.xlabel("Prompt item / variant")
    plt.ylim(0, 1.05)
    plt.title("Response Stability by Prompt Variant")
    plt.legend()
    plt.tight_layout()
    plot_path = plots_dir / "metric_vs_variant.png"
    plt.savefig(plot_path, dpi=200)
    plt.close()

    summary_json_path = run_dir / "summary.json"
    write_json(
        summary_json_path,
        {
            "run_path": str(run_dir),
            "record_count": len(records),
            "variant_summary": summary_rows,
            "item_level_drift": item_level_summary,
            "generated_files": {
                "summary_csv": str(summary_csv_path),
                "summary_json": str(summary_json_path),
                "plot": str(plot_path),
            },
        },
    )

    print(f"Analyzed {len(records)} responses from {run_dir}")
    print(f"Saved {summary_json_path}")
    print(f"Saved {summary_csv_path}")
    print(f"Saved {plot_path}")


if __name__ == "__main__":
    main()
