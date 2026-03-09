from __future__ import annotations

import argparse
import json
import os
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

from schema import PromptItem, validate_unique_ids
from utils import copy_latest_run, ensure_dir, extract_signals, load_jsonl, run_id_timestamp, sha256_text, utc_timestamp, write_json, write_jsonl


@dataclass
class ProviderResponse:
    response_text: str
    finish_reason: Optional[str]
    error_info: Optional[Dict[str, Any]]


class DryRunProvider:
    def __init__(self, model_name: str, seed: Optional[int]) -> None:
        self.model_name = model_name
        self.seed = seed if seed is not None else 0

    def generate(
        self,
        item: PromptItem,
        prompt_text: str,
        trial_index: int,
        sampling_params: Dict[str, Any],
    ) -> ProviderResponse:
        local_seed = sha256_text(
            json.dumps(
                {
                    "model": self.model_name,
                    "item_id": item.id,
                    "ambiguity_type": item.ambiguity_type,
                    "prompt_text": prompt_text,
                    "trial_index": trial_index,
                    "seed": self.seed,
                },
                sort_keys=True,
            )
        )
        rng = random.Random(int(local_seed[:16], 16))
        style = rng.choice(["brief", "bullets", "questioning"])
        qualifier = rng.choice(["likely", "reasonable", "default", "conservative"])
        output_lines: List[str] = []

        if style == "bullets":
            output_lines.append(f"- Interpreted goal: provide a {qualifier} response to the request.")
            output_lines.append(f"- Assumption focus: {rng.choice(item.expected_axes)}.")
            output_lines.append(f"- Ambiguity type observed: {item.ambiguity_type}.")
            if item.ambiguity_type == "conflict":
                output_lines.append("- Resolution choice: prioritize the most explicit safety or formatting requirement.")
            elif item.ambiguity_type == "missing":
                output_lines.append("- Filled gap: inferred omitted constraints from common task defaults.")
            else:
                output_lines.append("- Clarification strategy: narrow the vague objective into a concrete deliverable.")
        elif style == "questioning":
            output_lines.append(f"I can answer this, but the prompt leaves room for interpretation around {rng.choice(item.expected_axes)}.")
            output_lines.append(f"My working assumption is a {qualifier} interpretation that matches the stated task type: {item.task_type}.")
            output_lines.append("Would you want the answer optimized for speed or completeness?")
        else:
            output_lines.append(
                f"This dry-run response simulates an LLM choosing a {qualifier} interpretation for a {item.task_type} task with {item.ambiguity_type} ambiguity."
            )
            output_lines.append(f"It assumes variation may appear in {rng.choice(item.expected_axes)} and keeps the answer concise for reproducibility.")

        if rng.random() < 0.18:
            output_lines.append("Sorry if that interpretation is narrower than intended.")

        return ProviderResponse(
            response_text="\n".join(output_lines),
            finish_reason="stop",
            error_info=None,
        )


class OpenAICompatibleProvider:
    def __init__(self, model_name: str, api_key: str, base_url: str) -> None:
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def generate(
        self,
        item: PromptItem,
        prompt_text: str,
        trial_index: int,
        sampling_params: Dict[str, Any],
    ) -> ProviderResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": "You are participating in a controlled ambiguity-handling experiment. Answer the user prompt directly.",
                },
                {"role": "user", "content": prompt_text},
            ],
            "temperature": sampling_params["temperature"],
            "top_p": sampling_params["top_p"],
            "max_tokens": sampling_params["max_tokens"],
        }
        if sampling_params.get("seed") is not None:
            payload["seed"] = sampling_params["seed"] + trial_index

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=90,
            )
            response.raise_for_status()
            body = response.json()
            choice = body["choices"][0]
            message = choice["message"]["content"]
            return ProviderResponse(
                response_text=message,
                finish_reason=choice.get("finish_reason"),
                error_info=None,
            )
        except Exception as exc:  # pragma: no cover - error path is data oriented
            return ProviderResponse(
                response_text="",
                finish_reason=None,
                error_info={"type": exc.__class__.__name__, "message": str(exc)},
            )


