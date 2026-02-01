"""CLI commands for telemetry tracking.

Provides commands to view, analyze, and manage local usage telemetry data.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

import csv
import json
import sys
from datetime import datetime
from typing import Any

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None  # type: ignore

from empathy_os.config import _validate_file_path

from .usage_tracker import UsageTracker

# _validate_file_path is now imported from empathy_os.config
# This eliminates the duplicate definition that previously existed here (lines 30-69)


def cmd_telemetry_show(args: Any) -> int:
    """Show recent telemetry entries.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success)

    """
    tracker = UsageTracker.get_instance()
    limit = getattr(args, "limit", 20)
    days = getattr(args, "days", None)

    entries = tracker.get_recent_entries(limit=limit, days=days)

    if not entries:
        print("No telemetry data found.")
        print(f"Data location: {tracker.telemetry_dir}")
        return 0

    if RICH_AVAILABLE and Console is not None:
        console = Console()
        table = Table(title="Recent LLM Calls", show_header=True, header_style="bold magenta")
        table.add_column("Time", style="cyan", width=19)
        table.add_column("Workflow", style="green")
        table.add_column("Stage", style="blue")
        table.add_column("Tier", style="yellow")
        table.add_column("Cost", style="red", justify="right")
        table.add_column("Tokens", justify="right")
        table.add_column("Cache", style="green")
        table.add_column("Duration", justify="right")

        total_cost = 0.0
        total_duration = 0

        for entry in entries:
            ts = entry.get("ts", "")
            # Format timestamp
            try:
                dt = datetime.fromisoformat(ts.rstrip("Z"))
                ts_display = dt.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, AttributeError):
                ts_display = ts[:19] if len(ts) >= 19 else ts

            workflow = entry.get("workflow", "unknown")
            stage = entry.get("stage", "-")
            tier = entry.get("tier", "unknown")
            cost = entry.get("cost", 0.0)
            tokens = entry.get("tokens", {})
            cache = entry.get("cache", {})
            duration_ms = entry.get("duration_ms", 0)

            tokens_str = f"{tokens.get('input', 0)}/{tokens.get('output', 0)}"
            cache_str = "HIT" if cache.get("hit") else "MISS"
            if cache.get("hit"):
                cache_type = cache.get("type", "")
                if cache_type:
                    cache_str += f" ({cache_type})"

            table.add_row(
                ts_display,
                workflow[:20],
                stage[:15] if stage else "-",
                tier,
                f"${cost:.4f}",
                tokens_str,
                cache_str,
                f"{duration_ms}ms",
            )

            total_cost += cost
            total_duration += duration_ms

        console.print(table)
        console.print()
        console.print(f"[bold]Total Cost:[/bold] ${total_cost:.4f}")
        console.print(f"[bold]Avg Duration:[/bold] {total_duration // len(entries)}ms")
        console.print(f"\n[dim]Data location: {tracker.telemetry_dir}[/dim]")
    else:
        # Fallback to plain text
        print(
            f"\n{'Time':<19} {'Workflow':<20} {'Stage':<15} {'Tier':<10} {'Cost':>10} {'Cache':<10} {'Duration':>10}"
        )
        print("-" * 120)
        total_cost = 0.0
        for entry in entries:
            ts = entry.get("ts", "")[:19]
            workflow = entry.get("workflow", "unknown")[:20]
            stage = entry.get("stage", "-")[:15]
            tier = entry.get("tier", "unknown")
            cost = entry.get("cost", 0.0)
            cache = entry.get("cache", {})
            duration_ms = entry.get("duration_ms", 0)

            cache_str = "HIT" if cache.get("hit") else "MISS"
            print(
                f"{ts:<19} {workflow:<20} {stage:<15} {tier:<10} ${cost:>9.4f} {cache_str:<10} {duration_ms:>9}ms"
            )
            total_cost += cost

        print("-" * 120)
        print(f"Total Cost: ${total_cost:.4f}")
        print(f"\nData location: {tracker.telemetry_dir}")

    return 0


def cmd_telemetry_savings(args: Any) -> int:
    """Calculate and display cost savings.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success)

    """
    tracker = UsageTracker.get_instance()
    days = getattr(args, "days", 30)

    savings = tracker.calculate_savings(days=days)

    if savings["total_calls"] == 0:
        print("No telemetry data found for the specified period.")
        return 0

    if RICH_AVAILABLE and Console is not None:
        console = Console()

        # Create savings report
        title = Text("Cost Savings Analysis", style="bold magenta")
        content_lines = []

        content_lines.append(f"Period: Last {days} days")
        content_lines.append("")
        content_lines.append("Usage Pattern:")
        for tier, pct in sorted(savings["tier_distribution"].items()):
            content_lines.append(f"  {tier:8}: {pct:5.1f}%")
        content_lines.append("")
        content_lines.append("Cost Comparison:")
        content_lines.append(f"  Baseline (all PREMIUM): ${savings['baseline_cost']:.2f}")
        content_lines.append(f"  Actual (tier routing):  ${savings['actual_cost']:.2f}")
        content_lines.append("")
        savings_color = "green" if savings["savings"] > 0 else "red"
        content_lines.append(
            f"[bold {savings_color}]YOUR SAVINGS: ${savings['savings']:.2f} ({savings['savings_percent']:.1f}%)[/bold {savings_color}]"
        )
        content_lines.append("")
        content_lines.append(f"Cache savings: ${savings['cache_savings']:.2f}")
        content_lines.append(f"Total calls: {savings['total_calls']}")

        panel = Panel(
            "\n".join(content_lines),
            title=title,
            border_style="cyan",
        )
        console.print(panel)
    else:
        # Fallback to plain text
        print("\n" + "=" * 60)
        print("COST SAVINGS ANALYSIS")
        print("=" * 60)
        print(f"Period: Last {days} days\n")
        print("Usage Pattern:")
        for tier, pct in sorted(savings["tier_distribution"].items()):
            print(f"  {tier:8}: {pct:5.1f}%")
        print("\nCost Comparison:")
        print(f"  Baseline (all PREMIUM): ${savings['baseline_cost']:.2f}")
        print(f"  Actual (tier routing):  ${savings['actual_cost']:.2f}")
        print(f"\nYOUR SAVINGS: ${savings['savings']:.2f} ({savings['savings_percent']:.1f}%)")
        print(f"\nCache savings: ${savings['cache_savings']:.2f}")
        print(f"Total calls: {savings['total_calls']}")
        print("=" * 60)

    return 0


def cmd_telemetry_cache_stats(args: Any) -> int:
    """Show prompt caching performance statistics.

    Displays cache hit rates, cost savings, and workflow-level stats.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success)
    """
    tracker = UsageTracker.get_instance()
    days = getattr(args, "days", 7)

    stats = tracker.get_cache_stats(days=days)

    if stats["total_requests"] == 0:
        print("No telemetry data found for cache analysis.")
        print(f"Data location: {tracker.telemetry_dir}")
        return 0

    if RICH_AVAILABLE and Console is not None:
        console = Console()

        # Main stats table
        table = Table(
            title=f"Prompt Caching Stats (Last {days} Days)",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green", justify="right")

        # Cache hit rate
        hit_rate_color = "green" if stats["hit_rate"] > 0.5 else "yellow"
        table.add_row(
            "Cache Hit Rate",
            f"[{hit_rate_color}]{stats['hit_rate']:.1%}[/{hit_rate_color}]",
        )

        # Tokens
        table.add_row("Cache Reads", f"{stats['total_reads']:,} tokens")
        table.add_row("Cache Writes", f"{stats['total_writes']:,} tokens")

        # Cost savings
        savings_color = "green" if stats["savings"] > 0 else "dim"
        table.add_row(
            "Estimated Savings",
            f"[bold {savings_color}]${stats['savings']:.2f}[/bold {savings_color}]",
        )

        # Requests
        table.add_row("Requests with Cache Hits", f"{stats['hit_count']:,}")
        table.add_row("Total Requests", f"{stats['total_requests']:,}")

        console.print(table)

        # Per-workflow breakdown
        if stats["by_workflow"]:
            console.print("\n")
            wf_table = Table(
                title="Cache Performance by Workflow",
                show_header=True,
                header_style="bold magenta",
            )
            wf_table.add_column("Workflow", style="cyan")
            wf_table.add_column("Hit Rate", justify="right")
            wf_table.add_column("Reads", justify="right")
            wf_table.add_column("Writes", justify="right")

            # Sort by hit rate descending
            sorted_workflows = sorted(
                stats["by_workflow"].items(),
                key=lambda x: x[1].get("hit_rate", 0),
                reverse=True,
            )

            for workflow, wf_stats in sorted_workflows[:10]:  # Top 10
                hit_rate = wf_stats.get("hit_rate", 0.0)
                hit_rate_color = "green" if hit_rate > 0.5 else "yellow"
                wf_table.add_row(
                    workflow,
                    f"[{hit_rate_color}]{hit_rate:.1%}[/{hit_rate_color}]",
                    f"{wf_stats['reads']:,}",
                    f"{wf_stats['writes']:,}",
                )

            console.print(wf_table)

        # Recommendations
        if stats["hit_rate"] < 0.3:
            console.print("\n")
            console.print(
                Panel(
                    "[yellow]⚠ Cache hit rate is low (<30%)[/yellow]\n\n"
                    "Recommendations:\n"
                    "  • Increase reuse of system prompts across requests\n"
                    "  • Group similar requests together (5-min cache TTL)\n"
                    "  • Consider using workflow batching\n"
                    "  • Structure prompts with static content first",
                    title="Optimization Tips",
                    border_style="yellow",
                )
            )
    else:
        # Fallback to plain text
        print("\n" + "=" * 60)
        print(f"PROMPT CACHING STATS (LAST {days} DAYS)")
        print("=" * 60)
        print(f"Cache Hit Rate: {stats['hit_rate']:.1%}")
        print(f"Cache Reads: {stats['total_reads']:,} tokens")
        print(f"Cache Writes: {stats['total_writes']:,} tokens")
        print(f"Estimated Savings: ${stats['savings']:.2f}")
        print(f"Requests with Cache Hits: {stats['hit_count']:,}")
        print(f"Total Requests: {stats['total_requests']:,}")
        print("=" * 60)

        if stats["hit_rate"] < 0.3:
            print("\n⚠ Cache hit rate is low (<30%)")
            print("Recommendations:")
            print("  • Increase reuse of system prompts across requests")
            print("  • Group similar requests together (5-min cache TTL)")
            print("  • Consider using workflow batching")

    return 0


def cmd_telemetry_compare(args: Any) -> int:
    """Compare telemetry across two time periods.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success)

    """
    tracker = UsageTracker.get_instance()
    period1_days = getattr(args, "period1", 7)
    period2_days = getattr(args, "period2", 30)

    # Get stats for both periods
    stats1 = tracker.get_stats(days=period1_days)
    stats2 = tracker.get_stats(days=period2_days)

    if stats1["total_calls"] == 0 or stats2["total_calls"] == 0:
        print("Insufficient telemetry data for comparison.")
        return 0

    if RICH_AVAILABLE and Console is not None:
        console = Console()
        table = Table(title="Telemetry Comparison", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column(f"Last {period1_days} days", justify="right", style="green")
        table.add_column(f"Last {period2_days} days", justify="right", style="yellow")
        table.add_column("Change", justify="right", style="blue")

        # Total calls
        calls_change = (
            ((stats1["total_calls"] - stats2["total_calls"]) / stats2["total_calls"] * 100)
            if stats2["total_calls"] > 0
            else 0
        )
        table.add_row(
            "Total Calls",
            str(stats1["total_calls"]),
            str(stats2["total_calls"]),
            f"{calls_change:+.1f}%",
        )

        # Total cost
        cost_change = (
            ((stats1["total_cost"] - stats2["total_cost"]) / stats2["total_cost"] * 100)
            if stats2["total_cost"] > 0
            else 0
        )
        table.add_row(
            "Total Cost",
            f"${stats1['total_cost']:.2f}",
            f"${stats2['total_cost']:.2f}",
            f"{cost_change:+.1f}%",
        )

        # Avg cost per call
        avg1 = stats1["total_cost"] / stats1["total_calls"] if stats1["total_calls"] > 0 else 0
        avg2 = stats2["total_cost"] / stats2["total_calls"] if stats2["total_calls"] > 0 else 0
        avg_change = ((avg1 - avg2) / avg2 * 100) if avg2 > 0 else 0
        table.add_row(
            "Avg Cost/Call",
            f"${avg1:.4f}",
            f"${avg2:.4f}",
            f"{avg_change:+.1f}%",
        )

        # Cache hit rate
        cache_change = stats1["cache_hit_rate"] - stats2["cache_hit_rate"]
        table.add_row(
            "Cache Hit Rate",
            f"{stats1['cache_hit_rate']:.1f}%",
            f"{stats2['cache_hit_rate']:.1f}%",
            f"{cache_change:+.1f}pp",
        )

        console.print(table)
    else:
        # Fallback to plain text
        print("\n" + "=" * 80)
        print("TELEMETRY COMPARISON")
        print("=" * 80)
        print(
            f"{'Metric':<20} {'Last ' + str(period1_days) + ' days':>20} {'Last ' + str(period2_days) + ' days':>20} {'Change':>15}"
        )
        print("-" * 80)

        calls_change = (
            ((stats1["total_calls"] - stats2["total_calls"]) / stats2["total_calls"] * 100)
            if stats2["total_calls"] > 0
            else 0
        )
        print(
            f"{'Total Calls':<20} {stats1['total_calls']:>20} {stats2['total_calls']:>20} {calls_change:>14.1f}%"
        )

        cost_change = (
            ((stats1["total_cost"] - stats2["total_cost"]) / stats2["total_cost"] * 100)
            if stats2["total_cost"] > 0
            else 0
        )
        print(
            f"{'Total Cost':<20} ${stats1['total_cost']:>19.2f} ${stats2['total_cost']:>19.2f} {cost_change:>14.1f}%"
        )

        avg1 = stats1["total_cost"] / stats1["total_calls"] if stats1["total_calls"] > 0 else 0
        avg2 = stats2["total_cost"] / stats2["total_calls"] if stats2["total_calls"] > 0 else 0
        avg_change = ((avg1 - avg2) / avg2 * 100) if avg2 > 0 else 0
        print(f"{'Avg Cost/Call':<20} ${avg1:>19.4f} ${avg2:>19.4f} {avg_change:>14.1f}%")

        cache_change = stats1["cache_hit_rate"] - stats2["cache_hit_rate"]
        print(
            f"{'Cache Hit Rate':<20} {stats1['cache_hit_rate']:>19.1f}% {stats2['cache_hit_rate']:>19.1f}% {cache_change:>14.1f}pp"
        )

        print("=" * 80)

    return 0


def cmd_telemetry_reset(args: Any) -> int:
    """Reset/clear all telemetry data.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success)

    """
    tracker = UsageTracker.get_instance()
    confirm = getattr(args, "confirm", False)

    if not confirm:
        print("WARNING: This will permanently delete all telemetry data.")
        print(f"Location: {tracker.telemetry_dir}")
        print("\nUse --confirm to proceed.")
        return 1

    count = tracker.reset()
    print(f"Deleted {count} telemetry entries.")
    print("New tracking starts now.")
    return 0


def cmd_telemetry_export(args: Any) -> int:
    """Export telemetry data to JSON or CSV.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success)

    """
    tracker = UsageTracker.get_instance()
    format_type = getattr(args, "format", "json")
    output_file = getattr(args, "output", None)
    days = getattr(args, "days", None)

    entries = tracker.export_to_dict(days=days)

    if not entries:
        print("No telemetry data to export.")
        return 0

    if format_type == "json":
        # Export as JSON
        if output_file:
            validated_path = _validate_file_path(output_file)
            with open(validated_path, "w", encoding="utf-8") as f:
                json.dump(entries, f, indent=2)
            print(f"Exported {len(entries)} entries to {validated_path}")
        else:
            print(json.dumps(entries, indent=2))
    elif format_type == "csv":
        # Export as CSV
        if not entries:
            print("No data to export.")
            return 0

        # Get all possible fields
        fieldnames = [
            "ts",
            "workflow",
            "stage",
            "tier",
            "model",
            "provider",
            "cost",
            "tokens_input",
            "tokens_output",
            "cache_hit",
            "cache_type",
            "duration_ms",
        ]

        if output_file:
            validated_path = _validate_file_path(output_file)
            with open(validated_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for entry in entries:
                    row = {
                        "ts": entry.get("ts", ""),
                        "workflow": entry.get("workflow", ""),
                        "stage": entry.get("stage", ""),
                        "tier": entry.get("tier", ""),
                        "model": entry.get("model", ""),
                        "provider": entry.get("provider", ""),
                        "cost": entry.get("cost", 0.0),
                        "tokens_input": entry.get("tokens", {}).get("input", 0),
                        "tokens_output": entry.get("tokens", {}).get("output", 0),
                        "cache_hit": entry.get("cache", {}).get("hit", False),
                        "cache_type": entry.get("cache", {}).get("type", ""),
                        "duration_ms": entry.get("duration_ms", 0),
                    }
                    writer.writerow(row)
            print(f"Exported {len(entries)} entries to {validated_path}")
        else:
            # Print to stdout
            writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
            writer.writeheader()
            for entry in entries:
                row = {
                    "ts": entry.get("ts", ""),
                    "workflow": entry.get("workflow", ""),
                    "stage": entry.get("stage", ""),
                    "tier": entry.get("tier", ""),
                    "model": entry.get("model", ""),
                    "provider": entry.get("provider", ""),
                    "cost": entry.get("cost", 0.0),
                    "tokens_input": entry.get("tokens", {}).get("input", 0),
                    "tokens_output": entry.get("tokens", {}).get("output", 0),
                    "cache_hit": entry.get("cache", {}).get("hit", False),
                    "cache_type": entry.get("cache", {}).get("type", ""),
                    "duration_ms": entry.get("duration_ms", 0),
                }
                writer.writerow(row)
    else:
        print(f"Unknown format: {format_type}")
        print("Supported formats: json, csv")
        return 1

    return 0


# ==============================================================================
# Dashboard Commands
# ==============================================================================
# cmd_telemetry_dashboard and cmd_file_test_dashboard have been moved to:
# src/empathy_os/telemetry/commands/dashboard_commands.py
# They are imported at the top of this file for backward compatibility.
# ==============================================================================


# ==============================================================================
# Tier 1 Automation Monitoring CLI Commands
# ==============================================================================



# ==============================================================================
# Dashboard Commands (Extracted to Separate Module)
# ==============================================================================
# cmd_telemetry_dashboard and cmd_file_test_dashboard moved to:
# src/empathy_os/telemetry/commands/dashboard_commands.py
# Imported at top of file for backward compatibility.
# ==============================================================================

def cmd_tier1_status(args: Any) -> int:
    """Show comprehensive Tier 1 automation status.

    Args:
        args: Parsed command-line arguments (hours)

    Returns:
        Exit code (0 for success)
    """
    from datetime import timedelta

    from empathy_os.models.telemetry import TelemetryAnalytics, get_telemetry_store

    try:
        store = get_telemetry_store()
        analytics = TelemetryAnalytics(store)

        hours = getattr(args, "hours", 24)
        since = datetime.utcnow() - timedelta(hours=hours)

        summary = analytics.tier1_summary(since=since)
    except Exception as e:
        print(f"Error retrieving Tier 1 status: {e}")
        return 1

    if RICH_AVAILABLE and Console is not None:
        console = Console()

        # Task Routing Panel
        routing = summary["task_routing"]
        routing_text = Text()
        routing_text.append(f"Total Tasks: {routing['total_tasks']}\n")
        routing_text.append(f"Success Rate: {routing['accuracy_rate']:.1%}\n", style="green bold")
        routing_text.append(f"Avg Confidence: {routing['avg_confidence']:.2f}\n")

        # Test Execution Panel
        tests = summary["test_execution"]
        tests_text = Text()
        tests_text.append(f"Total Runs: {tests['total_executions']}\n")
        tests_text.append(f"Success Rate: {tests['success_rate']:.1%}\n", style="green bold")
        tests_text.append(f"Avg Duration: {tests['avg_duration_seconds']:.1f}s\n")
        tests_text.append(f"Total Failures: {tests['total_failures']}\n")

        # Coverage Panel
        coverage = summary["coverage"]
        coverage_text = Text()
        coverage_text.append(f"Current: {coverage['current_coverage']:.1f}%\n", style="cyan bold")
        coverage_text.append(f"Change: {coverage['change']:+.1f}%\n")
        coverage_text.append(f"Trend: {coverage['trend']}\n")
        coverage_text.append(f"Critical Gaps: {coverage['critical_gaps_count']}\n")

        # Agent Performance Panel
        agent = summary["agent_performance"]
        agent_text = Text()
        agent_text.append(f"Active Agents: {len(agent['by_agent'])}\n")
        agent_text.append(f"Automation Rate: {agent['automation_rate']:.1%}\n", style="green bold")
        agent_text.append(f"Human Review Rate: {agent['human_review_rate']:.1%}\n")

        # Display all panels
        console.print(f"\n[bold]Tier 1 Automation Status[/bold] (last {hours} hours)\n")
        console.print(Panel(routing_text, title="Task Routing", border_style="blue"))
        console.print(Panel(tests_text, title="Test Execution", border_style="green"))
        console.print(Panel(coverage_text, title="Coverage", border_style="cyan"))
        console.print(Panel(agent_text, title="Agent Performance", border_style="magenta"))
    else:
        # Plain text fallback
        routing = summary["task_routing"]
        tests = summary["test_execution"]
        coverage = summary["coverage"]
        agent = summary["agent_performance"]

        print(f"\nTier 1 Automation Status (last {hours} hours)")
        print("=" * 50)
        print("\nTask Routing:")
        print(f"  Total Tasks: {routing['total_tasks']}")
        print(f"  Success Rate: {routing['accuracy_rate']:.1%}")
        print(f"  Avg Confidence: {routing['avg_confidence']:.2f}")

        print("\nTest Execution:")
        print(f"  Total Runs: {tests['total_executions']}")
        print(f"  Success Rate: {tests['success_rate']:.1%}")
        print(f"  Avg Duration: {tests['avg_duration_seconds']:.1f}s")

        print("\nCoverage:")
        print(f"  Current: {coverage['current_coverage']:.1f}%")
        print(f"  Trend: {coverage['trend']}")

        print("\nAgent Performance:")
        print(f"  Active Agents: {len(agent['by_agent'])}")
        print(f"  Automation Rate: {agent['automation_rate']:.1%}")

    return 0


def cmd_task_routing_report(args: Any) -> int:
    """Show detailed task routing report.

    Args:
        args: Parsed command-line arguments (hours)

    Returns:
        Exit code (0 for success)
    """
    from datetime import timedelta

    from empathy_os.models.telemetry import TelemetryAnalytics, get_telemetry_store

    try:
        store = get_telemetry_store()
        analytics = TelemetryAnalytics(store)

        hours = getattr(args, "hours", 24)
        since = datetime.utcnow() - timedelta(hours=hours)

        stats = analytics.task_routing_accuracy(since=since)
    except Exception as e:
        print(f"Error retrieving task routing report: {e}")
        return 1

    if not stats["total_tasks"]:
        print(f"No task routing data found in the last {hours} hours.")
        return 0

    if RICH_AVAILABLE and Console is not None:
        console = Console()

        # Summary table
        table = Table(title=f"Task Routing Report (last {hours} hours)")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green", justify="right")

        table.add_row("Total Tasks", str(stats["total_tasks"]))
        table.add_row("Successful", str(stats["successful_routing"]))
        table.add_row("Accuracy Rate", f"{stats['accuracy_rate']:.1%}")
        table.add_row("Avg Confidence", f"{stats['avg_confidence']:.2f}")

        console.print(table)

        # By task type table
        if stats["by_task_type"]:
            type_table = Table(title="Breakdown by Task Type")
            type_table.add_column("Task Type", style="cyan")
            type_table.add_column("Total", justify="right")
            type_table.add_column("Success", justify="right")
            type_table.add_column("Rate", justify="right", style="green")

            for task_type, data in stats["by_task_type"].items():
                type_table.add_row(
                    task_type, str(data["total"]), str(data["success"]), f"{data['rate']:.1%}"
                )

            console.print(type_table)
    else:
        # Plain text fallback
        print(f"\nTask Routing Report (last {hours} hours)")
        print("=" * 50)
        print(f"Total Tasks: {stats['total_tasks']}")
        print(f"Successful: {stats['successful_routing']}")
        print(f"Accuracy Rate: {stats['accuracy_rate']:.1%}")
        print(f"Avg Confidence: {stats['avg_confidence']:.2f}")

        if stats["by_task_type"]:
            print("\nBy Task Type:")
            for task_type, data in stats["by_task_type"].items():
                print(f"  {task_type}: {data['success']}/{data['total']} ({data['rate']:.1%})")

    return 0


def cmd_test_status(args: Any) -> int:
    """Show test execution status.

    Args:
        args: Parsed command-line arguments (hours)

    Returns:
        Exit code (0 for success)
    """
    from datetime import timedelta

    from empathy_os.models.telemetry import TelemetryAnalytics, get_telemetry_store

    try:
        store = get_telemetry_store()
        analytics = TelemetryAnalytics(store)

        hours = getattr(args, "hours", 24)
        since = datetime.utcnow() - timedelta(hours=hours)

        stats = analytics.test_execution_trends(since=since)
        coverage = analytics.coverage_progress(since=since)
    except Exception as e:
        print(f"Error retrieving test status: {e}")
        return 1

    if not stats["total_executions"]:
        print(f"No test execution data found in the last {hours} hours.")
        return 0

    if RICH_AVAILABLE and Console is not None:
        console = Console()

        # Test execution table
        table = Table(title=f"Test Execution Status (last {hours} hours)")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green", justify="right")

        table.add_row("Total Runs", str(stats["total_executions"]))
        table.add_row("Success Rate", f"{stats['success_rate']:.1%}")
        table.add_row("Avg Duration", f"{stats['avg_duration_seconds']:.1f}s")
        table.add_row("Total Tests Run", str(stats["total_tests_run"]))
        table.add_row("Total Failures", str(stats["total_failures"]))
        table.add_row("Current Coverage", f"{coverage['current_coverage']:.1f}%")
        table.add_row("Coverage Trend", coverage["trend"])

        console.print(table)

        # Most failing tests
        if stats["most_failing_tests"]:
            fail_table = Table(title="Most Frequently Failing Tests")
            fail_table.add_column("Test Name", style="cyan")
            fail_table.add_column("Failures", justify="right", style="red")

            for test in stats["most_failing_tests"][:10]:
                fail_table.add_row(test["name"], str(test["failures"]))

            console.print(fail_table)
    else:
        # Plain text fallback
        print(f"\nTest Execution Status (last {hours} hours)")
        print("=" * 50)
        print(f"Total Runs: {stats['total_executions']}")
        print(f"Success Rate: {stats['success_rate']:.1%}")
        print(f"Avg Duration: {stats['avg_duration_seconds']:.1f}s")
        print(f"Total Tests Run: {stats['total_tests_run']}")
        print(f"Total Failures: {stats['total_failures']}")
        print(f"Current Coverage: {coverage['current_coverage']:.1f}%")

        if stats["most_failing_tests"]:
            print("\nMost Frequently Failing Tests:")
            for test in stats["most_failing_tests"][:10]:
                print(f"  {test['name']}: {test['failures']} failures")

    return 0


def cmd_agent_performance(args: Any) -> int:
    """Show agent performance metrics.

    Args:
        args: Parsed command-line arguments (hours)

    Returns:
        Exit code (0 for success)
    """
    from datetime import timedelta

    from empathy_os.models.telemetry import TelemetryAnalytics, get_telemetry_store

    try:
        store = get_telemetry_store()
        analytics = TelemetryAnalytics(store)

        hours = getattr(args, "hours", 168)  # Default 7 days for agent performance
        since = datetime.utcnow() - timedelta(hours=hours)

        stats = analytics.agent_performance(since=since)
    except Exception as e:
        print(f"Error retrieving agent performance: {e}")
        return 1

    if not stats["by_agent"]:
        print(f"No agent assignment data found in the last {hours} hours.")
        return 0

    if RICH_AVAILABLE and Console is not None:
        console = Console()

        # Agent performance table
        table = Table(title=f"Agent Performance (last {hours} hours)")
        table.add_column("Agent", style="cyan")
        table.add_column("Assignments", justify="right")
        table.add_column("Completed", justify="right")
        table.add_column("Success Rate", justify="right", style="green")
        table.add_column("Avg Duration", justify="right")

        for agent, data in stats["by_agent"].items():
            table.add_row(
                agent,
                str(data["assignments"]),
                str(data["completed"]),
                f"{data['success_rate']:.1%}",
                f"{data['avg_duration_hours']:.2f}h",
            )

        console.print(table)

        # Summary panel
        summary_text = Text()
        summary_text.append(
            f"Automation Rate: {stats['automation_rate']:.1%}\n", style="green bold"
        )
        summary_text.append(f"Human Review Rate: {stats['human_review_rate']:.1%}\n")

        console.print(Panel(summary_text, title="Summary", border_style="blue"))
    else:
        # Plain text fallback
        print(f"\nAgent Performance (last {hours} hours)")
        print("=" * 50)

        for agent, data in stats["by_agent"].items():
            print(f"\n{agent}:")
            print(f"  Assignments: {data['assignments']}")
            print(f"  Completed: {data['completed']}")
            print(f"  Success Rate: {data['success_rate']:.1%}")
            print(f"  Avg Duration: {data['avg_duration_hours']:.2f}h")

        print(f"\nAutomation Rate: {stats['automation_rate']:.1%}")
        print(f"Human Review Rate: {stats['human_review_rate']:.1%}")

    return 0


def cmd_sonnet_opus_analysis(args: Any) -> int:
    """Show Sonnet 4.5 → Opus 4.5 fallback analysis and cost savings.

    Args:
        args: Parsed command-line arguments (days)

    Returns:
        Exit code (0 for success)
    """
    from datetime import timedelta

    from empathy_os.models.telemetry import TelemetryAnalytics, get_telemetry_store

    store = get_telemetry_store()
    analytics = TelemetryAnalytics(store)

    days = getattr(args, "days", 30)
    since = datetime.utcnow() - timedelta(days=days)

    stats = analytics.sonnet_opus_fallback_analysis(since=since)

    if stats["total_calls"] == 0:
        print(f"No Sonnet/Opus calls found in the last {days} days.")
        return 0

    if RICH_AVAILABLE and Console is not None:
        console = Console()

        # Fallback Performance Panel
        perf_text = Text()
        perf_text.append(f"Total Anthropic Calls: {stats['total_calls']}\n")
        perf_text.append(f"Sonnet 4.5 Attempts: {stats['sonnet_attempts']}\n")
        perf_text.append(
            f"Sonnet Success Rate: {stats['success_rate_sonnet']:.1f}%\n",
            style="green bold",
        )
        perf_text.append(f"Opus Fallbacks: {stats['opus_fallbacks']}\n")
        perf_text.append(
            f"Fallback Rate: {stats['fallback_rate']:.1f}%\n",
            style="yellow bold" if stats["fallback_rate"] > 10 else "green",
        )

        console.print(
            Panel(
                perf_text,
                title=f"Sonnet 4.5 → Opus 4.5 Fallback Performance (last {days} days)",
                border_style="cyan",
            )
        )

        # Cost Savings Panel
        savings_text = Text()
        savings_text.append(f"Actual Cost: ${stats['actual_cost']:.2f}\n")
        savings_text.append(f"Always-Opus Cost: ${stats['always_opus_cost']:.2f}\n")
        savings_text.append(
            f"Savings: ${stats['savings']:.2f} ({stats['savings_percent']:.1f}%)\n",
            style="green bold",
        )
        savings_text.append("\n")
        savings_text.append(f"Avg Cost/Call (actual): ${stats['avg_cost_per_call']:.4f}\n")
        savings_text.append(f"Avg Cost/Call (all Opus): ${stats['avg_opus_cost_per_call']:.4f}\n")

        console.print(Panel(savings_text, title="Cost Savings Analysis", border_style="green"))

        # Recommendation
        if stats["fallback_rate"] < 5:
            rec_text = Text()
            rec_text.append("✅ Excellent Performance!\n", style="green bold")
            rec_text.append(
                f"Sonnet 4.5 handles {100 - stats['fallback_rate']:.1f}% of tasks successfully.\n"
            )
            rec_text.append(
                f"You're saving ${stats['savings']:.2f} compared to always using Opus.\n"
            )
            console.print(Panel(rec_text, title="Recommendation", border_style="green"))
        elif stats["fallback_rate"] < 15:
            rec_text = Text()
            rec_text.append("⚠️  Moderate Fallback Rate\n", style="yellow bold")
            rec_text.append(f"{stats['fallback_rate']:.1f}% of tasks need Opus fallback.\n")
            rec_text.append("Consider analyzing which tasks fail on Sonnet.\n")
            console.print(Panel(rec_text, title="Recommendation", border_style="yellow"))
        else:
            rec_text = Text()
            rec_text.append("❌ High Fallback Rate\n", style="red bold")
            rec_text.append(f"{stats['fallback_rate']:.1f}% of tasks need Opus fallback.\n")
            rec_text.append(
                "Consider using Opus directly for complex tasks to avoid retry overhead.\n"
            )
            console.print(Panel(rec_text, title="Recommendation", border_style="red"))
    else:
        # Plain text fallback
        print(f"\nSonnet 4.5 → Opus 4.5 Fallback Analysis (last {days} days)")
        print("=" * 60)
        print("\nFallback Performance:")
        print(f"  Total Anthropic Calls: {stats['total_calls']}")
        print(f"  Sonnet 4.5 Attempts: {stats['sonnet_attempts']}")
        print(f"  Sonnet Success Rate: {stats['success_rate_sonnet']:.1f}%")
        print(f"  Opus Fallbacks: {stats['opus_fallbacks']}")
        print(f"  Fallback Rate: {stats['fallback_rate']:.1f}%")
        print("\nCost Savings:")
        print(f"  Actual Cost: ${stats['actual_cost']:.2f}")
        print(f"  Always-Opus Cost: ${stats['always_opus_cost']:.2f}")
        print(f"  Savings: ${stats['savings']:.2f} ({stats['savings_percent']:.1f}%)")
        print(f"  Avg Cost/Call (actual): ${stats['avg_cost_per_call']:.4f}")
        print(f"  Avg Cost/Call (all Opus): ${stats['avg_opus_cost_per_call']:.4f}")

        if stats["fallback_rate"] < 5:
            print(f"\n✅ Excellent! Sonnet handles {100 - stats['fallback_rate']:.1f}% of tasks.")
        elif stats["fallback_rate"] < 15:
            print(f"\n⚠️  Moderate fallback rate ({stats['fallback_rate']:.1f}%).")
        else:
            print(f"\n❌ High fallback rate ({stats['fallback_rate']:.1f}%).")

    return 0


def cmd_file_test_status(args: Any) -> int:
    """Show per-file test status.

    Displays the test status for individual files, including:
    - Last test result (passed/failed/error/no_tests)
    - When tests were last run
    - Whether tests are stale (source modified since last test)

    Args:
        args: Parsed command-line arguments
            - file: Optional specific file to check
            - failed: Show only failed tests
            - stale: Show only stale tests
            - limit: Maximum files to show

    Returns:
        Exit code (0 for success)
    """
    from empathy_os.models.telemetry import get_telemetry_store

    try:
        store = get_telemetry_store()

        file_path = getattr(args, "file", None)
        failed_only = getattr(args, "failed", False)
        stale_only = getattr(args, "stale", False)
        limit = getattr(args, "limit", 50)

        if file_path:
            # Show status for a specific file
            record = store.get_latest_file_test(file_path)
            if record is None:
                print(f"No test record found for: {file_path}")
                return 0
            records = [record]
        else:
            # Get all file test records
            all_records = store.get_file_tests(limit=100000)

            if not all_records:
                print("No per-file test records found.")
                print("Run: empathy test-file <source_file> to track tests for a file.")
                return 0

            # Get latest record per file
            latest_by_file: dict[str, Any] = {}
            for record in all_records:
                existing = latest_by_file.get(record.file_path)
                if existing is None or record.timestamp > existing.timestamp:
                    latest_by_file[record.file_path] = record

            records = list(latest_by_file.values())

            # Apply filters
            if failed_only:
                records = [r for r in records if r.last_test_result in ("failed", "error")]
            if stale_only:
                records = [r for r in records if r.is_stale]

            # Sort by file path and limit
            records.sort(key=lambda r: r.file_path)
            records = records[:limit]

    except Exception as e:
        print(f"Error retrieving file test status: {e}")
        return 1

    if not records:
        filter_desc = []
        if failed_only:
            filter_desc.append("failed")
        if stale_only:
            filter_desc.append("stale")
        filter_str = " and ".join(filter_desc) if filter_desc else "matching"
        print(f"No {filter_str} file test records found.")
        return 0

    if RICH_AVAILABLE and Console is not None:
        console = Console()

        # Summary stats
        total = len(records)
        passed = sum(1 for r in records if r.last_test_result == "passed")
        failed = sum(1 for r in records if r.last_test_result in ("failed", "error"))
        no_tests = sum(1 for r in records if r.last_test_result == "no_tests")
        stale = sum(1 for r in records if r.is_stale)

        summary = Text()
        summary.append(f"Files: {total}  ", style="bold")
        summary.append(f"Passed: {passed}  ", style="green")
        summary.append(f"Failed: {failed}  ", style="red")
        summary.append(f"No Tests: {no_tests}  ", style="yellow")
        summary.append(f"Stale: {stale}", style="magenta")
        console.print(Panel(summary, title="Per-File Test Status Summary", border_style="cyan"))

        # File status table
        table = Table(title="File Test Status")
        table.add_column("File", style="cyan", max_width=50)
        table.add_column("Result", style="bold")
        table.add_column("Tests", justify="right")
        table.add_column("Passed", justify="right", style="green")
        table.add_column("Failed", justify="right", style="red")
        table.add_column("Duration", justify="right")
        table.add_column("Last Run", style="dim")
        table.add_column("Stale", style="magenta")

        for record in records:
            # Format result with color
            result = record.last_test_result
            if result == "passed":
                result_style = "green"
            elif result in ("failed", "error"):
                result_style = "red"
            elif result == "no_tests":
                result_style = "yellow"
            else:
                result_style = "dim"

            # Format timestamp
            try:
                dt = datetime.fromisoformat(record.timestamp.rstrip("Z"))
                ts_display = dt.strftime("%Y-%m-%d %H:%M")
            except (ValueError, AttributeError):
                ts_display = record.timestamp[:16] if record.timestamp else "-"

            # Stale indicator
            stale_str = "YES" if record.is_stale else ""

            table.add_row(
                record.file_path,
                Text(result, style=result_style),
                str(record.test_count),
                str(record.passed),
                str(record.failed + record.errors),
                f"{record.duration_seconds:.1f}s" if record.duration_seconds else "-",
                ts_display,
                stale_str,
            )

        console.print(table)

        # Show failed test details if any
        failed_records = [r for r in records if r.failed_tests]
        if failed_records:
            fail_table = Table(title="Failed Test Details")
            fail_table.add_column("File", style="cyan")
            fail_table.add_column("Test Name", style="red")
            fail_table.add_column("Error")

            for record in failed_records[:10]:
                for test in record.failed_tests[:3]:
                    fail_table.add_row(
                        record.file_path,
                        test.get("name", "unknown"),
                        test.get("error", "")[:50],
                    )

            console.print(fail_table)

    else:
        # Plain text fallback
        print("\nPer-File Test Status")
        print("=" * 80)

        for record in records:
            status = record.last_test_result.upper()
            stale_marker = " [STALE]" if record.is_stale else ""
            print(f"\n{record.file_path}")
            print(f"  Status: {status}{stale_marker}")
            print(
                f"  Tests: {record.test_count} (passed: {record.passed}, failed: {record.failed})"
            )
            if record.duration_seconds:
                print(f"  Duration: {record.duration_seconds:.1f}s")
            print(f"  Last Run: {record.timestamp[:19]}")

            if record.failed_tests:
                print("  Failed Tests:")
                for test in record.failed_tests[:3]:
                    print(f"    - {test.get('name', 'unknown')}: {test.get('error', '')[:40]}")

    return 0


