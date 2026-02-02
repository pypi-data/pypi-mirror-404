from argparse import ArgumentParser, Namespace, _SubParsersAction
from pathlib import Path
from typing import NamedTuple

from .info import _VALIDS, METADATA, ExitCode, _BumpType, _Version

DEFAULT_PATH = Path("bear_build.toml")


class _ReturnedArgs(NamedTuple):
    cmd: str
    version_name: bool
    bump_type: _BumpType
    no_color: bool
    project_name: str
    write_path: Path


def get_args(args: list[str]) -> _ReturnedArgs:
    """Parse command-line arguments."""
    parser = ArgumentParser(description="Pack Int CLI")
    subparsers: _SubParsersAction[ArgumentParser] = parser.add_subparsers(dest="command", required=True)
    version: ArgumentParser = subparsers.add_parser("version", help="Get the version of the package.")
    version.add_argument("--name", "-n", action="store_true", help="Print only the version name.")
    bump: ArgumentParser = subparsers.add_parser("bump", help="Bump the version of the package.")
    bump.add_argument("bump_type", type=str, choices=_VALIDS, help="Type of version bump (major, minor, patch).")
    debug: ArgumentParser = subparsers.add_parser("debug", help="Print debug information.")
    debug.add_argument("--no-color", "-nc", action="store_true", help="Disable colored output.")
    init: ArgumentParser = subparsers.add_parser("init", help="Initialize a build_cub configuration file.")
    init.add_argument("project_name", type=str, help="Name of the project/package.")
    init.add_argument(
        "--write-path",
        "-wp",
        type=Path,
        default=DEFAULT_PATH,
        help=f"Path to write the configuration file (default: {DEFAULT_PATH}).",
    )
    parsed: Namespace = parser.parse_args(args)
    return _ReturnedArgs(
        cmd=parsed.command,
        version_name=getattr(parsed, "name", False),
        bump_type=getattr(parsed, "bump_type", "patch"),
        no_color=getattr(parsed, "no_color", False),
        project_name=getattr(parsed, "project_name", ""),
        write_path=getattr(parsed, "write_path", Path("bear_build.toml")),
    )


def get_version(version_name: bool) -> ExitCode:
    """CLI command to get the version of the package."""
    if version_name:
        print(METADATA.full_version)
    else:
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
    v: _Version = METADATA.version_tuple
    if b not in _VALIDS:
        print(f"Invalid argument '{b}'. Use one of: {', '.join(_VALIDS)}.")
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


def debug_info(no_color: bool = False) -> ExitCode:
    """CLI command to print debug information."""
    from .debug import _print_debug_info

    _print_debug_info(no_color=no_color)
    return ExitCode.SUCCESS


def init_config(project_name: str, write_path: Path) -> ExitCode:
    """CLI command to initialize a build_cub configuration file."""
    from build_cub.utils._raw_config import write_toml_file

    write_toml_file(name=project_name, write_path=write_path)
    print(f"Configuration file written to {write_path}")
    return ExitCode.SUCCESS
