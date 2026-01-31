"""Utility commands for Empathy Framework CLI.

General-purpose utility commands (sync, cheatsheet, dashboard, etc.).

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

import subprocess
import sys

import typer
from rich.panel import Panel

from empathy_os.cli.core import console

# Create the utilities Typer app
utilities_app = typer.Typer(
    help="Utility tools - project init, cheatsheet, dashboard, costs",
    no_args_is_help=True,
)


@utilities_app.command("sync-claude")
def sync_claude(
    source: str = typer.Option("patterns", "--source", "-s", help="Source to sync"),
) -> None:
    """Sync patterns to Claude Code memory."""
    subprocess.run(["empathy-sync-claude", "--source", source], check=False)


@utilities_app.command("cheatsheet")
def cheatsheet() -> None:
    """Show quick reference for all commands."""
    console.print(
        Panel.fit(
            """[bold]Getting Started[/bold]
  empathy morning           Start-of-day briefing
  empathy health            Quick health check
  empathy ship              Pre-commit validation
  empathy run               Interactive REPL

[bold]Memory System[/bold]
  empathy memory status     Check Redis & patterns
  empathy memory start      Start Redis server
  empathy memory patterns   List stored patterns

[bold]Cross-Session Service[/bold]
  empathy service start     Start coordination service
  empathy service status    Show service & sessions
  empathy service sessions  List active agents

[bold]Provider Config[/bold]
  empathy provider          Show current config
  empathy provider --set hybrid    Use best-of-breed
  empathy provider registry        List all models

[bold]Code Inspection[/bold]
  empathy scan .            Scan for issues
  empathy inspect .         Deep analysis (SARIF)
  empathy fix-all           Auto-fix everything

[bold]Profiling[/bold]
  empathy profile memory-scan   Scan for memory leaks
  empathy profile hot-files     Show riskiest files
  empathy profile memory-test   Profile memory module

[bold]Pattern Learning[/bold]
  empathy learn --analyze 20    Learn from commits
  empathy utilities sync-claude Sync to Claude Code

[bold]Workflows[/bold]
  empathy workflow list     Show available workflows
  empathy workflow run <name>   Execute a workflow
  empathy workflow create <name> -p <patterns>  Create workflow (12x faster)
  empathy workflow list-patterns                List available patterns

[bold]Workflows[/bold]
  empathy workflow list       Show available workflows
  empathy workflow run <name> Execute a workflow
  empathy workflow create <name> -d <domain>  Create workflow (12x faster)
  empathy workflow list-patterns              List available patterns

[bold]Usage Telemetry[/bold]
  empathy telemetry show    View recent LLM calls & costs
  empathy telemetry savings Calculate cost savings (tier routing)
  empathy telemetry export  Export usage data (JSON/CSV)""",
            title="[bold blue]Empathy Framework Cheatsheet[/bold blue]",
        )
    )


@utilities_app.command("dashboard")
def dashboard() -> None:
    """Launch visual dashboard."""
    subprocess.run([sys.executable, "-m", "empathy_os.cli", "dashboard"], check=False)


@utilities_app.command("costs")
def costs() -> None:
    """View API cost tracking."""
    subprocess.run([sys.executable, "-m", "empathy_os.cli", "costs"], check=False)


@utilities_app.command("init")
def init() -> None:
    """Create a new configuration file."""
    subprocess.run([sys.executable, "-m", "empathy_os.cli", "init"], check=False)


@utilities_app.command("status")
def status() -> None:
    """What needs attention now."""
    subprocess.run([sys.executable, "-m", "empathy_os.cli", "status"], check=False)
