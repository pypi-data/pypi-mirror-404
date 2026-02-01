from argparse import ArgumentParser, Namespace
from typing import TYPE_CHECKING, NamedTuple

from .info import METADATA, ExitCode

if TYPE_CHECKING:
    from .info import _BumpType


class _ReturnedArgs(NamedTuple):
    cmd: str
    version_name: bool
    bump_type: _BumpType
    no_color: bool


def get_args(args: list[str]) -> _ReturnedArgs:
    """Parse command-line arguments."""
    from .info import _VALID_BUMP_TYPES as VALIDS, VERSION_CHECK

    parser = ArgumentParser(description="Pack Int CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for arg in args:
        if arg in VERSION_CHECK:
            args.remove(arg)
            args.insert(0, "version")
    ver: ArgumentParser = subparsers.add_parser("version", help="Get the version of the package.")
    ver.add_argument("--name", "-n", action="store_true", help="Get the package name instead of the version.")
    bump_parser: ArgumentParser = subparsers.add_parser("bump", help="Bump the version of the package.")
    bump_parser.add_argument("bump_type", type=str, choices=VALIDS, help="Type of version bump (major, minor, patch).")
    debug_parser: ArgumentParser = subparsers.add_parser("debug", help="Print debug information.")
    debug_parser.add_argument("--no-color", "-n", action="store_true", help="Disable colored output.")
    parsed: Namespace = parser.parse_args(args)
    return _ReturnedArgs(
        cmd=parsed.command,
        version_name=getattr(parsed, "name", False),
        bump_type=getattr(parsed, "bump_type", "patch"),
        no_color=getattr(parsed, "no_color", False),
    )


def get_version() -> ExitCode:
    """CLI command to get the version of the package."""
    print(METADATA.version)
    return ExitCode.SUCCESS


def bump_version(b: _BumpType) -> ExitCode:
    """Bump the version of the current package.

    Args:
        b: The type of bump ("major", "minor", or "patch").
        v: A Version instance representing the current version.

    Returns:
        An ExitCode indicating success or failure.
    """
    from .info import _VALID_BUMP_TYPES, _Version

    v: _Version = METADATA.version_tuple
    if b not in _VALID_BUMP_TYPES:
        print(f"Invalid argument '{b}'. Use one of: {', '.join(_VALID_BUMP_TYPES)}.")
        return ExitCode.FAILURE

    if v == (0, 0, 0):
        print("Current version is 0.0.0, cannot bump version.")
        return ExitCode.FAILURE
    try:
        new_version: _Version = v.new_version(b)
        print(str(new_version))
        return ExitCode.SUCCESS
    except ValueError:
        print(f"Invalid version tuple: {v}")
        return ExitCode.FAILURE


def debug_info() -> ExitCode:
    """CLI command to print debug information."""
    from .debug import _print_debug_info

    _print_debug_info()
    return ExitCode.SUCCESS


# ruff: noqa: PLC0415
