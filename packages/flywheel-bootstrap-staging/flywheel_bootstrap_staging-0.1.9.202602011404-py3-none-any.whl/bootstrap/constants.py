"""Shared constants for the bootstrap flow."""

from __future__ import annotations

from pathlib import Path

DEFAULT_SERVER_URL = "http://localhost:8000"
DEFAULT_RUN_ROOT = Path.home() / ".flywheel" / "runs"
DEFAULT_ARTIFACT_MANIFEST = "flywheel_artifacts.json"
HEARTBEAT_INTERVAL_SECONDS = 30
MAX_ARTIFACT_RETRIES = 2

# Environment variables that let the backend command override defaults.
ENV_SERVER_URL = "FLYWHEEL_SERVER"
ENV_RUN_ID = "FLYWHEEL_RUN_ID"
ENV_RUN_TOKEN = "FLYWHEEL_RUN_TOKEN"

# Codex download
DEFAULT_CODEX_VERSION = None  # latest
CODEX_RELEASE_BASE = "https://github.com/openai/codex/releases/latest/download"
