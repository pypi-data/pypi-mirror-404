"""Codex install/detection helpers (skeleton)."""

from __future__ import annotations

import shutil
import sys
import tarfile
import urllib.request
from pathlib import Path
import subprocess
import tempfile
import platform

from bootstrap.constants import CODEX_RELEASE_BASE, DEFAULT_CODEX_VERSION


def codex_on_path() -> bool:
    """Return True if `codex` is already available on PATH."""
    # On Windows, explicitly look for codex.exe to avoid conflicts with
    # other tools named "codex" (e.g., npm packages)
    if sys.platform == "win32":
        return shutil.which("codex.exe") is not None
    return shutil.which("codex") is not None


def codex_login_status_ok(executable: Path | str = "codex") -> bool:
    """Return True if `codex login status` succeeds."""
    cmd = [str(executable), "login", "status"]
    print(f"[bootstrap] running: {cmd}", file=sys.stderr)
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False
    except OSError as e:
        print(f"[bootstrap] OSError running codex: {e}", file=sys.stderr)
        raise


def ensure_codex(version: str | None = None, download_dir: Path | None = None) -> Path:
    """Ensure codex binary is available.

    Args:
        version: Optional explicit version string to install.
        download_dir: Optional directory where the tarball should be unpacked.

    Returns:
        Path to the resolved codex executable.
    """
    if codex_on_path():
        path = shutil.which("codex")
        assert path
        return Path(path)

    resolved_dir = download_dir or Path(tempfile.mkdtemp())
    resolved_dir.mkdir(parents=True, exist_ok=True)

    url, archive_type = _build_download_url(version)

    if archive_type == "exe":
        # Windows: direct .exe download, no extraction needed
        codex_path = resolved_dir / "codex.exe"
        _download(url, codex_path)
    elif archive_type == "tar.gz":
        archive_path = resolved_dir / "codex.tar.gz"
        _download(url, archive_path)
        with tarfile.open(archive_path, "r:gz") as tf:
            tf.extractall(path=resolved_dir)
        # Unix: look for codex binary
        found_codex = next(resolved_dir.rglob("codex"), None)
        if found_codex is None:
            raise RuntimeError("codex binary not found after extraction")
        codex_path = found_codex
    else:
        raise RuntimeError(f"unsupported archive type: {archive_type}")

    codex_path.chmod(codex_path.stat().st_mode | 0o111)
    return codex_path.resolve()


def _build_download_url(version: str | None) -> tuple[str, str]:
    """Build the download URL for Codex.

    Returns:
        Tuple of (url, archive_type) where archive_type is "exe" or "tar.gz".
    """
    ver = version or DEFAULT_CODEX_VERSION or "latest"
    system = sys.platform
    machine = platform.machine().lower()

    # Determine architecture tag
    if "arm" in machine or "aarch64" in machine:
        arch = "aarch64"
    else:
        arch = "x86_64"

    # Build platform-specific URL
    # Windows uses: codex-{arch}-pc-windows-msvc.exe
    # macOS uses: codex-{arch}-apple-darwin.tar.gz
    # Linux uses: codex-{arch}-unknown-linux-gnu.tar.gz
    if system == "win32":
        filename = f"codex-{arch}-pc-windows-msvc.exe"
        archive_type = "exe"
    elif system.startswith("darwin"):
        filename = f"codex-{arch}-apple-darwin.tar.gz"
        archive_type = "tar.gz"
    elif system.startswith("linux"):
        filename = f"codex-{arch}-unknown-linux-gnu.tar.gz"
        archive_type = "tar.gz"
    else:
        raise RuntimeError(f"unsupported platform: {system}")

    if ver == "latest":
        return f"{CODEX_RELEASE_BASE}/{filename}", archive_type
    return (
        f"https://github.com/openai/codex/releases/download/{ver}/{filename}",
        archive_type,
    )


def _download(url: str, dest: Path) -> None:
    with urllib.request.urlopen(url) as resp, dest.open("wb") as fh:
        fh.write(resp.read())
