from __future__ import annotations

from typing import Any
import pytest
from bootstrap.artifacts import ManifestResult, ManifestStatus
from bootstrap.config_loader import UserConfig
from bootstrap.orchestrator import BootstrapConfig, BootstrapOrchestrator
from bootstrap.payload import BootstrapPayload
from bootstrap.runner import CodexInvocation, CodexEvent


def test_orchestrator_happy_path(monkeypatch, tmp_path):
    """End-to-end orchestration with fakes: no real network or codex."""

    workspace = tmp_path / "work"
    artifacts = [{"artifact_type": "text", "payload": {"content": "hi"}}]
    captured_env: dict[str, str] = {}
    captured_extra_flags: tuple[str, ...] = ()

    # Prepare a dummy config file
    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text("", encoding="utf-8")

    # Telemetry collectors
    heartbeats: list[dict[str, Any]] = []
    logs: list[dict[str, Any]] = []
    posted_artifacts: list[dict[str, Any]] = []
    completions: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    monkeypatch.setattr(
        "bootstrap.orchestrator.load_codex_config",
        lambda path: UserConfig(
            raw={},
            working_dir=workspace,
            sandbox_mode=None,
            approval_policy="unless-allow-listed",
            oss_provider=None,
            writable_roots=(workspace,),
            workspace_instructions="use workspace",
            instructions_source="inline",
            warnings=(),
        ),
    )
    monkeypatch.setattr("bootstrap.orchestrator.codex_on_path", lambda: True)
    monkeypatch.setattr(
        "bootstrap.orchestrator.codex_login_status_ok", lambda _path: True
    )
    monkeypatch.setattr(
        "bootstrap.orchestrator.fetch_bootstrap_payload",
        lambda server_url, run_id, token: BootstrapPayload(prompt="PROMPT"),
    )

    def fake_build_invocation(codex_executable, prompt, workdir, env, extra_flags=()):
        captured_env.update(env)
        nonlocal captured_extra_flags
        captured_extra_flags = tuple(extra_flags)
        return CodexInvocation(args=["codex", "exec"], env=env, workdir=workdir)

    def fake_run_and_stream(invocation):
        invocation.exit_code = 0
        yield CodexEvent(raw={"run_id": "codex-run-1"})
        yield CodexEvent(raw={"message": "ok"})

    monkeypatch.setattr(
        "bootstrap.orchestrator.build_invocation", fake_build_invocation
    )
    monkeypatch.setattr("bootstrap.orchestrator.run_and_stream", fake_run_and_stream)
    monkeypatch.setattr(
        "bootstrap.orchestrator.read_manifest",
        lambda path: ManifestResult(status=ManifestStatus.VALID, artifacts=artifacts),
    )

    monkeypatch.setattr(
        "bootstrap.orchestrator.post_heartbeat",
        lambda server_url, run_id, token, summary: heartbeats.append(
            {"summary": summary}
        ),
    )
    monkeypatch.setattr(
        "bootstrap.orchestrator.post_log",
        lambda server_url, run_id, token, level, message, extra: logs.append(
            {"level": level, "message": message}
        ),
    )
    monkeypatch.setattr(
        "bootstrap.orchestrator.post_artifacts",
        lambda server_url, run_id, token, entries: posted_artifacts.extend(entries),
    )
    monkeypatch.setattr(
        "bootstrap.orchestrator.post_completion",
        lambda server_url, run_id, token, summary: completions.append(
            {"summary": summary}
        ),
    )
    monkeypatch.setattr(
        "bootstrap.orchestrator.post_error",
        lambda server_url, run_id, token, reason, summary=None: errors.append(
            {"reason": reason, "summary": summary}
        ),
    )

    cfg = BootstrapConfig(
        run_id="run-123",
        capability_token="secret",
        config_path=cfg_file,
        server_url="http://server",
        run_root=tmp_path,
    )
    orchestrator = BootstrapOrchestrator(cfg)
    code = orchestrator.run()

    assert code == 0
    assert heartbeats, "expected at least one heartbeat"
    assert logs, "expected log forwarding"
    assert posted_artifacts == artifacts
    assert completions and not errors
    assert "PATH" in captured_env
    assert captured_env.get("FLYWHEEL_RUN_ID") == "run-123"
    assert captured_env.get("FLYWHEEL_RUN_TOKEN") == "secret"
    assert captured_env.get("FLYWHEEL_SERVER") == "http://server"
    assert "CODEX_HOME" in captured_env
    # With sandbox_mode=None, no sandbox flags should be added
    assert len(captured_extra_flags) == 0


