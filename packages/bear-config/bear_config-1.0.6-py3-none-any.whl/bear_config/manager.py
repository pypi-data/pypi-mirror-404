"""Config Manager Module for Bears.

A generic configuration manager using Pydantic models
with environment-based overrides and TOML file support.
"""

from __future__ import annotations

import os
from pathlib import Path  # noqa: TC003
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ValidationError

from .common import EXCLUDE_CHECK, EnvVarConflictError, Names, Sources, default_files

if TYPE_CHECKING:
    from .dir_manager import DirectoryManager
    from .toml_handler import TomlFileHandler


class ConfigManager[ConfigType: BaseModel]:
    """A generic configuration manager with environment-based overrides.

    Configuration loading precedence (later sources override earlier):
    1. default.toml
    2. {env}.toml (e.g., dev.toml, prod.toml)
    3. local.toml
    4. Environment variables (prefixed with PROGRAM_NAME_)

    Searches in: ~/.config/{project_name}/ and ./config/{project_name}
    """

    def __init__(
        self,
        config_model: type[ConfigType],
        program_name: str,
        config_paths: list[Path] | None = None,
        file_names: list[str] | None = None,
        env: str = "dev",
    ) -> None:
        """Initialize the ConfigManager with a Pydantic model and configuration path.

        Args:
            config_model: A Pydantic model class defining the configuration schema.
            program_name: The name of the program (used for env var prefix and directory names).
            config_paths: Optional list of specific config file paths to use, must use full paths.
            file_names: Optional list of config file names to look for in order of precedence.
            env: The current environment (e.g., 'dev', 'prod') to determine which config files to load.
        """
        self._dir_manager: DirectoryManager | None = None
        self._toml_handler: TomlFileHandler | None = None
        self._config: ConfigType | None = None
        self._resolved_paths: list[Path] | None = None
        self._config_attrs: dict[str, Any] | None = None
        self._program_name = program_name
        self._names: Names | None = None
        self._model: type[ConfigType] = config_model
        self._env: str = env
        self._default_files: list[str] = file_names or default_files(self._env)
        self._config_paths: list[Path] = config_paths or self._default_paths(self._default_files)

    @property
    def config(self) -> ConfigType:
        """Load and cache configuration from files and environment variables."""
        if self._config is None:
            config_data: dict[str, Any] = {}
            for config_file in self.resolved_paths:
                file_data: dict[str, Any] = self._load_toml_file(config_file)
                if file_data:
                    config_data = self._deep_merge(config_data, file_data)
            env_overrides: dict[str, Any] = self._get_env_overrides()
            if env_overrides:
                config_data = self._deep_merge(config_data, env_overrides)
            try:
                self._config = self._model.model_validate(config_data)
            except ValidationError as e:
                raise ValueError(f"Configuration validation failed: {e}") from e
        return self._config

    @property
    def names(self) -> Names:
        """Get or create Names utility for program naming conventions."""
        if self._names is None:
            self._names = Names.create(program=self._program_name)
        return self._names

    @property
    def dir_manager(self) -> DirectoryManager:
        """Get or create a DirectoryManager for config directories."""
        if self._dir_manager is None:
            from .dir_manager import DirectoryManager  # noqa: PLC0415

            self._dir_manager = DirectoryManager(self.names.lower_name)
        return self._dir_manager

    @property
    def toml_handler(self) -> TomlFileHandler:
        """Get a TOML file handler for the first config file."""
        if self._toml_handler is None:
            from .toml_handler import TomlFileHandler  # noqa: PLC0415

            self._toml_handler = TomlFileHandler()
        return self._toml_handler

    @property
    def resolved_paths(self) -> list[Path]:
        """Get the actual config files that exist and will be loaded."""
        if self._resolved_paths is None:
            self._resolved_paths = [path for path in self._config_paths if path.is_file()]
        return self._resolved_paths

    @property
    def config_attrs(self) -> dict[str, Any]:
        """Cache all non-private attributes once."""
        if self._config_attrs is None:
            self._config_attrs = {
                attr: getattr(self.config, attr) for attr in dir(self.config) if not attr.startswith(("_", "model_"))
            }
        return self._config_attrs

    def reload(self) -> ConfigType:
        """Force reload the configuration."""
        self._config = None
        self._config_attrs = None
        self._resolved_paths = None
        self._dir_manager = None
        self._toml_handler = None
        return self.config

    def _default_paths(self, file_names: list[str]) -> list[Path]:
        """Create default configuration paths based on the project name."""
        dir_manager: DirectoryManager = self.dir_manager
        default_paths: list[Path] = [dir_manager.config(), dir_manager.local_config()]
        return [path.expanduser().resolve() / file_name for path in default_paths for file_name in file_names]

    def _convert_env_value(self, value: str) -> str | bool | list[str]:
        """Convert string environment variables to appropriate types.

        Handles booleans and lists (comma-separated). Numeric conversion
        is delegated to Pydantic's type coercion during model validation.

        Args:
            value: The string value from the environment variable.

        Returns:
            The value as bool, list, or string (Pydantic handles int/float conversion).
        """
        value = value.strip()
        if value.lower() in {"true", "false"}:
            return value.lower() == "true"
        if "," in value:
            return [item.strip() for item in value.split(",")]
        return value

    def _convert_path_to_full_name(self, parts: list[str]) -> str:
        """Convert list of parts to full environment variable name."""
        return "_".join(parts).upper()

    def _get_env_overrides(self) -> dict[str, Any]:
        """Convert environment variables to nested dictionary structure.

        Convert variables like MY_APP_DATABASE_HOST to {'database': {'host': value}}.
        Only variables starting with the program prefix are considered.

        Returns:
            A nested dictionary representing environment variable overrides.

        Raises:
            ValueError: If environment variables create conflicting nested/scalar paths.
        """
        env_config: dict[str, Any] = {}
        prefix: str = self.names.prefix

        for key, value in os.environ.items():
            if not key.startswith(prefix):
                continue

            clean_key: str = key[len(prefix) :].lower()
            parts: list[str] = clean_key.split("_")

            current: dict[str, Any] = env_config
            for i, part in enumerate(parts[:-1]):
                if part in current and not isinstance(current[part], dict):
                    conflicting_path: str = "_".join(parts[: i + 1])
                    full_path: str = "_".join(parts)
                    raise EnvVarConflictError(prefix, full_path, conflicting_path)
                current = current.setdefault(part, {})

            final_value: Any = self._convert_env_value(value)
            current[parts[-1]] = final_value
        return env_config

    def _load_toml_file(self, file_path: Path) -> dict[str, Any]:
        """Load a TOML file and return its contents using fluent TOML handler.

        Args:
            file_path: Path to the TOML file.

        Returns:
            A dictionary with the contents of the TOML file.
            Returns empty dict if file doesn't exist.

        Raises:
            ValueError: If the TOML file has invalid syntax.
        """
        if not file_path.exists() or not file_path.is_file():
            return {}
        try:
            return self.toml_handler.set_path(file_path).read()
        except ValueError as e:
            raise ValueError(f"Invalid TOML syntax in {file_path}: {e}") from e

    def _get_relevant_config_files(self) -> list[Path]:
        """Get config files in loading order for current environment."""
        file_order: list[str] = self._default_files
        relevant_files: list[Path] = []
        for file_name in file_order:
            for path in [p for p in self._config_paths if p.name == file_name]:
                relevant_files.append(path)
        return relevant_files

    def _flatten_keys(self, data: dict[str, Any], parts: list[str] | None = None) -> list[str]:
        """Recursively flatten nested dict into dotted paths."""
        parts = parts or []
        keys = []
        for key, value in data.items():
            current = [*parts, key]
            if isinstance(value, dict):
                keys.extend(self._flatten_keys(value, current))
            else:
                keys.append("_".join(current))
        return keys

    def keys_used(self) -> list[str]:
        """Extract all configuration keys used from files and environment variables."""
        all_keys: set[str] = set()

        for path in self.resolved_paths:
            data: dict[str, Any] = self._load_toml_file(path)
            all_keys.update(self._flatten_keys(data))  # <- recurse!

        env_overrides: dict[str, Any] = self._get_env_overrides()
        if env_overrides:
            all_keys.update(self._flatten_keys(env_overrides))  # <- recurse!

        return [f"{self.names.prefix}{key.upper()}" for key in sorted(all_keys)]

    def config_sources(self) -> Sources:
        """Get detailed information about config sources and their contribution.

        This is here for debugging purposes.

        Returns:
            A Sources object detailing the configuration sources.
        """
        sources = Sources(files_searched=self._config_paths.copy())
        for path in sources.files_searched:
            data: dict[str, Any] = self._load_toml_file(path)
            if data:
                sources.files_loaded.append({"path": str(path), "keys": list(data.keys())})
                sources.final_merge_order.append(str(path))
        env_overrides: dict[str, Any] = self._get_env_overrides()
        if env_overrides:
            sources.env_vars_used = [key for key in os.environ if key.startswith(self.names.prefix)]
            sources.final_merge_order.append("environment_variables")
        return sources

    def _deep_merge(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """Deep merge two dictionaries."""
        result: dict[str, Any] = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def create_default_config(
        self,
        target_path: Path | None = None,
        exclude_none: bool = True,
        exclude: list | tuple | set | None = None,
    ) -> None:
        """Create a default config file with example values.

        Args:
            target_path: Optional path to save the default config file.
                         If None, saves to local config directory as 'default.toml'.
            exclude_none: Whether to exclude fields with None values.
            exclude: Specific fields to exclude from the default config.
        """
        if not self._config_paths:
            return
        default_path: Path = target_path or self.dir_manager.local_config() / "default.toml"
        if not default_path.exists():
            default_path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(exclude, EXCLUDE_CHECK):
            exclude = set(exclude)
        try:
            with self.toml_handler.set_path(default_path) as handler:
                handler.write(self.config.model_dump(exclude_none=exclude_none, exclude=exclude))
        except Exception as e:
            raise OSError(f"Failed to create default config at {default_path}: {e}") from e

    def has_config[T](self, config_type: type[T]) -> bool:
        """Check if the current configuration has an attribute or nested class of the given type."""
        type_name: str = config_type.__name__.lower()
        return any(attr == type_name or isinstance(value, config_type) for attr, value in self.config_attrs.items())

    def get_config[T](self, config_type: type[T]) -> T | None:
        """Get the configuration of the specified type if it exists."""
        type_name: str = config_type.__name__.lower()
        for attr, value in self.config_attrs.items():
            if attr == type_name or isinstance(value, config_type):
                return value
        return None


__all__ = ["ConfigManager", "Sources"]
