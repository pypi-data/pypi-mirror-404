"""A specialized TOML file handler with caching and utilities."""

from __future__ import annotations

import fcntl
from pathlib import Path
import tomllib
from typing import IO, Any, Self

import tomlkit

from .common import EXCLUSIVE_LOCK, SHARED_LOCK, UNLOCK, UNSET, TomlData
from .dir_manager import touch


def flock(handle: IO[Any], operation: int) -> None:
    """Apply a file lock operation on the given file handle."""
    fcntl.flock(handle.fileno(), operation)


def ex_lock(handle: IO[Any]) -> None:
    """Apply an exclusive lock on the given file handle."""
    flock(handle=handle, operation=EXCLUSIVE_LOCK)


def sh_lock(handle: IO[Any]) -> None:
    """Apply a shared lock on the given file handle."""
    flock(handle=handle, operation=SHARED_LOCK)


def unlock(handle: IO[Any]) -> None:
    """Unlock the given file handle."""
    flock(handle=handle, operation=UNLOCK)


class TomlFileHandler:
    """TOML file handler with caching and utilities."""

    def __init__(self, file: Path | str | None = None, touch: bool = False) -> None:
        """Initialize the handler with a file path.

        Args:
            path: Path to the TOML file, or None for setting the path later
            touch: Whether to create the file if it doesn't exist
        """
        self.file: Path = Path(file) if file is not None else UNSET
        self.touch: bool = touch if file is not None else False
        self._handle: IO[Any] | None = None

    def handle(self, open_file: bool = True) -> IO[Any] | None:
        """Get the file handle, opening it if needed."""
        if self.file is UNSET:
            raise NotImplementedError("In-memory file handling not implemented.")
        if not open_file:
            return self._handle
        if self._handle is None or self._handle.closed:
            self._handle = self._open()
        return self._handle

    def _open(self, **kwargs: Any) -> IO[Any]:
        """Default opener. Subclasses can override if needed.

        NOTE: If self.touch is true and the file already exists,
        it will modify the file's access and modification times
        which can be seen as a side effect.
        """
        file: Path = self.file
        if file is UNSET:
            raise ValueError("File path is not set.")
        touch(file, mkdir=True, create_file=self.touch)
        return open(file=file, mode="r+", encoding="utf-8", **kwargs)

    def set_path(self, path: Path | str | None, touch: bool = False) -> Self:
        """Set a new file path for the handler.

        Args:
            path: New path to the TOML file
        Returns:
            Self: The updated TomlFileHandler instance
        """
        self.file = Path(path) if path is not None else UNSET
        self.touch = touch
        self.close()
        self._handle = None
        return self

    def read(self, **kwargs) -> TomlData:
        """Read the entire file (or up to n chars) as text with a shared lock."""
        handle: IO[Any] | None = self.handle()
        if handle is None:
            raise ValueError("File handle is not available.")
        try:
            sh_lock(handle)
            handle.seek(0)
            data: str = handle.read(kwargs.pop("n", -1))
            return self.to_dict(data) if data else {}
        finally:
            unlock(handle)

    def write(self, data: TomlData, **kwargs) -> None:
        """Replace file contents with text using an exclusive lock.

        Args:
            data: Data to write to the TOML file
            **kwargs: Additional keyword arguments like 'sort_keys' (bool)

        Raises:
            ValueError: If file cannot be written
        """
        handle: IO[Any] | None = self.handle()
        if handle is None:
            raise ValueError("File handle is not available.")
        try:
            ex_lock(handle)
            handle.seek(0)
            handle.truncate(0)
            handle.write(self.to_string(data, sort_keys=kwargs.get("sort_keys", False)))
            handle.flush()
        finally:
            unlock(handle)

    def to_dict(self, s: str) -> dict[str, Any]:
        """Parse a TOML string into a dictionary.

        Args:
            s: TOML string to parse

        Returns:
            Parsed TOML data as dictionary

        Raises:
            tomllib.TOMLDecodeError: If file contains invalid TOML
            ValueError: If file cannot be read
        """
        try:
            return tomllib.loads(s)
        except tomllib.TOMLDecodeError as e:
            raise ValueError(f"Invalid TOML in {self.file}: {e}") from e
        except Exception as e:
            raise ValueError(f"Error reading TOML file {self.file}: {e}") from e

    def clear(self) -> None:
        """Clear the file contents using an exclusive lock."""
        handle: IO[Any] | None = self.handle()
        if handle is None:
            raise ValueError("File handle is not available.")
        try:
            ex_lock(handle)
            handle.seek(0)
            handle.truncate(0)
        finally:
            unlock(handle)

    def to_string(self, data: TomlData, sort_keys: bool = False) -> str:
        """Convert data to TOML string.

        Args:
            data: Data to serialize

        Returns:
            TOML formatted string

        Raises:
            ValueError: If data cannot be serialized
        """
        try:
            return tomlkit.dumps(data, sort_keys=sort_keys)
        except Exception as e:
            raise ValueError(f"Cannot serialize data to TOML: {e}") from e

    def get_section(
        self,
        data: TomlData | None,
        section: str,
        default: TomlData | None = None,
    ) -> dict[str, Any] | None:
        """Get a specific section from TOML data.

        Args:
            data: TOML data to search
            section: Section name (supports dot notation like 'tool.poetry')
            default: Default value if section not found

        Returns:
            Section data or default
        """
        current: TomlData = data or self.read()
        for key in section.split("."):
            if not isinstance(current, dict) or key not in current:
                return default
            current = current[key]
        return current if isinstance(current, dict) else default

    def close(self) -> None:
        """Close the file handle if open."""
        if self.closed:
            return
        h: IO[Any] | None = self.handle(open_file=False)
        if h is not None and not h.closed:
            h.close()
        self._handle = None

    @property
    def closed(self) -> bool:
        """Check if the file handle is closed."""
        h: IO[Any] | None = self.handle(open_file=False)
        return not h or h.closed

    def __enter__(self) -> Self:
        """Enter context manager."""
        self.read()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        """Exit context manager and close file handle."""
        self.close()


__all__ = ["TomlData", "TomlFileHandler"]
