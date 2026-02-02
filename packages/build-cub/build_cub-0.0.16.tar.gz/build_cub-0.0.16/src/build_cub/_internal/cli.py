from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .info import ExitCode


def main(args: list[str] | None = None) -> ExitCode:
    """Entry point for the CLI application.

    This function is executed when you type `build_cub` or `python -m build_cub`.

    If none is passed into main, it is converted to sys.argv[1:] by the args_inject decorator and
    then passed through to get_args to be parsed.

    Parameters:
        args: Arguments passed from the command line.

    Returns:
        An exit code.
    """
    if args is None:
        args = sys.argv[1:]
    from ._cmds import _ReturnedArgs, bump_version, debug_info, get_args, get_version, init_config
    from .info import ExitCode

    parsed_args: _ReturnedArgs = get_args(args)
    try:
        match parsed_args.cmd:
            case "version":
                return get_version(version_name=parsed_args.version_name)
            case "bump":
                return bump_version(b=parsed_args.bump_type)
            case "debug":
                return debug_info(no_color=parsed_args.no_color)
            case "init":
                return init_config(
                    project_name=parsed_args.project_name,
                    write_path=parsed_args.write_path,
                )
            case _:
                return ExitCode.FAILURE
    except Exception:
        return ExitCode.FAILURE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
