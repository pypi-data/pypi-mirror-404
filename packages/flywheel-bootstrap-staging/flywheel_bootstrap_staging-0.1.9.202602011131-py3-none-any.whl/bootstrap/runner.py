"""Codex process launcher and stream parser (skeleton)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Iterator
import json
import subprocess
import sys


@dataclass
class CodexInvocation:
    """Command and environment prepared for invoking codex."""

    args: list[str]
    env: Mapping[str, str]
    workdir: Path
    prompt: str = ""  # Prompt to pass via stdin
    exit_code: int | None = None
    stderr_output: str = ""  # Captured stderr for debugging


@dataclass
class CodexEvent:
    """Structured event emitted by codex --json."""

    raw: dict


def build_invocation(
    codex_executable: Path,
    prompt: str,
    workdir: Path,
    env: Mapping[str, str],
    extra_flags: Iterable[str] = (),
) -> CodexInvocation:
    """Assemble the codex exec command.

    The prompt is written to a file in the workdir and passed via --prompt-file
    to avoid shell argument length limits and stdin handling issues.
    """
    # Write prompt to file in the workdir (which Codex has access to)
    prompt_file = workdir / "flywheel_prompt.txt"
    prompt_file.write_text(prompt, encoding="utf-8")

    # Use '-' to read prompt from stdin (avoids CLI arg length limits)
    args = [
        str(codex_executable),
        "exec",
        "--json",
        "--cd",
        str(workdir),
        "--skip-git-repo-check",
        *list(extra_flags),
        "-",  # Read prompt from stdin
    ]
    return CodexInvocation(args=args, env=dict(env), workdir=workdir, prompt=prompt)


def run_and_stream(invocation: CodexInvocation) -> Iterator[CodexEvent]:
    """Launch codex and yield parsed events as they arrive.

    The prompt is passed via file (referenced in args) to avoid stdin issues.
    """
    # Log the command being run (redact prompt for brevity)
    cmd_display = " ".join(invocation.args)
    print(f"[bootstrap] Running: {cmd_display}", file=sys.stderr)
    print(f"[bootstrap] Workdir: {invocation.workdir}", file=sys.stderr)
    print(f"[bootstrap] Prompt length: {len(invocation.prompt)} chars", file=sys.stderr)

    # Emit command info as first event for server-side logging
    yield CodexEvent(
        raw={
            "bootstrap_debug": "codex_launch",
            "command": invocation.args,
            "workdir": str(invocation.workdir),
            "prompt_length": len(invocation.prompt),
        }
    )

    try:
        proc = subprocess.Popen(
            invocation.args,
            cwd=invocation.workdir,
            env=invocation.env if invocation.env else None,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",  # Explicit UTF-8 for cross-platform Unicode support
            bufsize=1,
        )
    except Exception as e:
        error_msg = f"Failed to start codex process: {e}"
        print(f"[bootstrap] ERROR: {error_msg}", file=sys.stderr)
        yield CodexEvent(raw={"bootstrap_error": error_msg})
        invocation.exit_code = 127
        return

    assert proc.stdin is not None
    assert proc.stdout is not None

    # Write prompt to stdin and close it so Codex knows input is complete
    try:
        proc.stdin.write(invocation.prompt)
        proc.stdin.close()
    except Exception as e:
        error_msg = f"Failed to write prompt to stdin: {e}"
        print(f"[bootstrap] ERROR: {error_msg}", file=sys.stderr)
        yield CodexEvent(raw={"bootstrap_error": error_msg})

    for line in proc.stdout:
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            payload = {"message": line}
        yield CodexEvent(raw=payload)

    proc.wait()
    invocation.exit_code = proc.returncode

    # Always capture stderr for debugging
    stderr_content = ""
    if proc.stderr:
        stderr_content = proc.stderr.read().strip()
        invocation.stderr_output = stderr_content

    # Log exit status
    print(f"[bootstrap] Codex exited with code: {proc.returncode}", file=sys.stderr)
    if stderr_content:
        print(f"[bootstrap] Codex stderr:\n{stderr_content}", file=sys.stderr)

    # Emit detailed exit info
    yield CodexEvent(
        raw={
            "bootstrap_debug": "codex_exit",
            "exit_code": proc.returncode,
            "stderr": stderr_content if stderr_content else None,
        }
    )
