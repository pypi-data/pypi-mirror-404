from __future__ import annotations

from enum import IntEnum
from importlib.metadata import PackageNotFoundError, distribution, version
from typing import Final, Literal, NamedTuple

type _BumpType = Literal["major", "minor", "patch"]
_VALID_BUMP_TYPES: Final[list[_BumpType]] = ["major", "minor", "patch"]
_NULL_VER: Final = "0.0.0"
_NULL_TUP: Final = (0, 0, 0)
_ALL_PARTS: Final = 3
VERSION_CHECK: set[str] = {"-v", "--version"}

PACKAGE_NAME: Literal["bear-config"] = "bear-config"
PROJECT_NAME: Literal["bear_config"] = "bear_config"
PROJECT_UPPER: Literal["BEAR_CONFIG"] = "BEAR_CONFIG"
ENV_VARIABLE: Literal["BEAR_CONFIG_ENV"] = "BEAR_CONFIG_ENV"


class ExitCode(IntEnum):
    """An enumeration of common exit codes used in shell commands."""

    SUCCESS = 0
    """An exit code indicating success."""
    FAILURE = 1
    """An exit code indicating a general error."""
    MISUSE_OF_SHELL_COMMAND = 2
    """An exit code indicating misuse of a shell command."""
    COMMAND_CANNOT_EXECUTE = 126
    """An exit code indicating that the command invoked cannot execute."""
    COMMAND_NOT_FOUND = 127
    """An exit code indicating that the command was not found."""
    INVALID_ARGUMENT_TO_EXIT = 128
    """An exit code indicating an invalid argument to exit."""
    SCRIPT_TERMINATED_BY_CONTROL_C = 130
    """An exit code indicating that the script was terminated by Control-C."""
    PROCESS_KILLED_BY_SIGKILL = 137
    """An exit code indicating that the process was killed by SIGKILL (9)."""
    SEGMENTATION_FAULT = 139
    """An exit code indicating a segmentation fault (core dumped)."""
    PROCESS_TERMINATED_BY_SIGTERM = 143
    """An exit code indicating that the process was terminated by SIGTERM (15)."""
    EXIT_STATUS_OUT_OF_RANGE = 255
    """An exit code indicating that the exit status is out of range."""


class VersionParts(IntEnum):  # pragma: no cover
    """Enumeration for version parts."""

    MAJOR = 0
    MINOR = 1
    PATCH = 2


class _Version(NamedTuple):  # pragma: no cover
    major: int
    minor: int
    patch: int

    def new_version(self, bump_type: str) -> _Version:
        """Return a new version string based on the bump type."""
        bump_part: VersionParts = VersionParts[bump_type.upper()]
        match bump_part:
            case VersionParts.MAJOR:
                return _Version(major=self.major + 1, minor=0, patch=0)
            case VersionParts.MINOR:
                return _Version(major=self.major, minor=self.minor + 1, patch=0)
            case VersionParts.PATCH:
                return _Version(major=self.major, minor=self.minor, patch=self.patch + 1)
            case _:
                raise ValueError(f"Invalid bump type: {bump_type}")

    @classmethod
    def from_string(cls, version_str: str) -> _Version:
        """Create a Version instance from a version string."""
        parts: list[str] = version_str.split(".")
        default: list[int] = list(_NULL_TUP)
        for i in range(min(len(parts), _ALL_PARTS)):
            default[i] = int(parts[i])
        return cls(*default)

    @classmethod
    def default(cls) -> _Version:
        """Return the default version (0.0.0)."""
        return cls(major=0, minor=0, patch=0)

    def __repr__(self) -> str:
        """Return a string representation of the Version instance."""
        return f"{self.major}.{self.minor}.{self.patch}"

    def __str__(self) -> str:
        """Return a string representation of the Version instance."""
        return self.__repr__()


def _get_version(dist: str) -> str:
    """Get version of the given distribution or the current package.

    Parameters:
        dist: A distribution name.

    Returns:
        A version number.
    """
    try:
        return version(dist)
    except PackageNotFoundError:
        return "0.0.0"


def _get_description(dist: str) -> str:
    """Get description of the given distribution or the current package.

    Parameters:
        dist: A distribution name.

    Returns:
        A description string.
    """
    try:
        return distribution(dist).metadata.get("summary", "No description available.")
    except PackageNotFoundError:
        return "No description available."


class _Package(NamedTuple):
    """Model to represent package information."""

    name: str
    """Package name."""
    version: str = "0.0.0"
    """Package version."""
    version_tuple: _Version = _Version.default()
    """Package version as a tuple."""
    description: str = "No description available."
    """Package description."""

    def __str__(self) -> str:
        """String representation of the package information."""
        return f"{self.name} v{self.version}: {self.description}"

    @classmethod
    def new(cls, name: str) -> _Package:
        """Create a new Package instance with the given name."""
        version: str = _get_version(name)
        version_tuple: _Version = _Version.from_string(version)
        description: str = _get_description(name)
        return cls(name=name, version=version, version_tuple=version_tuple, description=description)

    @classmethod
    def package_info(cls, name: str) -> _Package:
        """Get a string representation of the package information."""
        from importlib.util import find_spec  # noqa: PLC0415

        if find_spec(f"{PROJECT_NAME}._internal._version"):
            from ._version import __version__ as _ver, __version_tuple__ as _ver_tuple  # noqa: PLC0415
        else:
            _ver = _NULL_VER
            _ver_tuple = _NULL_TUP
        v: str = _ver if _ver != _NULL_VER else _get_version(name)
        version_tuple: _Version = _Version(*_ver_tuple) if _ver_tuple != _NULL_TUP else _Version.from_string(v)
        description: str = _get_description(name)
        return cls(name=name, version=v, version_tuple=version_tuple, description=description)


PACKAGE: Final[_Package] = _Package.package_info(name=PACKAGE_NAME)


class _ProjectMetadata(NamedTuple):
    """Dataclass to store the current project metadata."""

    version: str = PACKAGE.version
    version_tuple: _Version = PACKAGE.version_tuple
    description: str = PACKAGE.description
    full_version: str = f"{PACKAGE.name} v{PACKAGE.version}"
    name: Literal["bear-config"] = PACKAGE_NAME
    name_upper: Literal["BEAR_CONFIG"] = PROJECT_UPPER
    project_name: Literal["bear_config"] = PROJECT_NAME
    env_variable: Literal["BEAR_CONFIG_ENV"] = ENV_VARIABLE

    def __str__(self) -> str:
        """String representation of the project metadata."""
        return f"{self.full_version}: {self.description}"


METADATA = _ProjectMetadata()


__all__ = ["METADATA"]
