"""Heartbeat, log, and artifact POST helpers (skeleton)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Mapping, Sequence
import json
import time
import urllib.request
import urllib.error
import ssl
import http.client
import sys

# Defaults are tuned to be tolerant of transient backend stalls.
READ_TIMEOUT_SECONDS = 30
MAX_ATTEMPTS = 3
BASE_DELAY_SECONDS = 0.5


def utcnow() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(tz=timezone.utc)


def post_heartbeat(
    server_url: str, run_id: str, token: str, summary: str | None
) -> None:
    """Send a heartbeat to the backend."""
    _post(
        f"{server_url.rstrip('/')}/runs/{run_id}/heartbeat",
        token,
        {"observed_at": utcnow().isoformat(), "summary": summary},
    )


def post_log(
    server_url: str,
    run_id: str,
    token: str,
    level: str,
    message: str,
    extra: Mapping[str, object] | None = None,
) -> None:
    """Send a log entry to the backend."""
    _post(
        f"{server_url.rstrip('/')}/runs/{run_id}/logs",
        token,
        {
            "created_at": utcnow().isoformat(),
            "level": level,
            "message": message,
            "extra": extra or {},
        },
    )


def post_artifacts(
    server_url: str,
    run_id: str,
    token: str,
    artifacts: Sequence[Mapping[str, object]],
) -> None:
    """Send artifact manifest entries to the backend."""
    for artifact in artifacts:
        payload: Mapping[str, object] | object = artifact
        if isinstance(artifact, Mapping):
            inner = artifact.get("payload", artifact)
            if isinstance(inner, Mapping):
                payload = inner
        _post(
            f"{server_url.rstrip('/')}/runs/{run_id}/artifacts",
            token,
            {
                "artifact_type": str(artifact.get("artifact_type", "unknown")),
                "payload": payload,
            },
        )


def post_completion(server_url: str, run_id: str, token: str, summary: str) -> None:
    """Mark run complete."""
    _post(
        f"{server_url.rstrip('/')}/runs/{run_id}/complete",
        token,
        {"summary": summary},
    )


def post_error(
    server_url: str, run_id: str, token: str, reason: str, summary: str | None = None
) -> None:
    """Mark run errored."""
    _post(
        f"{server_url.rstrip('/')}/runs/{run_id}/error",
        token,
        {"summary": summary or "", "reason": reason},
    )


def _post(url: str, token: str, body: Mapping[str, object]) -> None:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "X-Run-Token": token,
        },
        method="POST",
    )
    success = _urlopen_with_retries(
        req,
        timeout_seconds=READ_TIMEOUT_SECONDS,
        attempts=MAX_ATTEMPTS,
        base_delay_seconds=BASE_DELAY_SECONDS,
    )
    if not success:
        # Best-effort: log locally but do not raise, to avoid failing the run on transient stalls.
        print(f"telemetry POST to {url} failed after retries", file=sys.stderr)


def _urlopen_with_retries(
    req: urllib.request.Request,
    timeout_seconds: int,
    attempts: int,
    base_delay_seconds: float,
) -> bool:
    """Best-effort POST with retries for transient network errors."""
    for i in range(attempts):
        try:
            with urllib.request.urlopen(
                req, timeout=timeout_seconds
            ) as resp:  # pragma: no cover - network
                resp.read()
            return True
        except (
            TimeoutError,
            urllib.error.URLError,
            http.client.RemoteDisconnected,
            ssl.SSLError,
        ):
            if i == attempts - 1:
                break
            delay = base_delay_seconds * (2**i)
            time.sleep(delay)
    return False
