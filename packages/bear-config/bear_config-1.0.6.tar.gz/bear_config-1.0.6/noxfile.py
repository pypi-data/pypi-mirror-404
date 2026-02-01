"""A nox configuration file for automating tasks such as linting, type checking, testing, and documentation building."""

from __future__ import annotations

from enum import IntFlag, auto

import nox

PYTHON_VERSIONS: list[str] = ["3.12", "3.13", "3.14"]

BASIC: list[str] = ["nox", "ruff"]

TESTING: list[str] = [
    "pytest",
    "pytest-cov",
    "pytest-randomly",
    "pytest-xdist",
    "types-markdown",
    "types-pyyaml",
    "build_cub",
]

ALL: list[str] = ["nox", "pydantic", "ty", "tomlkit"]


class Mode(IntFlag):
    NONE = 0
    BASIC = auto()
    TESTING = auto()
    ALL = auto()


def install_deps(session: nox.Session, mode: Mode) -> None:
    """Install dependencies based on the specified mode."""
    if mode & Mode.BASIC:
        session.install(*BASIC)
    if mode & Mode.TESTING:
        session.install(*TESTING)
    if mode & Mode.ALL:
        session.install(*ALL)


@nox.session(venv_backend="uv", tags=["lint"])
def ruff_check(session: nox.Session) -> None:
    """Run ruff linting and formatting checks (CI-friendly, no changes)."""
    install_deps(session, Mode.BASIC)
    session.run(
        "ruff",
        "check",
        ".",
        "--config",
        "config/ruff.toml",
    )
    session.run(
        "ruff",
        "format",
        ".",
        "--check",
        "--config",
        "config/ruff.toml",
    )


@nox.session(venv_backend="uv", tags=["lint", "fix"])
def ruff_fix(session: nox.Session) -> None:
    """Run ruff linting and formatting with auto-fix (development)."""
    install_deps(session, Mode.BASIC)
    session.run(
        "ruff",
        "check",
        ".",
        "--fix",
        "--config",
        "config/ruff.toml",
    )
    session.run(
        "ruff",
        "format",
        ".",
        "--config",
        "config/ruff.toml",
    )


@nox.session(venv_backend="uv", tags=["typecheck"])
def ty(session: nox.Session) -> None:
    """Run static type checks."""
    install_deps(session, Mode.BASIC | Mode.TESTING | Mode.ALL)
    session.run("ty", "check")


@nox.session(python=PYTHON_VERSIONS, venv_backend="uv")
def tests(session: nox.Session) -> None:
    """Run the unit test suite."""
    session.install("-e", ".")
    session.run("pytest")
