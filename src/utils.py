from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


WORD_RE = re.compile(r"\b\w+\b", re.UNICODE)


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL in {path} line {line_number}: {exc}") from exc
    return records


def write_jsonl(path: Path, records: Iterable[Dict[str, Any]]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=True)
        handle.write("\n")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_id_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def tokenize_words(text: str) -> List[str]:
    return WORD_RE.findall(text.lower())


def jaccard_similarity(text_a: str, text_b: str) -> float:
    words_a = set(tokenize_words(text_a))
    words_b = set(tokenize_words(text_b))
    if not words_a and not words_b:
        return 1.0
    union = words_a | words_b
    if not union:
        return 1.0
    return len(words_a & words_b) / len(union)


def difflib_ratio(text_a: str, text_b: str) -> float:
    from difflib import SequenceMatcher

    return SequenceMatcher(None, text_a, text_b).ratio()


def pairwise_average(values: List[str], metric) -> float | None:
    if len(values) < 2:
        return None
    scores: List[float] = []
    for index, text_a in enumerate(values):
        for text_b in values[index + 1 :]:
            scores.append(metric(text_a, text_b))
    if not scores:
        return None
    return sum(scores) / len(scores)


def average(values: Iterable[float]) -> float | None:
    values = list(values)
    if not values:
        return None
    return sum(values) / len(values)


def round_or_none(value: float | None, digits: int = 4) -> float | None:
    if value is None or math.isnan(value):
        return None
    return round(value, digits)


def extract_signals(text: str) -> Dict[str, Any]:
    stripped = text.strip()
    bullet_count = 0
    question_marks = 0
    for line in stripped.splitlines():
        line = line.strip()
        if line.startswith(("-", "*")):
            bullet_count += 1
        elif re.match(r"^\d+\.\s", line):
            bullet_count += 1
        question_marks += line.count("?")

    lowered = stripped.lower()
    refusal_patterns = (
        "i can't help",
        "i cannot help",
        "i won’t help",
        "i won't help",
        "cannot comply",
        "cannot assist",
        "refuse",
    )
    apology_patterns = ("sorry", "apologize", "apologies")

    return {
        "length": len(stripped),
        "bullet_count": bullet_count,
        "contains_apology": any(token in lowered for token in apology_patterns),
        "contains_questions": question_marks > 0,
        "refusal_flag": any(token in lowered for token in refusal_patterns),
    }


def copy_latest_run(run_dir: Path, latest_dir: Path) -> None:
    if latest_dir.exists():
        shutil.rmtree(latest_dir)
    shutil.copytree(run_dir, latest_dir)

