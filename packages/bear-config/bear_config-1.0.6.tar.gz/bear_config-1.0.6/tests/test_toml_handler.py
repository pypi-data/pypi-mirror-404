"""Tests for the TOML file handler utilities."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003

import pytest

from bear_config.toml_handler import TomlFileHandler


def test_write_and_read_round_trip(tmp_path: Path) -> None:
    """Data should round-trip through write/read."""
    path: Path = tmp_path / "config.toml"
    handler = TomlFileHandler(path, touch=True)

    data = {"section": {"value": 3, "tags": ["a", "b"]}}
    handler.write(data)

    raw = path.read_text()
    assert "section" in raw
    assert handler.read() == data


def test_get_section_with_dot_notation(tmp_path: Path) -> None:
    """get_section should traverse nested dictionaries using dot notation."""
    path: Path = tmp_path / "config.toml"
    handler = TomlFileHandler(path, touch=True)
    handler.write({"tool": {"poetry": {"name": "bear"}}})

    section = handler.get_section(None, "tool.poetry")
    assert section == {"name": "bear"}

    missing = handler.get_section(None, "tool.poetry.dependencies", default={})
    assert missing == {}


def test_set_path_allows_late_binding_write_read(tmp_path: Path) -> None:
    """Handler without initial path should work after set_path."""
    path: Path = tmp_path / "late.toml"
    handler = TomlFileHandler()

    handler.set_path(path, touch=True).write({"section": {"enabled": True}})

    assert handler.read() == {"section": {"enabled": True}}


def test_context_manager_with_late_bound_path(tmp_path: Path) -> None:
    """Context manager should function after setting path later."""
    path: Path = tmp_path / "ctx.toml"
    path.write_text('name = "bear"\n')
    handler = TomlFileHandler()

    with handler.set_path(path) as h:
        data = h.read()
        data["name"] = "updated"
        h.write(data)

    assert TomlFileHandler(path).read()["name"] == "updated"


def test_invalid_toml_raises_value_error(tmp_path: Path) -> None:
    """Parsing invalid TOML should raise ValueError."""
    path = tmp_path / "config.toml"
    path.write_text("invalid = [\n")
    handler = TomlFileHandler(path)

    with pytest.raises(ValueError, match="Invalid TOML"):
        handler.read()


def test_to_dict_error_message_includes_path(tmp_path: Path) -> None:
    """to_dict should surface file path in error messages."""
    path = tmp_path / "config.toml"
    handler = TomlFileHandler(path, touch=True)
    path.write_text("a = [\n")

    with pytest.raises(ValueError, match="Invalid TOML") as excinfo:
        handler.to_dict(path.read_text())

    assert str(path) in str(excinfo.value)
