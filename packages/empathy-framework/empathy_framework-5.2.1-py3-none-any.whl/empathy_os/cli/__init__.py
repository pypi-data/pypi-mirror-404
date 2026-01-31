"""Empathy Framework CLI - Refactored modular structure.

Entry point for the empathy command-line interface.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

import argparse
import sys

from empathy_os.discovery import show_tip_if_available
from empathy_os.logging_config import get_logger
from empathy_os.platform_utils import setup_asyncio_policy

logger = get_logger(__name__)


def get_version() -> str:
    """Get package version.

    Returns:
        Version string or "dev" if not installed
    """
    try:
        from importlib.metadata import version

        return version("empathy-framework")
    except Exception:  # noqa: BLE001
        return "dev"


def main() -> int:
    """Main CLI entry point.

    This is the refactored CLI entry point that uses modular command
    and parser organization instead of a monolithic 3,957-line file.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Windows async compatibility
    setup_asyncio_policy()

    # Create main parser
    parser = argparse.ArgumentParser(
        prog="empathy", description="Empathy Framework - Context-aware development automation"
    )

    # Add global flags
    parser.add_argument("--version", action="version", version=f"empathy {get_version()}")

    # Create subparsers
    subparsers = parser.add_subparsers(
        dest="command", title="commands", description="Available commands"
    )

    # Register all command parsers (modular!)
    from .parsers import register_all_parsers

    register_all_parsers(subparsers)

    # TODO: Import and register remaining commands from cli.py
    # This is a partial refactoring - additional commands still in cli.py
    # For now, if command not found in new structure, fall back to old cli.py
    #
    # NOTE: Temporarily disabled to avoid conflicts with extracted commands.
    # Commands that have been extracted:
    #   - help, tier, info, patterns, status (Phase 1)
    #   - workflow, inspect (run, inspect, export, import) (Phase 2)
    # Once all commands are extracted, the old cli.py will be removed entirely.
    #
    # try:
    #     from empathy_os import cli as old_cli
    #     _register_legacy_commands(subparsers, old_cli)
    # except ImportError:
    #     pass  # Old cli.py not available or already moved

    # Parse arguments
    args = parser.parse_args()

    # Execute command
    if hasattr(args, "func"):
        try:
            result = args.func(args)

            # Show discovery tips (except for dashboard/run)
            if args.command and args.command not in ("dashboard", "run"):
                try:
                    show_tip_if_available(args.command)
                except Exception:  # noqa: BLE001
                    logger.debug("Discovery tip not available")

            return result if result is not None else 0

        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
            return 130

        except Exception as e:  # noqa: BLE001
            logger.exception(f"Unexpected error in command {args.command}")
            print(f"\n❌ Error: {e}")
            return 1

    # No command specified
    parser.print_help()
    return 0


def _register_legacy_commands(subparsers, old_cli):
    """Temporarily register commands not yet extracted from old cli.py.

    This function provides backward compatibility during the refactoring process.
    As commands are extracted into the new structure, they should be removed
    from this registration.

    Args:
        subparsers: ArgumentParser subparsers object
        old_cli: Reference to old cli module

    Note:
        This is a TEMPORARY function that will be removed once all commands
        are extracted from the monolithic cli.py file.
    """
    # Import command functions that haven't been extracted yet
    try:
        # Patterns commands
        from empathy_os.cli import cmd_patterns_export, cmd_patterns_list, cmd_patterns_resolve

        patterns_parser = subparsers.add_parser("patterns", help="Pattern management")
        patterns_sub = patterns_parser.add_subparsers(dest="patterns_command")

        p_list = patterns_sub.add_parser("list", help="List patterns")
        p_list.set_defaults(func=cmd_patterns_list)

        p_export = patterns_sub.add_parser("export", help="Export patterns")
        p_export.add_argument("output", help="Output file")
        p_export.set_defaults(func=cmd_patterns_export)

        p_resolve = patterns_sub.add_parser("resolve", help="Resolve pattern")
        p_resolve.add_argument("pattern_id", help="Pattern ID")
        p_resolve.set_defaults(func=cmd_patterns_resolve)
    except (ImportError, AttributeError):
        pass  # Commands not available

    # Add other legacy commands as needed...
    # This list will shrink as commands are extracted


# Preserve backward compatibility
if __name__ == "__main__":
    sys.exit(main())
