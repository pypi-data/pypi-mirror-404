"""Unit tests for artifact manifest parsing – defensive handling."""

from __future__ import annotations

import json
from pathlib import Path

from bootstrap.artifacts import ManifestStatus, read_manifest


class TestReadManifestDefensive:
    """read_manifest should tolerate common LLM output variations."""

    def test_valid_list(self, tmp_path: Path) -> None:
        """A well-formed JSON list is returned as-is."""
        manifest = tmp_path / "manifest.json"
        entries = [{"artifact_type": "text", "payload": {"content": "hi"}}]
        manifest.write_text(json.dumps(entries), encoding="utf-8")

        result = read_manifest(manifest)
        assert list(result.artifacts) == entries
        assert result.status == ManifestStatus.VALID
        assert result.error is None

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        """Non-existent manifest returns MISSING status."""
        result = read_manifest(tmp_path / "nope.json")
        assert list(result.artifacts) == []
        assert result.status == ManifestStatus.MISSING

    def test_dict_with_artifacts_key(self, tmp_path: Path) -> None:
        """LLM wraps the list in {"artifacts": [...]}, we unwrap it."""
        manifest = tmp_path / "manifest.json"
        entries = [{"artifact_type": "text", "payload": {"content": "hi"}}]
        manifest.write_text(json.dumps({"artifacts": entries}), encoding="utf-8")

        result = read_manifest(manifest)
        assert list(result.artifacts) == entries
        assert result.status == ManifestStatus.MALFORMED
        assert result.error is not None

    def test_dict_with_other_list_key(self, tmp_path: Path) -> None:
        """Dict wrapping with an arbitrary key containing a list is unwrapped."""
        manifest = tmp_path / "manifest.json"
        entries = [{"artifact_type": "text", "payload": {"content": "x"}}]
        manifest.write_text(json.dumps({"results": entries}), encoding="utf-8")

        result = read_manifest(manifest)
        assert list(result.artifacts) == entries
        assert result.status == ManifestStatus.MALFORMED

    def test_dict_single_artifact_wrapped_in_list(self, tmp_path: Path) -> None:
        """A single artifact dict (not in a list) gets wrapped."""
        manifest = tmp_path / "manifest.json"
        entry = {"artifact_type": "text", "payload": {"content": "single"}}
        manifest.write_text(json.dumps(entry), encoding="utf-8")

        result = read_manifest(manifest)
        assert list(result.artifacts) == [entry]
        assert result.status == ManifestStatus.MALFORMED

    def test_dict_with_artifact_type_takes_priority_over_nested_list(
        self, tmp_path: Path
    ) -> None:
        """A dict with artifact_type is treated as a single artifact even if it has nested lists."""
        manifest = tmp_path / "manifest.json"
        entry = {
            "artifact_type": "text",
            "payload": {"content": "hi", "items": ["a", "b"]},
        }
        manifest.write_text(json.dumps(entry), encoding="utf-8")

        result = read_manifest(manifest)
        assert list(result.artifacts) == [entry]
        assert result.status == ManifestStatus.MALFORMED

    def test_dict_with_multiple_list_values_prefers_artifacts_key(
        self, tmp_path: Path
    ) -> None:
        """When dict has no artifact_type and multiple list values, prefer 'artifacts' key."""
        manifest = tmp_path / "manifest.json"
        entries = [{"artifact_type": "text", "payload": {"content": "a"}}]
        other = [{"something": "else"}]
        manifest.write_text(
            json.dumps({"artifacts": entries, "other": other}), encoding="utf-8"
        )

        result = read_manifest(manifest)
        assert list(result.artifacts) == entries

    def test_dict_with_no_list_values_is_single_artifact(self, tmp_path: Path) -> None:
        """A dict with artifact_type but no list values is treated as a single artifact."""
        manifest = tmp_path / "manifest.json"
        entry = {"artifact_type": "text", "payload": {"content": "solo"}}
        manifest.write_text(json.dumps(entry), encoding="utf-8")

        result = read_manifest(manifest)
        assert list(result.artifacts) == [entry]

    def test_truncated_json_is_malformed(self, tmp_path: Path) -> None:
        """Truncated/invalid JSON is reported as malformed."""
        manifest = tmp_path / "manifest.json"
        manifest.write_text('[{"artifact_type": "text", "pay', encoding="utf-8")

        result = read_manifest(manifest)
        assert list(result.artifacts) == []
        assert result.status == ManifestStatus.MALFORMED
        assert result.error is not None
        assert "invalid JSON" in result.error

    def test_empty_file_is_malformed(self, tmp_path: Path) -> None:
        """An empty file is reported as malformed."""
        manifest = tmp_path / "manifest.json"
        manifest.write_text("", encoding="utf-8")

        result = read_manifest(manifest)
        assert list(result.artifacts) == []
        assert result.status == ManifestStatus.MALFORMED

    def test_non_json_content_is_malformed(self, tmp_path: Path) -> None:
        """Non-JSON content is reported as malformed."""
        manifest = tmp_path / "manifest.json"
        manifest.write_text("this is not json at all", encoding="utf-8")

        result = read_manifest(manifest)
        assert list(result.artifacts) == []
        assert result.status == ManifestStatus.MALFORMED

    def test_empty_list(self, tmp_path: Path) -> None:
        """An empty JSON list is VALID (just no artifacts)."""
        manifest = tmp_path / "manifest.json"
        manifest.write_text("[]", encoding="utf-8")

        result = read_manifest(manifest)
        assert list(result.artifacts) == []
        assert result.status == ManifestStatus.VALID

    def test_empty_dict_is_malformed(self, tmp_path: Path) -> None:
        """An empty dict is reported as malformed."""
        manifest = tmp_path / "manifest.json"
        manifest.write_text("{}", encoding="utf-8")

        result = read_manifest(manifest)
        assert list(result.artifacts) == []
        assert result.status == ManifestStatus.MALFORMED

    def test_scalar_value_is_malformed(self, tmp_path: Path) -> None:
        """A scalar JSON value (string, number) is reported as malformed."""
        manifest = tmp_path / "manifest.json"
        manifest.write_text('"just a string"', encoding="utf-8")

        result = read_manifest(manifest)
        assert list(result.artifacts) == []
        assert result.status == ManifestStatus.MALFORMED
