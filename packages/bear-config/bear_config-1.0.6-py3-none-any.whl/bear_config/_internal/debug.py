from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any, Literal, NamedTuple

if TYPE_CHECKING:
    from collections.abc import Callable

    from .info import _Package


class _Variable(NamedTuple):
    """Dataclass describing an environment variable."""

    name: str
    """Variable name."""
    value: str
    """Variable value."""


class _Environment(NamedTuple):
    """Dataclass to store environment information."""

    interpreter_info: _Variable
    """Interpreter name and version."""
    interpreter_path: str
    """Path to Python executable."""
    platform: str
    """Operating System."""
    packages: list[Any]
    """Installed packages."""
    variables: list[_Variable]
    """Environment variables."""


def _interpreter_name_version() -> _Variable:
    if hasattr(sys, "implementation"):
        impl: sys._version_info = sys.implementation.version
        version: str = f"{impl.major}.{impl.minor}.{impl.micro}"
        kind: Literal["alpha", "beta", "candidate", "final"] = impl.releaselevel
        if kind != "final":
            version += kind[0] + str(impl.serial)
        return _Variable(sys.implementation.name, version)
    return _Variable("", "0.0.0")


def _get_debug_info() -> _Environment:
    """Get debug/environment information.

    Returns:
        Environment information.
    """
    from os import environ, getenv
    import platform

    from .info import METADATA

    environ[f"{METADATA.name_upper}_DEBUG"] = "1"
    variables: list[str] = [
        "PYTHONPATH",
        *[var for var in environ if var.startswith(METADATA.name_upper)],
    ]
    return _Environment(
        interpreter_info=_interpreter_name_version(),
        interpreter_path=sys.executable,
        platform=platform.platform(),
        variables=[_Variable(var, val) for var in variables if (val := getenv(var))],
        packages=_get_installed_packages(),
    )


def _get_installed_packages() -> list[_Package]:
    """Get all installed packages in current environment"""
    from importlib.metadata import distributions

    from .info import _Package

    packages: list[_Package] = []
    for dist in distributions():
        packages.append(_Package.new(name=dist.metadata["Name"]))
    return packages


class Printer:
    def __init__(self, no_color: bool = False) -> None:
        self.no_color: bool = no_color
        self.rich: bool = False
        self.p: Callable[..., None] = self._get_printer()

    def _get_printer(self) -> Callable[..., None]:
        from importlib.util import find_spec

        if find_spec("rich") is not None:
            from rich.console import Console

            self.rich = True
            return Console(highlight=True, no_color=self.no_color).print

        return print

    def print(self, *args: object, **kwargs: object) -> None:
        if not self.rich:
            kwargs.pop("style", None)
        self.p(*args, **kwargs)


def _print_debug_info(no_color: bool = False) -> None:
    """Print debug/environment information with minimal clean formatting."""
    info: _Environment = _get_debug_info()
    sections: list[tuple[str, list[tuple[str, str]]]] = [
        (
            "SYSTEM",
            [
                ("Platform", info.platform),
                ("Python", f"{info.interpreter_info.name} {info.interpreter_info.value}"),
                ("Location", info.interpreter_path),
            ],
        ),
        ("ENVIRONMENT", [(var.name, var.value) for var in info.variables]),
        ("PACKAGES", [(pkg.name, f"v{pkg.version}") for pkg in info.packages]),
    ]

    output: Printer = Printer(no_color=no_color)

    for i, (section_name, items) in enumerate(sections):
        if items:
            output.print(f"{section_name}", style="bold red")
            for key, value in items:
                output.print(key, style="bold blue", end=": ")
                output.print(value, style="bold green")
            if i < len(sections) - 1:
                output.print()


if __name__ == "__main__":
    _print_debug_info()

# ruff: noqa: PLC0415
