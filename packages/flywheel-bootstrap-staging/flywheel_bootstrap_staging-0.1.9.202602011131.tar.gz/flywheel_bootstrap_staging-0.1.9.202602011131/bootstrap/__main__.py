"""CLI entry point for the bootstrap flow.

Usage (placeholder):
    python -m bootstrap --run-id <id> --token <token> --config /path/to/config.toml
"""

from __future__ import annotations

import argparse
import sys

from bootstrap.orchestrator import BootstrapOrchestrator, build_config


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Flywheel BYOC bootstrapper")
    parser.add_argument(
        "--run-id",
        help="Run identifier issued by the Flywheel backend (falls back to FLYWHEEL_RUN_ID)",
        default=None,
    )
    parser.add_argument(
        "--token",
        help="Capability token for authenticating to the backend (or FLYWHEEL_RUN_TOKEN)",
        default=None,
    )
    parser.add_argument(
        "--server",
        help="Backend base URL (default: http://localhost:8000 or FLYWHEEL_SERVER)",
        default=None,
    )
    parser.add_argument(
        "--config",
        help="Path to the Codex config.toml file",
        required=True,
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    config = build_config(args)
    orchestrator = BootstrapOrchestrator(config)
    return orchestrator.run()


if __name__ == "__main__":
    raise SystemExit(main())
