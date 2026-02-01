"""Codex config parsing helpers (skeleton)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
import tomllib


@dataclass
class UserConfig:
    """Parsed subset of Codex config relevant to bootstrap."""

    raw: Mapping[str, Any]
    working_dir: Path | None
    sandbox_mode: str | None
    approval_policy: str | None
    oss_provider: str | None
    writable_roots: tuple[Path, ...]
    workspace_instructions: str
    instructions_source: str
    warnings: tuple[str, ...] = ()


def load_codex_config(path: Path) -> UserConfig:
    """Load and extract relevant fields from the user's Codex config."""

    with path.open("rb") as fp:
        data = tomllib.load(fp)

    flywheel_raw = data.get("flywheel")
    flywheel_section: Mapping[str, Any] = (
        flywheel_raw if isinstance(flywheel_raw, Mapping) else {}
    )

    inline_instructions = _get_str(flywheel_section, "workspace_instructions")
    instructions_file = _get_path(flywheel_section, "workspace_instructions_file", path)

    warnings: list[str] = []
    if instructions_file is not None and inline_instructions:
        warnings.append(
            "workspace_instructions ignored because workspace_instructions_file is set"
        )

    if instructions_file is not None:
        try:
            instructions_text = instructions_file.read_text(encoding="utf-8").strip()
        except FileNotFoundError as exc:
            raise SystemExit(
                f"workspace_instructions_file not found: {instructions_file}"
            ) from exc
        if not instructions_text:
            raise SystemExit(
                f"workspace_instructions_file is empty: {instructions_file}"
            )
        source = "file"
    else:
        instructions_text = inline_instructions.strip() if inline_instructions else ""
        source = "inline"

    if not instructions_text:
        raise SystemExit(
            "workspace instructions are required; set [flywheel].workspace_instructions "
            "or [flywheel].workspace_instructions_file"
        )

    # Best-effort extraction; Codex config schema may evolve.
    working_dir = _get_path(data, "cd") or _get_path(data, "workspace_dir")
    sandbox_mode = (
        data.get("sandbox_mode") if isinstance(data.get("sandbox_mode"), str) else None
    )
    approval_policy = (
        data.get("approval_policy")
        if isinstance(data.get("approval_policy"), str)
        else None
    )
    oss_provider = (
        data.get("oss_provider") if isinstance(data.get("oss_provider"), str) else None
    )

    writable_roots: tuple[Path, ...] = tuple()
    sandbox_write = data.get("sandbox_workspace_write")
    if isinstance(sandbox_write, dict):
        roots = sandbox_write.get("writable_roots")
        if isinstance(roots, list):
            writable_roots = tuple(
                Path(str(r)).expanduser().resolve() for r in roots if isinstance(r, str)
            )

    return UserConfig(
        raw=data,
        working_dir=working_dir,
        sandbox_mode=sandbox_mode,
        approval_policy=approval_policy,
        oss_provider=oss_provider,
        writable_roots=writable_roots,
        workspace_instructions=instructions_text,
        instructions_source=source,
        warnings=tuple(warnings),
    )


def _get_path(
    data: Mapping[str, Any], key: str, relative_to: Path | None = None
) -> Path | None:
    value = data.get(key)
    if isinstance(value, str) and value:
        path = Path(value).expanduser()
        if not path.is_absolute() and relative_to is not None:
            path = (relative_to.parent / path).resolve()
        else:
            path = path.resolve()
        return path
    return None


def _get_str(data: Mapping[str, Any], key: str) -> str | None:
    value = data.get(key)
    if isinstance(value, str) and value:
        return value
    return None
