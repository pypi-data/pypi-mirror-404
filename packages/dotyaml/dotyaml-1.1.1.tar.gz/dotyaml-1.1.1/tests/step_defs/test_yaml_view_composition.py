from __future__ import annotations

from pathlib import Path

import pytest

from dotyaml import load_yaml_view


def test_load_yaml_view_deep_merges_mappings_and_replaces_lists(tmp_path: Path) -> None:
    base = tmp_path / "base.yml"
    overlay = tmp_path / "overlay.yml"

    base.write_text(
        "\n".join(
            [
                "a: 1",
                "nested:",
                "  x: 1",
                "  list: [1, 2]",
            ]
        ),
        encoding="utf-8",
    )
    overlay.write_text(
        "\n".join(
            [
                "nested:",
                "  x: 2",
                "  y: 3",
                "  list: [9]",
            ]
        ),
        encoding="utf-8",
    )

    view = load_yaml_view([base, overlay], load_dotenv_first=False, dotenv_path=None)
    assert view["a"] == 1
    assert view["nested"]["x"] == 2
    assert view["nested"]["y"] == 3
    assert view["nested"]["list"] == [9]


def test_load_yaml_view_rejects_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing.yml"
    with pytest.raises(FileNotFoundError):
        load_yaml_view([missing], load_dotenv_first=False, dotenv_path=None)
