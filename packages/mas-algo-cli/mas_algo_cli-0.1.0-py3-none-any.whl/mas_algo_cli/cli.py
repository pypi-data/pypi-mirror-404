#!/usr/bin/env python
"""mas-algo-cli main entry point."""

import argparse
import sys

from . import __version__
from .commands import new, run, pack, stubs, debug


def main():
    parser = argparse.ArgumentParser(
        prog="algo",
        description="CLI tool for managing MAS hosting platform algorithm services",
    )
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # new command
    new_parser = subparsers.add_parser("new", help="Create a new algorithm service project")
    new_parser.add_argument("name", help="Service name (e.g., ocr_service)")
    new_parser.add_argument("-d", "--dir", default=".", help="Parent directory (default: current)")
    new_parser.add_argument(
        "-t", "--template",
        choices=["basic", "predict", "cv"],
        help="Project template (basic, predict, cv). Prompts interactively if not specified."
    )

    # run command
    run_parser = subparsers.add_parser("run", help="Run service locally for testing")
    run_parser.add_argument("path", nargs="?", default=".", help="Service directory (default: current)")
    run_parser.add_argument("-p", "--port", type=int, default=8080, help="Port to listen on (default: 8080)")
    run_parser.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    run_parser.add_argument("--debug", action="store_true", help="Enable debugpy and wait for VS Code to attach")
    run_parser.add_argument("--debug-port", type=int, default=5678, help="Debug port (default: 5678)")

    # pack command
    pack_parser = subparsers.add_parser("pack", help="Package service for deployment")
    pack_parser.add_argument("path", nargs="?", default=".", help="Service directory (default: current)")
    pack_parser.add_argument("-o", "--output", help="Output file path (default: {name}.tar.gz)")

    # stubs command
    subparsers.add_parser("stubs", help="Install stub packages for IDE/linting support")

    # debug command
    debug_parser = subparsers.add_parser("debug", help="Generate VS Code launch.json for debugging")
    debug_parser.add_argument("path", nargs="?", default=".", help="Project directory (default: current)")

    args = parser.parse_args()

    if args.command == "new":
        return new.execute(args.name, args.dir, args.template)
    elif args.command == "run":
        return run.execute(args.path, args.host, args.port, args.debug, args.debug_port)
    elif args.command == "pack":
        return pack.execute(args.path, args.output)
    elif args.command == "stubs":
        return stubs.execute()
    elif args.command == "debug":
        return debug.execute(args.path)

    return 1


if __name__ == "__main__":
    sys.exit(main())
