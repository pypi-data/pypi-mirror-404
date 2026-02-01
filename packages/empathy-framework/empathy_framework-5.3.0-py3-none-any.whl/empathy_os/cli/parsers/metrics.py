"""Parser definitions for metrics commands.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

from ..commands import metrics


def register_parsers(subparsers):
    """Register metrics command parsers.

    Args:
        subparsers: ArgumentParser subparsers object from main parser
    """
    # Metrics command
    parser_metrics = subparsers.add_parser(
        "metrics",
        help="Display user metrics",
    )
    parser_metrics.add_argument(
        "user",
        help="User ID to retrieve metrics for",
    )
    parser_metrics.add_argument(
        "--db",
        default="./metrics.db",
        help="Path to metrics database (default: ./metrics.db)",
    )
    parser_metrics.set_defaults(func=metrics.cmd_metrics_show)

    # State command
    parser_state = subparsers.add_parser(
        "state",
        help="List saved user states",
    )
    parser_state.add_argument(
        "--state-dir",
        default=".empathy/state",
        help="State directory path (default: .empathy/state)",
    )
    parser_state.set_defaults(func=metrics.cmd_state_list)