def test_resolve_workspace_rejects_outside_writable(monkeypatch, tmp_path):
    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text("", encoding="utf-8")

    orchestrator = BootstrapOrchestrator(
        BootstrapConfig(
            run_id="run-1",
            capability_token="token",
            config_path=cfg_file,
            server_url="http://server",
            run_root=tmp_path,
        )
    )
    orchestrator.user_config = UserConfig(
        raw={},
        working_dir=tmp_path / "work",
        sandbox_mode="workspace-write",
        approval_policy="unless-allow-listed",
        oss_provider=None,
        writable_roots=(tmp_path / "other",),
        workspace_instructions="instr",
        instructions_source="inline",
        warnings=(),
    )

    with pytest.raises(SystemExit):
        orchestrator._resolve_workspace()


def test_resolve_workspace_expands_run_id_placeholder(tmp_path) -> None:
    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text("", encoding="utf-8")

    orchestrator = BootstrapOrchestrator(
        BootstrapConfig(
            run_id="run-xyz",
            capability_token="token",
            config_path=cfg_file,
            server_url="http://server",
            run_root=tmp_path,
        )
    )

    templated = tmp_path / "runs" / "<run_id>"
    orchestrator.user_config = UserConfig(
        raw={},
        working_dir=templated,
        sandbox_mode="workspace-write",
        approval_policy="unless-allow-listed",
        oss_provider=None,
        writable_roots=(tmp_path,),
        workspace_instructions="instr",
        instructions_source="inline",
        warnings=(),
    )

    orchestrator._resolve_workspace()
    assert orchestrator.workspace == (tmp_path / "runs" / "run-xyz").resolve()


def test_malformed_manifest_triggers_two_retry_attempts(monkeypatch, tmp_path):
    """When manifest is malformed, the orchestrator retries up to 2 times with feedback."""

    workspace = tmp_path / "work"
    good_artifacts = [{"artifact_type": "text", "payload": {"content": "hi"}}]

    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text("", encoding="utf-8")

    heartbeats: list[dict[str, Any]] = []
    logs: list[dict[str, Any]] = []
    posted_artifacts: list[dict[str, Any]] = []
    completions: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    monkeypatch.setattr(
        "bootstrap.orchestrator.load_codex_config",
        lambda path: UserConfig(
            raw={},
            working_dir=workspace,
            sandbox_mode=None,
            approval_policy="unless-allow-listed",
            oss_provider=None,
            writable_roots=(workspace,),
            workspace_instructions="use workspace",
            instructions_source="inline",
            warnings=(),
        ),
    )
    monkeypatch.setattr("bootstrap.orchestrator.codex_on_path", lambda: True)
    monkeypatch.setattr(
        "bootstrap.orchestrator.codex_login_status_ok", lambda _path: True
    )
    monkeypatch.setattr(
        "bootstrap.orchestrator.fetch_bootstrap_payload",
        lambda server_url, run_id, token: BootstrapPayload(prompt="PROMPT"),
    )

    def fake_build_invocation(codex_executable, prompt, workdir, env, extra_flags=()):
        return CodexInvocation(args=["codex", "exec"], env=env, workdir=workdir)

    def fake_run_and_stream(invocation):
        invocation.exit_code = 0
        yield CodexEvent(raw={"run_id": "codex-run-1"})
        yield CodexEvent(raw={"message": "ok"})

    monkeypatch.setattr(
        "bootstrap.orchestrator.build_invocation", fake_build_invocation
    )
    monkeypatch.setattr("bootstrap.orchestrator.run_and_stream", fake_run_and_stream)

    calls = {"manifest": 0, "retry": 0}

    def fake_read_manifest(path):
        calls["manifest"] += 1
        # First two reads return malformed, third returns good data
        if calls["manifest"] <= 2:
            return ManifestResult(
                status=ManifestStatus.MALFORMED,
                artifacts=[],
                error="artifact manifest wrapped in dict",
            )
        return ManifestResult(status=ManifestStatus.VALID, artifacts=good_artifacts)

    monkeypatch.setattr("bootstrap.orchestrator.read_manifest", fake_read_manifest)

    def fake_attempt_artifact_retry(self, manifest_path, manifest_result):
        calls["retry"] += 1

    monkeypatch.setattr(
        "bootstrap.orchestrator.BootstrapOrchestrator._attempt_artifact_retry",
        fake_attempt_artifact_retry,
    )

    monkeypatch.setattr("bootstrap.orchestrator.HEARTBEAT_INTERVAL_SECONDS", 0.01)
    monkeypatch.setattr(
        "bootstrap.orchestrator.post_heartbeat",
        lambda server_url, run_id, token, summary: heartbeats.append(
            {"summary": summary}
        ),
    )
    monkeypatch.setattr(
        "bootstrap.orchestrator.post_log",
        lambda server_url, run_id, token, level, message, extra: logs.append(
            {"level": level, "message": message}
        ),
    )
    monkeypatch.setattr(
        "bootstrap.orchestrator.post_artifacts",
        lambda server_url, run_id, token, entries: posted_artifacts.extend(entries),
    )
    monkeypatch.setattr(
        "bootstrap.orchestrator.post_completion",
        lambda server_url, run_id, token, summary: completions.append(
            {"summary": summary}
        ),
    )
    monkeypatch.setattr(
        "bootstrap.orchestrator.post_error",
        lambda server_url, run_id, token, reason, summary=None: errors.append(
            {"reason": reason, "summary": summary}
        ),
    )

    cfg = BootstrapConfig(
        run_id="run-456",
        capability_token="secret",
        config_path=cfg_file,
        server_url="http://server",
        run_root=tmp_path,
    )
    orchestrator = BootstrapOrchestrator(cfg)
    code = orchestrator.run()

    assert code == 0
    # Should have attempted retry twice (max retries = 2)
    assert calls["retry"] == 2
    # manifest read: initial + after 1st retry + after 2nd retry = 3
    assert calls["manifest"] == 3
    assert posted_artifacts == good_artifacts
    assert completions and not errors


