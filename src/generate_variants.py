from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import pandas as pd

from schema import PromptItem, validate_unique_ids
from utils import load_jsonl


def load_items(dataset_paths: List[Path]) -> List[PromptItem]:
    items: List[PromptItem] = []
    for dataset_path in dataset_paths:
        for payload in load_jsonl(dataset_path):
            items.append(PromptItem.from_dict(payload))
    validate_unique_ids(items)
    return items


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate prompt datasets and export a flat variant table.")
    parser.add_argument(
        "--datasets",
        nargs="+",
        default=["data/synthetic_prompts.jsonl", "data/realworld_prompts_sample.jsonl"],
        help="JSONL dataset files to validate.",
    )
    parser.add_argument(
        "--out",
        default="outputs/variant_inventory.csv",
        help="Where to write the flattened variant inventory CSV.",
    )
    args = parser.parse_args()

    dataset_paths = [Path(path) for path in args.datasets]
    items = load_items(dataset_paths)

    rows = []
    for item in items:
        for variant in item.variants:
            rows.append(
                {
                    "id": item.id,
                    "source": item.source,
                    "task_type": item.task_type,
                    "ambiguity_type": item.ambiguity_type,
                    "variant_id": variant.variant_id,
                    "prompt_text": variant.prompt_text,
                    "ambiguity_notes": variant.ambiguity_notes,
                    "expected_axes": " | ".join(item.expected_axes),
                }
            )

    frame = pd.DataFrame(rows)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out_path, index=False)

    print(f"Validated {len(items)} prompt items across {len(rows)} variants.")
    print(f"Saved flattened inventory to {out_path}")


if __name__ == "__main__":
    main()
