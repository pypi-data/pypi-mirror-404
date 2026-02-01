"""Parser definitions for setup commands.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

from ..commands import setup


def register_parsers(subparsers):
    """Register setup command parsers.

    Args:
        subparsers: ArgumentParser subparsers object from main parser
    """
    # Init command
    parser_init = subparsers.add_parser(
        "init",
        help="Initialize a new Empathy Framework project",
    )
    parser_init.add_argument(
        "--format",
        choices=["yaml", "json"],
        default="yaml",
        help="Configuration format (default: yaml)",
    )
    parser_init.add_argument(
        "--output",
        help="Output file path (default: empathy.config.{format})",
    )
    parser_init.set_defaults(func=setup.cmd_init)

    # Validate command
    parser_validate = subparsers.add_parser(
        "validate",
        help="Validate a configuration file",
    )
    parser_validate.add_argument(
        "config",
        help="Path to configuration file to validate",
    )
    parser_validate.set_defaults(func=setup.cmd_validate)
