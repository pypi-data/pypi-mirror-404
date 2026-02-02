from __future__ import annotations

import importlib.metadata


def test_console_entrypoint_exists() -> None:
    """Package must expose a 'flywheel-bootstrap' console script (used by bootstrap.sh)."""

    scripts = importlib.metadata.entry_points().select(group="console_scripts")
    names = {ep.name: ep.value for ep in scripts}
    assert "flywheel-bootstrap" in names, "console script 'flywheel-bootstrap' missing"
    assert names["flywheel-bootstrap"] == "bootstrap.__main__:main"
