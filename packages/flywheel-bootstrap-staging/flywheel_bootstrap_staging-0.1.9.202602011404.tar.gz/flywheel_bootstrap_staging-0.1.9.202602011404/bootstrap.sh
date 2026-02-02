#!/usr/bin/env bash
# Thin shim to invoke the Python bootstrapper via uvx.
#
# Flow:
#   1) ensure uvx is installed (install via official curl script if missing)
#   2) invoke uvx with the local bootstrap package as the source
#   3) pass through all user arguments
#
# Usage:
#   ./bootstrap.sh --run-id <id> --token <token> --config /path/to/config.toml

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PKG_PATH="$REPO_ROOT/project/bootstrap"

ensure_uvx() {
  if command -v uvx >/dev/null 2>&1; then
    return
  fi
  echo "uvx not found; installing via https://astral.sh/uv/install.sh ..." >&2
  # Official installer; defaults to ~/.cargo/bin/uv
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Refresh PATH for common install location
  export PATH="$HOME/.cargo/bin:$PATH"
  if ! command -v uvx >/dev/null 2>&1; then
    echo "bootstrap: uvx still not found after install; please ensure it is on PATH." >&2
    exit 1
  fi
}

ensure_uvx

PKG_FROM="${FLYWHEEL_BOOTSTRAP_PACKAGE:-$PKG_PATH}"
uvx --no-cache --from "$PKG_FROM" flywheel-bootstrap "$@"

# No-op comment to bump version detection (keeps BYOC and provisioned aligned)
