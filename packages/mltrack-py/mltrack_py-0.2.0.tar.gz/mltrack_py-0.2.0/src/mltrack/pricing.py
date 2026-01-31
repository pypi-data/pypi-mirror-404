"""Pricing snapshot utilities for LLM cost calculation."""

from __future__ import annotations

import json
import logging
import os
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union
import importlib.resources as resources

logger = logging.getLogger(__name__)

LLM_MODES = {"chat", "completion", "embedding"}


def _canonical_provider(source_provider: Optional[str]) -> Optional[str]:
    if not source_provider:
        return None

    normalized = source_provider.lower()
    if normalized.startswith("vertex_ai"):
        return "vertex_ai"
    if normalized in {"openai", "text-completion-openai"}:
        return "openai"
    if normalized == "anthropic":
        return "anthropic"
    if normalized in {"bedrock", "bedrock_converse"}:
        return "bedrock"
    if normalized == "gemini":
        return "gemini"

    return normalized


def _maybe_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_litellm_snapshot(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize LiteLLM pricing JSON into a minimal snapshot."""
    models: Dict[str, Dict[str, Any]] = {}

    for model_id, spec in raw.items():
        if model_id == "sample_spec":
            continue
        if not isinstance(spec, dict):
            continue

        mode = spec.get("mode")
        if mode not in LLM_MODES:
            continue

        source_provider = spec.get("litellm_provider")
        canonical_provider = _canonical_provider(source_provider)
        if not canonical_provider:
            continue

        entry: Dict[str, Any] = {
            "canonical_provider": canonical_provider,
            "source_provider": source_provider,
            "mode": mode,
        }

        for field in ("input_cost_per_token", "output_cost_per_token", "output_cost_per_reasoning_token"):
            if field in spec:
                value = _maybe_float(spec.get(field))
                if value is not None:
                    entry[field] = value

        for field in ("max_input_tokens", "max_output_tokens", "max_tokens", "supports_prompt_caching"):
            if field in spec and spec.get(field) is not None:
                entry[field] = spec[field]

        models[str(model_id).lower()] = entry

    return {
        "schema_version": "1",
        "models": models,
    }


def needs_snapshot_refresh(
    existing_snapshot: Optional[Dict[str, Any]],
    source_sha256: str,
) -> bool:
    if not existing_snapshot:
        return True
    existing_hash = existing_snapshot.get("source_sha256")
    if not existing_hash:
        return True
    return existing_hash != source_sha256


def build_litellm_snapshot(
    raw: Dict[str, Any],
    *,
    source_url: str,
    raw_bytes: bytes,
    fetched_at: Optional[str] = None,
) -> Dict[str, Any]:
    snapshot = normalize_litellm_snapshot(raw)
    snapshot["source"] = "litellm"
    snapshot["source_url"] = source_url
    snapshot["fetched_at"] = fetched_at or datetime.now(timezone.utc).isoformat()
    snapshot["source_sha256"] = hashlib.sha256(raw_bytes).hexdigest()
    return snapshot


def _load_json_file(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_pricing_snapshot(
    snapshot_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Load a normalized pricing snapshot from disk or packaged resources."""
    path: Optional[Path] = None
    if snapshot_path:
        path = Path(snapshot_path)
    else:
        env_path = os.getenv("MLTRACK_LLM_PRICING_SNAPSHOT")
        if env_path:
            path = Path(env_path)

    if path:
        return _load_json_file(path)

    try:
        if hasattr(resources, "files"):
            data_path = resources.files("mltrack.data").joinpath("litellm_snapshot.json")
            if data_path.is_file():
                return json.loads(data_path.read_text(encoding="utf-8"))
            raise FileNotFoundError

        with resources.open_text("mltrack.data", "litellm_snapshot.json") as handle:
            return json.load(handle)
    except (FileNotFoundError, ModuleNotFoundError):
        logger.warning("No LLM pricing snapshot found; cost tracking disabled.")
        return {"schema_version": "1", "models": {}}


def resolve_model_pricing(
    snapshot: Dict[str, Any],
    model: str,
    provider: Optional[str],
) -> Optional[Dict[str, Any]]:
    if not snapshot or not model:
        return None

    models = snapshot.get("models", {})
    model_key = model.strip().lower()
    provider_key = provider.lower() if provider else None

    candidates = []
    if model_key:
        candidates.append(model_key)
        if "/" in model_key:
            candidates.append(model_key.split("/", 1)[1])
    if provider_key:
        candidates.append(f"{provider_key}/{model_key}")
        if "/" in model_key:
            stripped = model_key.split("/", 1)[1]
            candidates.append(f"{provider_key}/{stripped}")

    seen = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        entry = models.get(candidate)
        if entry and (not provider_key or entry.get("canonical_provider") == provider_key):
            return entry

    if provider_key:
        stripped = model_key.split("/", 1)[1] if "/" in model_key else model_key
        for key, entry in models.items():
            if entry.get("canonical_provider") != provider_key:
                continue
            if key == stripped or key.endswith(f"/{stripped}"):
                return entry

    return None


def calculate_cost(
    tokens: Dict[str, int],
    model: str,
    provider: str,
    snapshot: Optional[Dict[str, Any]] = None,
) -> Optional[float]:
    """Calculate cost based on token usage and the pricing snapshot."""
    if not tokens or not model or not provider:
        return None

    pricing_snapshot = snapshot or load_pricing_snapshot()
    pricing = resolve_model_pricing(pricing_snapshot, model, provider)
    if not pricing:
        return None

    input_rate = pricing.get("input_cost_per_token")
    output_rate = pricing.get("output_cost_per_token")
    if input_rate is None and output_rate is None:
        return None

    prompt_tokens = tokens.get("prompt_tokens", 0) or 0
    completion_tokens = tokens.get("completion_tokens", 0) or 0

    cost = (prompt_tokens * float(input_rate or 0)) + (completion_tokens * float(output_rate or 0))
    return round(cost, 6)