def load_items(dataset_paths: List[Path]) -> List[PromptItem]:
    items: List[PromptItem] = []
    for dataset_path in dataset_paths:
        for payload in load_jsonl(dataset_path):
            items.append(PromptItem.from_dict(payload))
    validate_unique_ids(items)
    return items


def build_provider(mode: str, model_name: str, seed: Optional[int]):
    if mode == "dry-run":
        return DryRunProvider(model_name=model_name, seed=seed)

    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is required for --mode api")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    return OpenAICompatibleProvider(model_name=model_name, api_key=api_key, base_url=base_url)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ambiguity experiments and log responses.")
    parser.add_argument("--mode", choices=["dry-run", "api"], default="dry-run", help="Execution mode.")
    parser.add_argument("--trials", type=int, default=3, help="Number of trials per prompt variant.")
    parser.add_argument(
        "--datasets",
        nargs="+",
        default=["data/synthetic_prompts.jsonl", "data/realworld_prompts_sample.jsonl"],
        help="JSONL dataset files to include.",
    )
    parser.add_argument("--model", default="dry-run-simulator", help="Model identifier recorded in outputs.")
    parser.add_argument("--temperature", type=float, default=0.7, help="Sampling temperature.")
    parser.add_argument("--top-p", dest="top_p", type=float, default=1.0, help="Sampling top-p.")
    parser.add_argument("--max-tokens", dest="max_tokens", type=int, default=256, help="Maximum generated tokens.")
    parser.add_argument("--seed", type=int, default=7, help="Base random seed when supported.")
    args = parser.parse_args()

    if args.trials < 1:
        raise SystemExit("--trials must be at least 1")

    dataset_paths = [Path(path) for path in args.datasets]
    items = load_items(dataset_paths)
    provider = build_provider(args.mode, args.model, args.seed)

    run_id = run_id_timestamp()
    run_dir = ensure_dir(Path("outputs") / "runs" / run_id)
    latest_dir = Path("outputs") / "runs" / "latest"
    responses_path = run_dir / "responses.jsonl"

    sampling_params = {
        "temperature": args.temperature,
        "top_p": args.top_p,
        "max_tokens": args.max_tokens,
        "seed": args.seed,
    }

    response_records: List[Dict[str, Any]] = []
    for item in items:
        for variant in item.variants:
            for trial_index in range(1, args.trials + 1):
                provider_response = provider.generate(
                    item=item,
                    prompt_text=variant.prompt_text,
                    trial_index=trial_index,
                    sampling_params=sampling_params,
                )
                response_records.append(
                    {
                        "run_id": run_id,
                        "timestamp": utc_timestamp(),
                        "model_name": args.model,
                        "prompt_item_id": item.id,
                        "variant_id": variant.variant_id,
                        "prompt_text_hash": sha256_text(variant.prompt_text),
                        "prompt_text": variant.prompt_text,
                        "sampling_params": sampling_params,
                        "trial_index": trial_index,
                        "response_text": provider_response.response_text,
                        "finish_reason": provider_response.finish_reason,
                        "parseable_signals": extract_signals(provider_response.response_text),
                        "error_info": provider_response.error_info,
                        "source": item.source,
                        "task_type": item.task_type,
                        "ambiguity_type": item.ambiguity_type,
                        "expected_axes": item.expected_axes,
                    }
                )

    write_jsonl(responses_path, response_records)
    write_json(
        run_dir / "run_config.json",
        {
            "run_id": run_id,
            "mode": args.mode,
            "model_name": args.model,
            "datasets": [str(path) for path in dataset_paths],
            "trials": args.trials,
            "sampling_params": sampling_params,
            "record_count": len(response_records),
        },
    )
    copy_latest_run(run_dir, latest_dir)

    print(f"Wrote {len(response_records)} response records to {responses_path}")
    print(f"Latest run snapshot updated at {latest_dir}")


if __name__ == "__main__":
    main()
