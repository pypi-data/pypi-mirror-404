"""Tests for the ConfigManager utilities and behaviors."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003
from textwrap import dedent
import tomllib
from typing import Any

from pydantic import BaseModel
import pytest

from bear_config.manager import ConfigManager, default_files


class NestedConfig(BaseModel):
    """Nested configuration used for testing merges and lookups."""

    host: str = "localhost"
    port: int = 5432
    enabled: bool = False
    ratio: float = 1.0
    tags: list[str] = ["a"]


class AppConfig(BaseModel):
    """Top-level configuration model for testing."""

    nested: NestedConfig = NestedConfig()
    name: str = "app"
    level: str = "INFO"
    optional: str | None = None


@pytest.fixture
def config_paths(tmp_path: Path) -> list[Path]:
    """Convenience fixture that provides the standard file order."""
    return [tmp_path / "default.toml", tmp_path / "dev.toml", tmp_path / "local.toml"]


@pytest.fixture
def manager(config_paths: list[Path]) -> ConfigManager[AppConfig]:
    """Config manager instance pointed at temporary files."""
    return ConfigManager[AppConfig](
        config_model=AppConfig,
        program_name="myapp",
        config_paths=config_paths,
        env="dev",
    )


def test_default_files_includes_environment_file() -> None:
    """Environment-specific file should be inserted between default and local."""
    assert default_files("prod") == ["default.toml", "prod.toml", "local.toml"]


def test_convert_env_value(manager: ConfigManager[AppConfig]) -> None:
    """Environment strings should be coerced to useful Python types (booleans, lists).

    Numeric conversion is delegated to Pydantic's type coercion.
    """
    assert manager._convert_env_value("true") is True
    assert manager._convert_env_value("FALSE") is False
    assert manager._convert_env_value("10") == "10"  # Pydantic will convert to int
    assert manager._convert_env_value("1.25") == "1.25"  # Pydantic will convert to float
    assert manager._convert_env_value("one,two") == ["one", "two"]
    assert manager._convert_env_value("plain") == "plain"


def test_env_overrides_are_nested(monkeypatch: pytest.MonkeyPatch, manager: ConfigManager[AppConfig]) -> None:
    """Prefixed environment variables should become nested dicts."""
    monkeypatch.setenv("MYAPP_NESTED_HOST", "db.example")
    monkeypatch.setenv("MYAPP_FEATURE_FLAGS", "a,b,c")
    monkeypatch.setenv("IGNORED", "value")

    overrides = manager._get_env_overrides()

    assert overrides == {
        "nested": {"host": "db.example"},
        "feature": {"flags": ["a", "b", "c"]},
    }


def test_resolved_config_paths_filter_missing(config_paths: list[Path]) -> None:
    """Only existing config files should be considered for loading."""
    default_path, dev_path, local_path = config_paths
    default_path.write_text('name = "default"\n')
    dev_path.write_text('name = "dev"\n')

    cm = ConfigManager[AppConfig](
        config_model=AppConfig,
        program_name="myapp",
        config_paths=[default_path, dev_path, local_path],
        env="dev",
    )

    assert cm.resolved_paths == [default_path, dev_path]


def test_load_merges_files_then_environment(
    monkeypatch: pytest.MonkeyPatch,
    config_paths: list[Path],
) -> None:
    """Loading should respect file order and apply environment overrides last."""
    default_path, dev_path, local_path = config_paths
    default_path.write_text(
        dedent(
            """
            [nested]
            host = "default"
            port = 5432
            tags = ["one"]
            """
        )
    )
    dev_path.write_text(
        dedent(
            """
            [nested]
            port = 6000
            ratio = 2.5
            """
        )
    )
    local_path.write_text(
        dedent(
            """
            [nested]
            enabled = true
            tags = ["local"]
            """
        )
    )
    monkeypatch.setenv("MYAPP_NESTED_HOST", "from-env")
    monkeypatch.setenv("MYAPP_NAME", "overridden")

    cm = ConfigManager[AppConfig](
        config_model=AppConfig,
        program_name="myapp",
        config_paths=[default_path, dev_path, local_path],
        env="dev",
    )

    config = cm.config

    assert config.nested.host == "from-env"
    assert config.nested.port == 6000
    assert config.nested.ratio == pytest.approx(2.5)
    assert config.nested.enabled is True
    assert config.nested.tags == ["local"]
    assert config.name == "overridden"


def test_invalid_toml_raises_value_error(config_paths: list[Path]) -> None:
    """Invalid TOML should raise a ValueError during load."""
    bad_path = config_paths[0]
    bad_path.write_text("invalid = [\n")

    cm = ConfigManager[AppConfig](
        config_model=AppConfig,
        program_name="myapp",
        config_paths=[bad_path],
        env="dev",
    )

    with pytest.raises(ValueError, match="Invalid TOML"):
        cm._load_toml_file(bad_path)


def test_config_sources_reports_loaded_files(monkeypatch: pytest.MonkeyPatch, config_paths: list[Path]) -> None:
    """config_sources should describe what was loaded and in which order."""
    default_path, dev_path, local_path = config_paths
    default_path.write_text("[nested]\nhost = 'default'\n")
    local_path.write_text("[nested]\nport = 9000\n")
    monkeypatch.setenv("MYAPP_NESTED_HOST", "env-host")

    cm = ConfigManager[AppConfig](
        config_model=AppConfig,
        program_name="myapp",
        config_paths=[default_path, dev_path, local_path],
        env="dev",
    )

    sources = cm.config_sources()

    assert sources.files_searched == [default_path, dev_path, local_path]
    assert str(default_path) in sources.final_merge_order
    assert str(local_path) in sources.final_merge_order
    assert "environment_variables" in sources.final_merge_order
    assert any(entry["path"] == str(default_path) for entry in sources.files_loaded)
    assert any(var.startswith("MYAPP_") for var in sources.env_vars_used)


def test_reload_refreshes_cached_config(config_paths: list[Path]) -> None:
    """Reload should clear caches and pick up new file contents."""
    default_path = config_paths[0]
    default_path.write_text("[nested]\nhost = 'first'\n")

    cm = ConfigManager[AppConfig](
        config_model=AppConfig,
        program_name="myapp",
        config_paths=[default_path],
        env="dev",
    )

    assert cm.config.nested.host == "first"

    default_path.write_text("[nested]\nhost = 'second'\n")

    assert cm.reload().nested.host == "second"


def test_create_default_config_writes_file(tmp_path: Path) -> None:
    """Default config should be serialized to TOML at the requested path."""
    output_path: Path = tmp_path / "generated.toml"
    output_path.touch()
    cm: ConfigManager[AppConfig] = ConfigManager[AppConfig](
        config_model=AppConfig,
        program_name="myapp",
        config_paths=[tmp_path / "default.toml"],
        env="dev",
    )

    cm.create_default_config(target_path=output_path)

    written: dict[str, Any] = tomllib.loads(output_path.read_text())
    assert written["nested"]["host"] == "localhost"
    assert written["nested"]["port"] == 5432
    assert written["name"] == "app"
    assert "optional" not in written  # excluded because None by default


def test_create_default_config_uses_default_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """When no target is provided, default.toml should be written to the local config directory."""
    default_path = tmp_path / "default.toml"
    cm: ConfigManager[AppConfig] = ConfigManager[AppConfig](
        config_model=AppConfig,
        program_name="myapp",
        config_paths=[default_path],
        env="dev",
    )
    # Redirect the internal DirectoryManager to our temporary directory
    monkeypatch.setattr(cm.dir_manager, "local_config", lambda: tmp_path, raising=True)

    cm.create_default_config()

    contents: dict[str, Any] = tomllib.loads(default_path.read_text())
    assert contents["nested"]["host"] == "localhost"
    assert contents["name"] == "app"
    assert "optional" not in contents


def test_has_and_get_config(config_paths: list[Path]) -> None:
    """Type lookups should work for nested config classes."""
    cm: ConfigManager[AppConfig] = ConfigManager[AppConfig](
        config_model=AppConfig,
        program_name="myapp",
        config_paths=config_paths,
        env="dev",
    )

    assert cm.has_config(NestedConfig) is True
    assert cm.get_config(NestedConfig) == cm.config.nested

    class AnotherConfig(BaseModel):
        value: str = "x"

    assert cm.has_config(AnotherConfig) is False
    assert cm.get_config(AnotherConfig) is None


def test_get_relevant_config_files_respects_order(config_paths: list[Path]) -> None:
    """Only recognized file names should be returned in precedence order."""
    default_path, dev_path, local_path = config_paths
    extra: Path = default_path.with_name("extra.toml")
    cm: ConfigManager[AppConfig] = ConfigManager[AppConfig](
        config_model=AppConfig,
        program_name="myapp",
        config_paths=[local_path, extra, default_path, dev_path],
        env="dev",
    )
    assert cm._get_relevant_config_files() == [default_path, dev_path, local_path]


def test_deep_merge_combines_nested_dicts(manager: ConfigManager[AppConfig]) -> None:
    """Nested dictionaries should merge recursively."""
    base = {"nested": {"host": "db", "opts": {"retries": 1}}, "debug": False}
    override = {"nested": {"opts": {"timeout": 30}}, "debug": True}

    merged: dict[str, Any] = manager._deep_merge(base, override)

    assert merged["nested"]["host"] == "db"
    assert merged["nested"]["opts"] == {"retries": 1, "timeout": 30}
    assert merged["debug"] is True


def test_load_validation_error_surfaces_value_error(config_paths: list[Path]) -> None:
    """Invalid data should raise ValueError from load."""
    bad_path = config_paths[0]
    bad_path.write_text("nested = { port = 'not-an-int' }\n")
    cm: ConfigManager[AppConfig] = ConfigManager[AppConfig](
        config_model=AppConfig,
        program_name="myapp",
        config_paths=[bad_path],
        env="dev",
    )

    with pytest.raises(ValueError, match="Configuration validation failed"):
        _ = cm.config


def test_load_skips_directory_paths(tmp_path: Path) -> None:
    """Directories in config_paths should be filtered out from resolved_paths."""
    cfg_dir = tmp_path / "config_dir"
    cfg_dir.mkdir()
    cm: ConfigManager[AppConfig] = ConfigManager[AppConfig](
        config_model=AppConfig,
        program_name="myapp",
        config_paths=[cfg_dir],
        env="dev",
    )

    config: AppConfig = cm.config

    assert config.nested.host == "localhost"
    assert cm.resolved_paths == []  # Directories are filtered out


def test_reload_clears_resolved_paths_cache(tmp_path: Path) -> None:
    """Reload should pick up new files added after initial load."""
    cfg_file = tmp_path / "default.toml"
    cm: ConfigManager[AppConfig] = ConfigManager[AppConfig](
        config_model=AppConfig,
        program_name="myapp",
        config_paths=[cfg_file],
        env="dev",
    )

    assert cm.config.name == "app"
    cfg_file.write_text('name = "after"\n')

    reloaded = cm.reload()
    assert reloaded.name == "after"


def test_create_default_config_respects_exclude_flags(tmp_path: Path) -> None:
    """exclude_none and exclude should control emitted fields."""
    cfg_path = tmp_path / "default.toml"
    cm: ConfigManager[AppConfig] = ConfigManager[AppConfig](
        config_model=AppConfig,
        program_name="myapp",
        config_paths=[cfg_path],
        env="dev",
    )

    cm.create_default_config(target_path=cfg_path, exclude_none=True, exclude={"level"})

    contents: dict[str, Any] = tomllib.loads(cfg_path.read_text())
    assert "optional" not in contents
    assert "level" not in contents


def test_convert_env_value_additional_cases(manager: ConfigManager[AppConfig]) -> None:
    """Edge strings should still be coerced sensibly.

    Numeric conversion is delegated to Pydantic's type coercion.
    """
    assert manager._convert_env_value("1.") == "1."  # Pydantic will convert to float
    assert manager._convert_env_value("001") == "001"  # Pydantic will convert to int
    assert manager._convert_env_value("a, ,b") == ["a", "", "b"]
