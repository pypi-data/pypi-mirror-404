"""Parser definitions for pattern commands.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

from ..commands import patterns as patterns_commands


def register_parsers(subparsers):
    """Register pattern command parsers.

    Args:
        subparsers: ArgumentParser subparsers object
    """
    # Create patterns subcommand group
    patterns_parser = subparsers.add_parser("patterns", help="Pattern management commands")
    patterns_subparsers = patterns_parser.add_subparsers(dest="patterns_command")

    # patterns list
    parser_list = patterns_subparsers.add_parser("list", help="List patterns in library")
    parser_list.add_argument("library", help="Path to pattern library")
    parser_list.add_argument(
        "--format", choices=["json", "sqlite"], default="json", help="Library format"
    )
    parser_list.set_defaults(func=patterns_commands.cmd_patterns_list)

    # patterns export
    parser_export = patterns_subparsers.add_parser("export", help="Export patterns")
    parser_export.add_argument("input", help="Input file path")
    parser_export.add_argument("output", help="Output file path")
    parser_export.add_argument(
        "--input-format", choices=["json", "sqlite"], default="json", help="Input format"
    )
    parser_export.add_argument(
        "--output-format", choices=["json", "sqlite"], default="json", help="Output format"
    )
    parser_export.set_defaults(func=patterns_commands.cmd_patterns_export)

    # patterns resolve
    parser_resolve = patterns_subparsers.add_parser("resolve", help="Resolve a bug pattern")
    parser_resolve.add_argument("bug_id", nargs="?", help="Bug ID to resolve")
    parser_resolve.add_argument("--root-cause", help="Root cause description")
    parser_resolve.add_argument("--fix", help="Fix description")
    parser_resolve.add_argument("--fix-code", help="Code snippet of the fix")
    parser_resolve.add_argument("--time", type=int, help="Resolution time in minutes")
    parser_resolve.add_argument(
        "--patterns-dir", default="./patterns", help="Patterns directory path"
    )
    parser_resolve.add_argument("--resolved-by", help="Who resolved it")
    parser_resolve.add_argument(
        "--no-regenerate", action="store_true", help="Don't regenerate summary"
    )
    parser_resolve.set_defaults(func=patterns_commands.cmd_patterns_resolve)
