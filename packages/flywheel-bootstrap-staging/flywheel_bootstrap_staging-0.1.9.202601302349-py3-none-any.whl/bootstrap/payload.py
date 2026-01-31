"""Bootstrap payload fetch/validation (skeleton)."""

from __future__ import annotations

from dataclasses import dataclass
import json
import time
import urllib.request
import urllib.error
import ssl
import http.client
from typing import Any, Mapping


@dataclass
class RepoContext:
    """Repository context for code persistence.

    Mirrors the core.models.RepoContext class but is a standalone
    definition to avoid tight coupling between bootstrap and core.
    """

    repo_url: str
    repo_owner: str
    repo_name: str
    branch_name: str
    base_branch: str
    is_fork: bool = False
    fork_source_url: str | None = None
    base_commit_sha: str | None = None
    head_commit_sha: str | None = None

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "RepoContext":
        return cls(
            repo_url=str(payload["repo_url"]),
            repo_owner=str(payload["repo_owner"]),
            repo_name=str(payload["repo_name"]),
            branch_name=str(payload["branch_name"]),
            base_branch=str(payload["base_branch"]),
            is_fork=bool(payload.get("is_fork", False)),
            fork_source_url=payload.get("fork_source_url"),
            base_commit_sha=payload.get("base_commit_sha"),
            head_commit_sha=payload.get("head_commit_sha"),
        )


@dataclass
class BootstrapPayload:
    """Representation of the backend bootstrap payload."""

    prompt: str
    repo_context: RepoContext | None = None
    github_token: str | None = None


def fetch_bootstrap_payload(
    server_url: str,
    run_id: str,
    token: str,
) -> BootstrapPayload:
    """Retrieve bootstrap payload from the backend server.

    Raises:
        NotImplementedError: placeholder until HTTP wiring is added.
    """

    url = f"{server_url.rstrip('/')}/runs/{run_id}/bootstrap"
    req = urllib.request.Request(url, headers={"X-Run-Token": token})
    payload = _urlopen_json_with_retries(
        req,
        timeout_seconds=30,
        attempts=6,
        base_delay_seconds=0.5,
    )
    inner = payload.get("payload", {})

    # Parse repo context if present
    repo_context = None
    if inner.get("repo_context"):
        repo_context = RepoContext.from_dict(inner["repo_context"])

    return BootstrapPayload(
        prompt=str(inner.get("prompt", "")),
        repo_context=repo_context,
        github_token=inner.get("github_token"),
    )


def _urlopen_json_with_retries(
    req: urllib.request.Request,
    timeout_seconds: int,
    attempts: int,
    base_delay_seconds: float,
) -> dict:
    """Best-effort JSON fetch with retries.

    Fly.io apps can be cold-started (min_machines_running=0), and network edges
    can occasionally drop connections. This helper retries common transient
    failures with exponential backoff.
    """
    last_exc: Exception | None = None
    for i in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (
            TimeoutError,
            urllib.error.URLError,
            http.client.RemoteDisconnected,
            ssl.SSLError,
        ) as exc:
            last_exc = exc
            if i == attempts - 1:
                break
            delay = base_delay_seconds * (2**i)
            time.sleep(delay)
    assert last_exc is not None
    raise last_exc