def test_malformed_manifest_exhausts_retries_still_completes(monkeypatch, tmp_path):
    """When all retry attempts fail to produce artifacts, run still completes (no crash)."""

    workspace = tmp_path / "work"

    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text("", encoding="utf-8")

    completions: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    monkeypatch.setattr(
        "bootstrap.orchestrator.load_codex_config",
        lambda path: UserConfig(
            raw={},
            working_dir=workspace,
            sandbox_mode=None,
            approval_policy="unless-allow-listed",
            oss_provider=None,
            writable_roots=(workspace,),
            workspace_instructions="use workspace",
            instructions_source="inline",
            warnings=(),
        ),
    )
    monkeypatch.setattr("bootstrap.orchestrator.codex_on_path", lambda: True)
    monkeypatch.setattr(
        "bootstrap.orchestrator.codex_login_status_ok", lambda _path: True
    )
    monkeypatch.setattr(
        "bootstrap.orchestrator.fetch_bootstrap_payload",
        lambda server_url, run_id, token: BootstrapPayload(prompt="PROMPT"),
    )

    def fake_build_invocation(codex_executable, prompt, workdir, env, extra_flags=()):
        return CodexInvocation(args=["codex", "exec"], env=env, workdir=workdir)

    def fake_run_and_stream(invocation):
        invocation.exit_code = 0
        yield CodexEvent(raw={"run_id": "codex-run-1"})

    monkeypatch.setattr(
        "bootstrap.orchestrator.build_invocation", fake_build_invocation
    )
    monkeypatch.setattr("bootstrap.orchestrator.run_and_stream", fake_run_and_stream)

    calls = {"retry": 0}

    # Always return malformed (manifest never gets fixed)
    monkeypatch.setattr(
        "bootstrap.orchestrator.read_manifest",
        lambda path: ManifestResult(
            status=ManifestStatus.MALFORMED,
            artifacts=[],
            error="artifact manifest is empty",
        ),
    )

    def fake_attempt_artifact_retry(self, manifest_path, manifest_result):
        calls["retry"] += 1

    monkeypatch.setattr(
        "bootstrap.orchestrator.BootstrapOrchestrator._attempt_artifact_retry",
        fake_attempt_artifact_retry,
    )

    monkeypatch.setattr("bootstrap.orchestrator.HEARTBEAT_INTERVAL_SECONDS", 0.01)
    monkeypatch.setattr(
        "bootstrap.orchestrator.post_heartbeat",
        lambda server_url, run_id, token, summary: None,
    )
    monkeypatch.setattr(
        "bootstrap.orchestrator.post_log",
        lambda server_url, run_id, token, level, message, extra: None,
    )
    monkeypatch.setattr(
        "bootstrap.orchestrator.post_artifacts",
        lambda server_url, run_id, token, entries: None,
    )
    monkeypatch.setattr(
        "bootstrap.orchestrator.post_completion",
        lambda server_url, run_id, token, summary: completions.append(
            {"summary": summary}
        ),
    )
    monkeypatch.setattr(
        "bootstrap.orchestrator.post_error",
        lambda server_url, run_id, token, reason, summary=None: errors.append(
            {"reason": reason, "summary": summary}
        ),
    )

    cfg = BootstrapConfig(
        run_id="run-789",
        capability_token="secret",
        config_path=cfg_file,
        server_url="http://server",
        run_root=tmp_path,
    )
    orchestrator = BootstrapOrchestrator(cfg)
    code = orchestrator.run()

    assert code == 0
    # Exhausted all 2 retry attempts
    assert calls["retry"] == 2
    # Still completes (exit code was 0)
    assert completions and not errors
