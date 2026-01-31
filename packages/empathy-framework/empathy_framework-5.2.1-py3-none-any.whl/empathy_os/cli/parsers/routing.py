"""Argument parser for adaptive routing commands.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""


def register_parsers(subparsers):
    """Register routing command parsers.

    Args:
        subparsers: Subparser object from main argument parser

    Returns:
        None: Adds routing subparser with stats, check, models subcommands
    """
    from ..commands.routing import (
        cmd_routing_check,
        cmd_routing_models,
        cmd_routing_stats,
    )

    # Main routing command
    routing_parser = subparsers.add_parser(
        "routing",
        help="Adaptive model routing statistics and recommendations",
        description="Analyze model routing performance based on historical telemetry",
    )

    # Routing subcommands
    routing_subparsers = routing_parser.add_subparsers(
        dest="routing_command", required=True
    )

    # routing stats command
    stats_parser = routing_subparsers.add_parser(
        "stats",
        help="Show routing statistics for a workflow",
        description="Display model performance metrics and recommendations",
    )

    stats_parser.add_argument("workflow", help="Workflow name (e.g., 'code-review')")

    stats_parser.add_argument(
        "--stage",
        help="Stage name (optional, shows all stages if not specified)",
    )

    stats_parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to analyze (default: 7)",
    )

    stats_parser.set_defaults(func=cmd_routing_stats)

    # routing check command
    check_parser = routing_subparsers.add_parser(
        "check",
        help="Check for tier upgrade recommendations",
        description="Analyze failure rates and recommend tier upgrades",
    )

    check_parser.add_argument(
        "--workflow",
        help="Workflow name (required unless --all is used)",
    )

    check_parser.add_argument(
        "--stage",
        help="Stage name (optional)",
    )

    check_parser.add_argument(
        "--all",
        action="store_true",
        help="Check all workflows",
    )

    check_parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to analyze (default: 7)",
    )

    check_parser.set_defaults(func=cmd_routing_check)

    # routing models command
    models_parser = routing_subparsers.add_parser(
        "models",
        help="Compare model performance",
        description="Show performance metrics for all models from a provider",
    )

    models_parser.add_argument(
        "--provider",
        default="anthropic",
        help="Provider name (default: anthropic)",
    )

    models_parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to analyze (default: 7)",
    )

    models_parser.set_defaults(func=cmd_routing_models)
