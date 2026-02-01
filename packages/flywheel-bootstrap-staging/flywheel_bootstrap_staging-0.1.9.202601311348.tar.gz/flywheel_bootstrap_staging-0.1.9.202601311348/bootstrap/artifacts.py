"""Artifact manifest helpers."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Mapping, Sequence

logger = logging.getLogger(__name__)


class ManifestStatus(Enum):
    """Outcome of reading the artifact manifest."""

    MISSING = "missing"
    VALID = "valid"
    MALFORMED = "malformed"


@dataclass
class ManifestResult:
    """Result of reading the artifact manifest, with diagnostic info."""

    status: ManifestStatus
    artifacts: Sequence[Mapping[str, object]]
    error: str | None = None


def read_manifest(manifest_path: Path) -> ManifestResult:
    """Load artifact entries from the manifest path.

    Tolerant of common LLM output variations:
    - A well-formed JSON list is returned as-is.
    - A dict wrapping a list (e.g. ``{"artifacts": [...]}``) is unwrapped.
    - A single artifact dict is wrapped in a list.
    - Truncated / invalid JSON is reported as malformed.
    - Non-dict, non-list scalars are reported as malformed.

    Returns a ``ManifestResult`` carrying the parsed artifacts, the outcome
    status, and an optional human-readable error description for feedback.
    """
    if not manifest_path.exists():
        return ManifestResult(status=ManifestStatus.MISSING, artifacts=[])
    raw = manifest_path.read_text(encoding="utf-8")
    if not raw.strip():
        msg = "artifact manifest file is empty"
        logger.warning("%s: %s", msg, manifest_path)
        return ManifestResult(status=ManifestStatus.MALFORMED, artifacts=[], error=msg)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        msg = f"artifact manifest contains invalid JSON: {exc}"
        logger.warning("%s: %s", msg, manifest_path)
        return ManifestResult(status=ManifestStatus.MALFORMED, artifacts=[], error=msg)
    return _coerce_manifest(data, manifest_path)


def _coerce_manifest(data: object, manifest_path: Path) -> ManifestResult:
    """Best-effort coercion of parsed JSON into a list of artifact dicts."""
    if isinstance(data, list):
        return ManifestResult(status=ManifestStatus.VALID, artifacts=data)
    if isinstance(data, dict):
        return _unwrap_dict(data, manifest_path)
    msg = f"artifact manifest is a {type(data).__name__}, expected a JSON list"
    logger.warning("%s: %s", msg, manifest_path)
    return ManifestResult(status=ManifestStatus.MALFORMED, artifacts=[], error=msg)


def _unwrap_dict(data: dict[str, object], manifest_path: Path) -> ManifestResult:
    """Extract an artifact list from a dict, or treat it as a single artifact."""
    # If the dict itself looks like an artifact, treat it as one.
    # Check this BEFORE scanning for nested lists — a single artifact dict
    # like {"artifact_type": "text", "payload": {"items": [...]}} must not
    # have its nested list mistakenly extracted.
    if "artifact_type" in data:
        msg = "artifact manifest is a single artifact dict, wrapping in list"
        logger.warning("%s: %s", msg, manifest_path)
        return ManifestResult(
            status=ManifestStatus.MALFORMED, artifacts=[data], error=msg
        )
    # Prefer the "artifacts" key if present and is a list.
    if "artifacts" in data and isinstance(data["artifacts"], list):
        msg = "artifact manifest wrapped in dict with 'artifacts' key, unwrapping"
        logger.warning("%s: %s", msg, manifest_path)
        return ManifestResult(
            status=ManifestStatus.MALFORMED, artifacts=data["artifacts"], error=msg
        )
    # Fall back to the first value that is a list.
    for key, value in data.items():
        if isinstance(value, list):
            msg = f"artifact manifest wrapped in dict with '{key}' key, unwrapping"
            logger.warning("%s: %s", msg, manifest_path)
            return ManifestResult(
                status=ManifestStatus.MALFORMED, artifacts=value, error=msg
            )
    msg = "artifact manifest is a dict with no recognisable artifact data"
    logger.warning("%s: %s", msg, manifest_path)
    return ManifestResult(status=ManifestStatus.MALFORMED, artifacts=[], error=msg)
