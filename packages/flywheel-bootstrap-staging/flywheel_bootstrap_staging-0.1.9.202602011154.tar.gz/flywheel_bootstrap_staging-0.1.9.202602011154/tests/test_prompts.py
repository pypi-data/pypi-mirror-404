"""Tests for prompt assembly helpers."""

from __future__ import annotations

from bootstrap.prompts import build_prompt_text


def test_build_prompt_includes_task_and_workspace():
    """Verify prompt combines base context, task, and workspace instructions."""
    prompt = build_prompt_text(
        server_prompt="Train a model",
        workspace_instructions="Use PyTorch",
        artifact_manifest="artifacts.json",
    )
    assert "Train a model" in prompt
    assert "Use PyTorch" in prompt
    assert "artifacts.json" in prompt


def test_build_prompt_includes_artifact_types():
    """Verify prompt includes supported artifact types."""
    prompt = build_prompt_text(
        server_prompt="test task",
        workspace_instructions="test instructions",
        artifact_manifest="flywheel_artifacts.json",
    )
    assert '"text"' in prompt
    assert '"table"' in prompt
    assert '"image"' in prompt
    assert '"json"' in prompt


def test_build_prompt_includes_command_execution_tips():
    """Verify prompt includes guidance on suppressing verbose command output."""
    prompt = build_prompt_text(
        server_prompt="test task",
        workspace_instructions="test instructions",
        artifact_manifest="artifacts.json",
    )
    assert "Command Execution:" in prompt
    # Should include quiet flag guidance
    assert "--quiet" in prompt or "-q" in prompt
