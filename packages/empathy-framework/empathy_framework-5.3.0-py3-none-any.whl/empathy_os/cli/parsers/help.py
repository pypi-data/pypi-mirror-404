"""Parser definitions for help commands.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

from ..commands import help as help_commands


def register_parsers(subparsers):
    """Register help command parsers.

    Args:
        subparsers: ArgumentParser subparsers object
    """
    # version command
    parser_version = subparsers.add_parser("version", help="Display version information")
    parser_version.set_defaults(func=help_commands.cmd_version)

    # cheatsheet command
    parser_cheatsheet = subparsers.add_parser("cheatsheet", help="Quick reference guide")
    parser_cheatsheet.add_argument("--category", help="Specific category to show")
    parser_cheatsheet.add_argument(
        "--compact", action="store_true", help="Show commands only"
    )
    parser_cheatsheet.set_defaults(func=help_commands.cmd_cheatsheet)

    # onboard command
    parser_onboard = subparsers.add_parser("onboard", help="Interactive tutorial")
    parser_onboard.add_argument("--step", type=int, help="Jump to specific step")
    parser_onboard.add_argument("--reset", action="store_true", help="Reset progress")
    parser_onboard.set_defaults(func=help_commands.cmd_onboard)

    # explain command
    parser_explain = subparsers.add_parser("explain", help="Explain a command in detail")
    parser_explain.add_argument("command", help="Command to explain")
    parser_explain.set_defaults(func=help_commands.cmd_explain)

    # achievements command
    parser_achievements = subparsers.add_parser("achievements", help="Show user progress")
    parser_achievements.set_defaults(func=help_commands.cmd_achievements)
