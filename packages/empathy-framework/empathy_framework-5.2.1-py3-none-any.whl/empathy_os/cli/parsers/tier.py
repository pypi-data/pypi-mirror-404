"""Parser definitions for tier commands.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

from ..commands import tier as tier_commands


def register_parsers(subparsers):
    """Register tier command parsers.

    Args:
        subparsers: ArgumentParser subparsers object
    """
    # Create tier subcommand group
    tier_parser = subparsers.add_parser("tier", help="Tier management commands")
    tier_subparsers = tier_parser.add_subparsers(dest="tier_command")

    # tier recommend
    parser_recommend = tier_subparsers.add_parser(
        "recommend", help="Get tier recommendation"
    )
    parser_recommend.add_argument("description", help="Bug or task description")
    parser_recommend.add_argument("--files", help="Comma-separated list of files")
    parser_recommend.add_argument(
        "--complexity", choices=["low", "medium", "high"], help="Complexity hint"
    )
    parser_recommend.set_defaults(func=tier_commands.cmd_tier_recommend)

    # tier stats
    parser_stats = tier_subparsers.add_parser("stats", help="Show tier statistics")
    parser_stats.set_defaults(func=tier_commands.cmd_tier_stats)
