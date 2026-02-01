"""Common validators for Bear Config models."""

from __future__ import annotations

import fcntl
from pathlib import Path
import re
from typing import TYPE_CHECKING, Any, Final, NamedTuple, Self
import unicodedata

from pydantic import BaseModel, Field, field_validator

if TYPE_CHECKING:
    from collections.abc import Callable


class UnsetPath(Path):
    """A sentinel class to represent an unset path."""

    def __new__(cls, *args: Any, **kwargs: Any) -> Self:  # noqa: ARG004, D102
        return super().__new__(cls, "<UNSET>")


NULL_CHOICES: set[str] = {"null", "none", ""}
DASH: str = "-"
EMPTY_STRING: str = ""
EXCLUDE_CHECK: Final = (list, tuple)
UNSET = UnsetPath()
EXCLUSIVE_LOCK: int = fcntl.LOCK_EX
SHARED_LOCK: int = fcntl.LOCK_SH
UNLOCK: int = fcntl.LOCK_UN

TomlData = dict[str, Any]


def get_config_path() -> Path:
    """Get the path to the configuration directory based on the operating system."""
    import os  # noqa: PLC0415

    if "XDG_CONFIG_HOME" in os.environ:
        return Path(os.environ["XDG_CONFIG_HOME"])
    if "APPDATA" in os.environ:
        return Path(os.environ["APPDATA"])
    return Path.home() / ".config"


PATH_TO_DOWNLOADS: Path = Path.home() / "Downloads"
"""Path to the Downloads folder."""
PATH_TO_PICTURES: Path = Path.home() / "Pictures"
"""Path to the Pictures folder."""
PATH_TO_DOCUMENTS: Path = Path.home() / "Documents"
"""Path to the Documents folder."""
PATH_TO_HOME: Path = Path.home()
"""Path to the user's home directory."""
PATH_TO_CONFIG: Path = get_config_path()
"""Path to the configuration directory based on the operating system."""


class EnvVarConflictError(ValueError):
    """Raised when there is a conflict in environment variable nesting."""

    def __init__(self, prefix: str, full_path: str, conflicting_path: str) -> None:
        """Initialize the error with details about the conflict."""
        super().__init__(
            f"Environment variable conflict: {prefix}{full_path.upper()} "
            f"tries to nest under {prefix}{conflicting_path.upper()}, "
            f"but that variable already has a scalar value. "
            f"Remove one of these conflicting variables."
        )


def _program_name(name: str) -> str:
    return slugify(name, "_")


def _lower_name(name: str) -> str:
    return _program_name(name).lower()


def _prefix(name: str) -> str:
    return f"{_program_name(name)}_".upper()


class Names(NamedTuple):
    """Dataclass to hold normalized names for a configuration program."""

    program: str
    lower_name: str
    prefix: str

    @classmethod
    def create(cls, program: str) -> Names:
        """Create a Names instance with normalized values."""
        return cls(
            program=_program_name(program),
            lower_name=_lower_name(program),
            prefix=_prefix(program),
        )


class Sources(BaseModel):
    """Model to represent configuration sources for debugging purposes."""

    files_loaded: list[dict[str, Any]] = Field(default_factory=list)
    files_searched: list[Path] = Field(default_factory=list)
    env_vars_used: list[str] = Field(default_factory=list)
    final_merge_order: list[str] = Field(default_factory=list)


def slugify(value: str, sep: str = DASH) -> str:
    """Return an ASCII slug for ``value``.

    Args:
        value: String to normalize.
        sep: Character used to replace whitespace and punctuation.

    Returns:
        A sluggified version of ``value``.
    """
    value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", EMPTY_STRING, value.lower())
    return re.sub(r"[-_\s]+", sep, value).strip("-_")


def nullable_string_validator(field_name: str) -> Callable[..., str | None]:
    """Create a validator that converts 'null' strings to None."""

    @field_validator(field_name)
    @classmethod
    def _validate(cls: object, v: str | None) -> str | None:  # noqa: ARG001
        if v is None:
            return None
        if isinstance(v, str) and v.lower() in NULL_CHOICES:
            return None
        return v

    return _validate


def default_files(env: str) -> list[str]:
    """Get the default configuration file names including environment-specific file."""
    default_files: list[str] = ["default.toml", "local.toml"]
    default_files.insert(1, f"{env}.toml")
    return default_files
