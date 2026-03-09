from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


ALLOWED_SOURCES = {"synthetic", "realworld"}
ALLOWED_AMBIGUITY_TYPES = {"missing", "vague", "conflict"}


@dataclass
class PromptVariant:
    variant_id: str
    prompt_text: str
    ambiguity_notes: str

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "PromptVariant":
        for field_name in ("variant_id", "prompt_text", "ambiguity_notes"):
            if field_name not in payload or not isinstance(payload[field_name], str) or not payload[field_name].strip():
                raise ValueError(f"Variant is missing required string field: {field_name}")
        return cls(
            variant_id=payload["variant_id"].strip(),
            prompt_text=payload["prompt_text"].strip(),
            ambiguity_notes=payload["ambiguity_notes"].strip(),
        )


@dataclass
class PromptItem:
    id: str
    source: str
    task_type: str
    ambiguity_type: str
    base_prompt: str
    variants: List[PromptVariant]
    expected_axes: List[str]

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "PromptItem":
        required_string_fields = ("id", "source", "task_type", "ambiguity_type", "base_prompt")
        for field_name in required_string_fields:
            if field_name not in payload or not isinstance(payload[field_name], str) or not payload[field_name].strip():
                raise ValueError(f"Prompt item is missing required string field: {field_name}")

        source = payload["source"].strip()
        ambiguity_type = payload["ambiguity_type"].strip()
        if source not in ALLOWED_SOURCES:
            raise ValueError(f"Unsupported source: {source}")
        if ambiguity_type not in ALLOWED_AMBIGUITY_TYPES:
            raise ValueError(f"Unsupported ambiguity type: {ambiguity_type}")

        variants_payload = payload.get("variants")
        if not isinstance(variants_payload, list) or not variants_payload:
            raise ValueError("Prompt item must include a non-empty variants list")
        variants = [PromptVariant.from_dict(item) for item in variants_payload]

        expected_axes = payload.get("expected_axes")
        if not isinstance(expected_axes, list) or not expected_axes or not all(isinstance(axis, str) and axis.strip() for axis in expected_axes):
            raise ValueError("Prompt item must include a non-empty expected_axes list of strings")

        return cls(
            id=payload["id"].strip(),
            source=source,
            task_type=payload["task_type"].strip(),
            ambiguity_type=ambiguity_type,
            base_prompt=payload["base_prompt"].strip(),
            variants=variants,
            expected_axes=[axis.strip() for axis in expected_axes],
        )


def validate_unique_ids(items: List[PromptItem]) -> None:
    item_ids = set()
    for item in items:
        if item.id in item_ids:
            raise ValueError(f"Duplicate prompt item id detected: {item.id}")
        item_ids.add(item.id)

        variant_ids = set()
        for variant in item.variants:
            if variant.variant_id in variant_ids:
                raise ValueError(f"Duplicate variant_id '{variant.variant_id}' in item '{item.id}'")
            variant_ids.add(variant.variant_id)
