"""CLI parser registration.

This module coordinates parser registration for all CLI commands.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

from . import (
    batch,
    cache,
    help,
    info,
    inspect,
    metrics,
    orchestrate,
    patterns,
    provider,
    routing,
    setup,
    status,
    sync,
    tier,
    workflow,
)


def register_all_parsers(subparsers):
    """Register all command parsers.

    This function is called from the main CLI entry point to set up
    all subcommands and their argument parsers.

    Args:
        subparsers: ArgumentParser subparsers object from main parser

    Note:
        All 30 commands have been extracted from the monolithic cli.py
        and organized into focused modules.
    """
    # Core commands
    help.register_parsers(subparsers)
    tier.register_parsers(subparsers)
    info.register_parsers(subparsers)

    # Pattern and state management
    patterns.register_parsers(subparsers)
    status.register_parsers(subparsers)

    # Workflow and execution
    workflow.register_parsers(subparsers)
    inspect.register_parsers(subparsers)

    # Provider configuration
    provider.register_parsers(subparsers)

    # Orchestration and sync
    orchestrate.register_parsers(subparsers)
    sync.register_parsers(subparsers)

    # Metrics and state
    metrics.register_parsers(subparsers)
    cache.register_parsers(subparsers)  # Cache monitoring
    batch.register_parsers(subparsers)  # Batch processing (50% cost savings)
    routing.register_parsers(subparsers)  # Adaptive routing statistics

    # Setup and initialization
    setup.register_parsers(subparsers)
