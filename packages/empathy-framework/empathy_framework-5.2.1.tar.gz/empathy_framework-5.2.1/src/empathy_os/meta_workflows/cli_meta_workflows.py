"""CLI Commands for Meta-Workflow System (Backward Compatible Entry Point).

This module maintains backward compatibility by re-exporting all CLI commands
from the cli_commands package.

For new code, import from the package directly:
    from empathy_os.meta_workflows.cli_commands import meta_workflow_app

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

# Re-export all commands and the Typer app from the package
from .cli_commands import (
    cleanup_executions,
    create_agent,
    create_team,
    detect_intent,
    generate_plan_cmd,
    inspect_template,
    list_runs,
    list_templates,
    meta_workflow_app,
    natural_language_run,
    run_workflow,
    search_memory,
    show_analytics,
    show_execution,
    show_migration_guide,
    show_session_stats,
    suggest_defaults_cmd,
)

__all__ = [
    # Typer app
    "meta_workflow_app",
    # Template commands
    "list_templates",
    "inspect_template",
    "generate_plan_cmd",
    # Workflow commands
    "run_workflow",
    "natural_language_run",
    "detect_intent",
    # Analytics commands
    "show_analytics",
    "list_runs",
    "show_execution",
    "cleanup_executions",
    # Memory commands
    "search_memory",
    "show_session_stats",
    # Config commands
    "suggest_defaults_cmd",
    "show_migration_guide",
    # Agent commands
    "create_agent",
    "create_team",
]
