#!/usr/bin/env python3
"""Empathy Framework CLI.

IMPORTANT: This CLI is for automation only (git hooks, scripts, CI/CD).
For interactive use, use Claude Code skills in VSCode or Claude Desktop.

Automation commands:
    empathy workflow list              List available workflows
    empathy workflow run <name>        Execute a workflow
    empathy workflow info <name>       Show workflow details

Monitoring commands:
    empathy dashboard start            Start agent coordination dashboard
                                       (opens web UI at http://localhost:8000)

Utility commands:
    empathy telemetry show             Display usage summary
    empathy telemetry savings          Show cost savings
    empathy telemetry export           Export to CSV/JSON
    empathy telemetry routing-stats    Show adaptive routing statistics
    empathy telemetry routing-check    Check for tier upgrade recommendations
    empathy telemetry models           Show model performance by provider
    empathy telemetry agents           Show active agents and their status
    empathy telemetry signals          Show coordination signals for an agent

    empathy provider show              Show current provider config
    empathy provider set <name>        Set provider (anthropic, openai, hybrid)

    empathy validate                   Validate configuration
    empathy version                    Show version

For interactive development, use Claude Code skills:
    /dev        Developer tools (commit, review, debug, refactor)
    /testing    Run tests, coverage, generate tests
    /workflows  AI-powered workflows (security, bug prediction)
    /docs       Documentation generation
    /release    Release preparation
    /learning   Session evaluation and improvement
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import Namespace

logger = logging.getLogger(__name__)


def get_version() -> str:
    """Get package version."""
    try:
        from importlib.metadata import version

        return version("empathy-framework")
    except Exception:  # noqa: BLE001
        # INTENTIONAL: Fallback for dev installs without metadata
        return "dev"


# =============================================================================
# Workflow Commands
# =============================================================================


def cmd_workflow_list(args: Namespace) -> int:
    """List available workflows."""
    from empathy_os.workflows import discover_workflows

    workflows = discover_workflows()

    print("\n📋 Available Workflows\n")
    print("-" * 60)

    if not workflows:
        print("No workflows registered.")
        return 0

    for name, workflow_cls in sorted(workflows.items()):
        doc = workflow_cls.__doc__ or "No description"
        # Get first line of docstring
        description = doc.split("\n")[0].strip()
        print(f"  {name:25} {description}")

    print("-" * 60)
    print(f"\nTotal: {len(workflows)} workflows")
    print("\nRun a workflow: empathy workflow run <name>")
    return 0


def cmd_workflow_info(args: Namespace) -> int:
    """Show workflow details."""
    from empathy_os.workflows import discover_workflows

    workflows = discover_workflows()
    name = args.name
    if name not in workflows:
        print(f"❌ Workflow not found: {name}")
        print("\nAvailable workflows:")
        for wf_name in sorted(workflows.keys()):
            print(f"  - {wf_name}")
        return 1

    workflow_cls = workflows[name]
    print(f"\n📋 Workflow: {name}\n")
    print("-" * 60)

    # Show docstring
    if workflow_cls.__doc__:
        print(workflow_cls.__doc__)

    # Show input schema if available
    if hasattr(workflow_cls, "input_schema"):
        print("\nInput Schema:")
        print(json.dumps(workflow_cls.input_schema, indent=2))

    print("-" * 60)
    return 0


def cmd_workflow_run(args: Namespace) -> int:
    """Execute a workflow."""
    import asyncio

    from empathy_os.config import _validate_file_path
    from empathy_os.workflows import discover_workflows

    workflows = discover_workflows()
    name = args.name
    if name not in workflows:
        print(f"❌ Workflow not found: {name}")
        return 1

    # Parse input if provided
    input_data = {}
    if args.input:
        try:
            input_data = json.loads(args.input)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON input: {e}")
            return 1

    # Add common options with validation
    if args.path:
        try:
            # Validate path to prevent path traversal attacks
            validated_path = _validate_file_path(args.path)
            input_data["path"] = str(validated_path)
        except ValueError as e:
            print(f"❌ Invalid path: {e}")
            return 1
    if args.target:
        input_data["target"] = args.target

    print(f"\n🚀 Running workflow: {name}\n")

    try:
        workflow_cls = workflows[name]
        workflow = workflow_cls()

        # Run the workflow
        if asyncio.iscoroutinefunction(workflow.execute):
            result = asyncio.run(workflow.execute(**input_data))
        else:
            result = workflow.execute(**input_data)

        # Output result
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            if isinstance(result, dict):
                print("\n✅ Workflow completed\n")
                for key, value in result.items():
                    print(f"  {key}: {value}")
            else:
                print(f"\n✅ Result: {result}")

        return 0

    except Exception as e:  # noqa: BLE001
        # INTENTIONAL: CLI commands should catch all errors and report gracefully
        logger.exception(f"Workflow failed: {e}")
        print(f"\n❌ Workflow failed: {e}")
        return 1


# =============================================================================
# Telemetry Commands
# =============================================================================


def cmd_telemetry_show(args: Namespace) -> int:
    """Display usage summary."""
    try:
        from empathy_os.models.telemetry import TelemetryStore

        store = TelemetryStore()

        print("\n📊 Telemetry Summary\n")
        print("-" * 60)
        print(f"  Period:         Last {args.days} days")

        # Get workflow records from store
        # TODO: Consider adding aggregate methods to TelemetryStore for better performance
        # with large datasets (e.g., store.get_total_cost(), store.get_token_counts())
        workflows = store.get_workflows(limit=1000)
        calls = store.get_calls(limit=1000)

        if workflows:
            total_cost = sum(r.total_cost for r in workflows)
            total_tokens = sum(r.total_input_tokens + r.total_output_tokens for r in workflows)
            print(f"  Workflow runs:  {len(workflows):,}")
            print(f"  Total tokens:   {total_tokens:,}")
            print(f"  Total cost:     ${total_cost:.2f}")
        elif calls:
            total_cost = sum(c.estimated_cost for c in calls)
            total_tokens = sum(c.input_tokens + c.output_tokens for c in calls)
            print(f"  API calls:      {len(calls):,}")
            print(f"  Total tokens:   {total_tokens:,}")
            print(f"  Total cost:     ${total_cost:.2f}")
        else:
            print("  No telemetry data found.")

        print("-" * 60)
        return 0

    except ImportError:
        print("❌ Telemetry module not available")
        return 1
    except Exception as e:  # noqa: BLE001
        # INTENTIONAL: CLI commands should catch all errors and report gracefully
        logger.exception(f"Telemetry error: {e}")
        print(f"❌ Error: {e}")
        return 1


def cmd_telemetry_savings(args: Namespace) -> int:
    """Show cost savings from tier routing."""
    try:
        from empathy_os.models.telemetry import TelemetryStore

        store = TelemetryStore()

        print("\n💰 Cost Savings Report\n")
        print("-" * 60)
        print(f"  Period:              Last {args.days} days")

        # Calculate savings from workflow runs
        records = store.get_workflows(limit=1000)
        if records:
            actual_cost = sum(r.total_cost for r in records)
            total_tokens = sum(r.total_input_tokens + r.total_output_tokens for r in records)

            # Calculate what premium-only pricing would cost
            # Using Claude Opus pricing as premium baseline: ~$15/1M input, ~$75/1M output
            # Simplified: ~$45/1M tokens average (blended input/output)
            premium_rate_per_token = 45.0 / 1_000_000
            baseline_cost = total_tokens * premium_rate_per_token

            # Only show savings if we actually routed to cheaper models
            if baseline_cost > actual_cost:
                savings = baseline_cost - actual_cost
                savings_pct = (savings / baseline_cost * 100) if baseline_cost > 0 else 0

                print(f"  Actual cost:         ${actual_cost:.2f}")
                print(f"  Premium-only cost:   ${baseline_cost:.2f} (estimated)")
                print(f"  Savings:             ${savings:.2f}")
                print(f"  Savings percentage:  {savings_pct:.1f}%")
            else:
                print(f"  Total cost:          ${actual_cost:.2f}")
                print(f"  Total tokens:        {total_tokens:,}")
                print("\n  Note: No savings detected (may already be optimized)")

            print("\n  * Premium baseline assumes Claude Opus pricing (~$45/1M tokens)")
        else:
            print("  No telemetry data found.")

        print("-" * 60)
        return 0

    except ImportError:
        print("❌ Telemetry module not available")
        return 1
    except Exception as e:  # noqa: BLE001
        # INTENTIONAL: CLI commands should catch all errors and report gracefully
        logger.exception(f"Telemetry error: {e}")
        print(f"❌ Error: {e}")
        return 1


def cmd_telemetry_export(args: Namespace) -> int:
    """Export telemetry data to file."""
    from empathy_os.config import _validate_file_path

    try:
        from empathy_os.models.telemetry import TelemetryStore

        store = TelemetryStore()
        records = store.get_workflows(limit=10000)

        # Convert to exportable format
        data = [
            {
                "run_id": r.run_id,
                "workflow_name": r.workflow_name,
                "timestamp": r.started_at,
                "total_cost": r.total_cost,
                "input_tokens": r.total_input_tokens,
                "output_tokens": r.total_output_tokens,
                "success": r.success,
            }
            for r in records
        ]

        # Validate output path
        output_path = _validate_file_path(args.output)

        if args.format == "csv":
            import csv

            with output_path.open("w", newline="") as f:
                if data:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
            print(f"✅ Exported {len(data)} entries to {output_path}")

        elif args.format == "json":
            with output_path.open("w") as f:
                json.dump(data, f, indent=2, default=str)
            print(f"✅ Exported {len(data)} entries to {output_path}")

        return 0

    except ImportError:
        print("❌ Telemetry module not available")
        return 1
    except ValueError as e:
        print(f"❌ Invalid path: {e}")
        return 1
    except Exception as e:  # noqa: BLE001
        # INTENTIONAL: CLI commands should catch all errors and report gracefully
        logger.exception(f"Export error: {e}")
        print(f"❌ Error: {e}")
        return 1


def cmd_telemetry_routing_stats(args: Namespace) -> int:
    """Show adaptive routing statistics."""
    try:
        from empathy_os.models import AdaptiveModelRouter
        from empathy_os.telemetry import UsageTracker

        tracker = UsageTracker.get_instance()
        router = AdaptiveModelRouter(telemetry=tracker)

        workflow = args.workflow if hasattr(args, "workflow") and args.workflow else None
        stage = args.stage if hasattr(args, "stage") and args.stage else None
        days = args.days if hasattr(args, "days") else 7

        print("\n📊 Adaptive Routing Statistics\n")
        print("-" * 70)

        if workflow:
            # Show stats for specific workflow
            stats = router.get_routing_stats(workflow=workflow, stage=stage, days=days)

            if stats["total_calls"] == 0:
                print(f"\n  No data found for workflow: {workflow}")
                if stage:
                    print(f"  Stage: {stage}")
                return 0

            print(f"\n  Workflow:      {stats['workflow']}")
            if stage:
                print(f"  Stage:         {stage}")
            print(f"  Period:        Last {days} days")
            print(f"  Total calls:   {stats['total_calls']}")
            print(f"  Avg cost:      ${stats['avg_cost']:.4f}")
            print(f"  Success rate:  {stats['avg_success_rate']:.1%}")

            print(f"\n  Models used:   {', '.join(stats['models_used'])}")

            if stats["performance_by_model"]:
                print("\n  Per-Model Performance:")
                for model, perf in sorted(
                    stats["performance_by_model"].items(),
                    key=lambda x: x[1]["quality_score"],
                    reverse=True,
                ):
                    print(f"\n    {model}:")
                    print(f"      Calls:         {perf['calls']}")
                    print(f"      Success rate:  {perf['success_rate']:.1%}")
                    print(f"      Avg cost:      ${perf['avg_cost']:.4f}")
                    print(f"      Avg latency:   {perf['avg_latency_ms']:.0f}ms")
                    print(f"      Quality score: {perf['quality_score']:.2f}")

        else:
            # Show overall statistics
            stats = tracker.get_stats(days=days)

            if stats["total_calls"] == 0:
                print("\n  No telemetry data found.")
                return 0

            print(f"\n  Period:          Last {days} days")
            print(f"  Total calls:     {stats['total_calls']:,}")
            print(f"  Total cost:      ${stats['total_cost']:.2f}")
            print(f"  Cache hit rate:  {stats['cache_hit_rate']:.1f}%")

            print("\n  Cost by Tier:")
            for tier, cost in sorted(stats["by_tier"].items(), key=lambda x: x[1], reverse=True):
                pct = (cost / stats["total_cost"] * 100) if stats["total_cost"] > 0 else 0
                print(f"    {tier:8s}: ${cost:6.2f} ({pct:5.1f}%)")

            print("\n  Top Workflows:")
            for workflow_name, cost in list(stats["by_workflow"].items())[:5]:
                pct = (cost / stats["total_cost"] * 100) if stats["total_cost"] > 0 else 0
                print(f"    {workflow_name:30s}: ${cost:6.2f} ({pct:5.1f}%)")

        print("\n" + "-" * 70)
        return 0

    except ImportError as e:
        print(f"❌ Adaptive routing not available: {e}")
        print("   Ensure empathy-framework is installed with telemetry support")
        return 1
    except Exception as e:  # noqa: BLE001
        # INTENTIONAL: CLI commands should catch all errors and report gracefully
        logger.exception(f"Routing stats error: {e}")
        print(f"❌ Error: {e}")
        return 1


def cmd_telemetry_routing_check(args: Namespace) -> int:
    """Check for tier upgrade recommendations."""
    try:
        from empathy_os.models import AdaptiveModelRouter
        from empathy_os.telemetry import UsageTracker

        tracker = UsageTracker.get_instance()
        router = AdaptiveModelRouter(telemetry=tracker)

        workflow = args.workflow if hasattr(args, "workflow") and args.workflow else None
        check_all = args.all if hasattr(args, "all") else False

        print("\n🔍 Adaptive Routing Tier Upgrade Checks\n")
        print("-" * 70)

        if check_all:
            # Check all workflows
            stats = tracker.get_stats(days=7)
            workflows = list(stats["by_workflow"].keys())

            if not workflows:
                print("\n  No workflow data found.")
                return 0

            recommendations = []

            for wf_name in workflows:
                try:
                    should_upgrade, reason = router.recommend_tier_upgrade(
                        workflow=wf_name, stage=None
                    )

                    if should_upgrade:
                        recommendations.append(
                            {
                                "workflow": wf_name,
                                "reason": reason,
                            }
                        )
                except Exception:  # noqa: BLE001
                    # INTENTIONAL: Skip workflows without enough data
                    continue

            if recommendations:
                print("\n  ⚠️  Tier Upgrade Recommendations:\n")
                for rec in recommendations:
                    print(f"    Workflow: {rec['workflow']}")
                    print(f"    Reason:   {rec['reason']}")
                    print()
            else:
                print("\n  ✅ All workflows performing well - no upgrades needed.\n")

        elif workflow:
            # Check specific workflow
            should_upgrade, reason = router.recommend_tier_upgrade(workflow=workflow, stage=None)

            print(f"\n  Workflow: {workflow}")

            if should_upgrade:
                print("  Status:   ⚠️  UPGRADE RECOMMENDED")
                print(f"  Reason:   {reason}")
                print("\n  Action: Consider upgrading from CHEAP → CAPABLE or CAPABLE → PREMIUM")
            else:
                print("  Status:   ✅ Performing well")
                print(f"  Reason:   {reason}")

        else:
            print("\n  Error: Specify --workflow <name> or --all")
            return 1

        print("\n" + "-" * 70)
        return 0

    except ImportError as e:
        print(f"❌ Adaptive routing not available: {e}")
        return 1
    except Exception as e:  # noqa: BLE001
        # INTENTIONAL: CLI commands should catch all errors and report gracefully
        logger.exception(f"Routing check error: {e}")
        print(f"❌ Error: {e}")
        return 1


def cmd_telemetry_models(args: Namespace) -> int:
    """Show model performance by provider."""
    try:
        from empathy_os.telemetry import UsageTracker

        tracker = UsageTracker.get_instance()
        provider = args.provider if hasattr(args, "provider") else None
        days = args.days if hasattr(args, "days") else 7

        stats = tracker.get_stats(days=days)

        if stats["total_calls"] == 0:
            print("\n  No telemetry data found.")
            return 0

        print("\n📊 Model Performance\n")
        print("-" * 70)
        print(f"\n  Period: Last {days} days")

        # Get entries for analysis
        entries = tracker.get_recent_entries(limit=10000, days=days)

        # Group by provider and model
        model_stats: dict[str, dict[str, dict]] = {}

        for entry in entries:
            entry_provider = entry.get("provider", "unknown")
            if provider and entry_provider != provider:
                continue

            model = entry.get("model", "unknown")
            cost = entry.get("cost", 0.0)
            success = entry.get("success", True)
            duration = entry.get("duration_ms", 0)

            if entry_provider not in model_stats:
                model_stats[entry_provider] = {}

            if model not in model_stats[entry_provider]:
                model_stats[entry_provider][model] = {
                    "calls": 0,
                    "total_cost": 0.0,
                    "successes": 0,
                    "total_duration": 0,
                }

            model_stats[entry_provider][model]["calls"] += 1
            model_stats[entry_provider][model]["total_cost"] += cost
            if success:
                model_stats[entry_provider][model]["successes"] += 1
            model_stats[entry_provider][model]["total_duration"] += duration

        # Display by provider
        for prov, models in sorted(model_stats.items()):
            print(f"\n  Provider: {prov.upper()}")

            for model_name, mstats in sorted(
                models.items(), key=lambda x: x[1]["total_cost"], reverse=True
            ):
                calls = mstats["calls"]
                avg_cost = mstats["total_cost"] / calls if calls > 0 else 0
                success_rate = (mstats["successes"] / calls * 100) if calls > 0 else 0
                avg_duration = mstats["total_duration"] / calls if calls > 0 else 0

                print(f"\n    {model_name}:")
                print(f"      Calls:        {calls:,}")
                print(f"      Total cost:   ${mstats['total_cost']:.2f}")
                print(f"      Avg cost:     ${avg_cost:.4f}")
                print(f"      Success rate: {success_rate:.1f}%")
                print(f"      Avg duration: {avg_duration:.0f}ms")

        print("\n" + "-" * 70)
        return 0

    except ImportError as e:
        print(f"❌ Telemetry not available: {e}")
        return 1
    except Exception as e:  # noqa: BLE001
        # INTENTIONAL: CLI commands should catch all errors and report gracefully
        logger.exception(f"Models error: {e}")
        print(f"❌ Error: {e}")
        return 1


def cmd_telemetry_agents(args: Namespace) -> int:
    """Show active agents and their status."""
    try:
        from empathy_os.telemetry import HeartbeatCoordinator

        coordinator = HeartbeatCoordinator()
        active_agents = coordinator.get_active_agents()

        print("\n🤖 Active Agents\n")
        print("-" * 70)

        if not active_agents:
            print("\n  No active agents found.")
            print("  (Agents must use HeartbeatCoordinator to be tracked)")
            return 0

        print(f"\n  Found {len(active_agents)} active agent(s):\n")

        for agent in sorted(active_agents, key=lambda a: a.last_beat, reverse=True):
            # Calculate time since last beat
            from datetime import datetime

            now = datetime.utcnow()
            time_since = (now - agent.last_beat).total_seconds()

            # Status indicator
            if agent.status in ("completed", "failed", "cancelled"):
                status_icon = "✅" if agent.status == "completed" else "❌"
            elif time_since > 30:
                status_icon = "⚠️"  # Stale
            else:
                status_icon = "🟢"  # Active

            print(f"  {status_icon} {agent.agent_id}")
            print(f"      Status:       {agent.status}")
            print(f"      Progress:     {agent.progress*100:.1f}%")
            print(f"      Task:         {agent.current_task}")
            print(f"      Last beat:    {time_since:.1f}s ago")

            # Show metadata if present
            if agent.metadata:
                workflow = agent.metadata.get("workflow", "")
                if workflow:
                    print(f"      Workflow:     {workflow}")
            print()

        print("-" * 70)
        return 0

    except ImportError as e:
        print(f"❌ Agent tracking not available: {e}")
        return 1
    except Exception as e:  # noqa: BLE001
        # INTENTIONAL: CLI commands should catch all errors and report gracefully
        logger.exception(f"Agents error: {e}")
        print(f"❌ Error: {e}")
        return 1


def cmd_telemetry_signals(args: Namespace) -> int:
    """Show coordination signals."""
    try:
        from empathy_os.telemetry import CoordinationSignals

        agent_id = args.agent if hasattr(args, "agent") else None

        if not agent_id:
            print("❌ Error: --agent <id> required to view signals")
            return 1

        coordinator = CoordinationSignals(agent_id=agent_id)
        signals = coordinator.get_pending_signals()

        print(f"\n📡 Coordination Signals for {agent_id}\n")
        print("-" * 70)

        if not signals:
            print("\n  No pending signals.")
            return 0

        print(f"\n  Found {len(signals)} pending signal(s):\n")

        for signal in sorted(signals, key=lambda s: s.timestamp, reverse=True):
            # Calculate age
            from datetime import datetime

            now = datetime.utcnow()
            age = (now - signal.timestamp).total_seconds()

            # Signal type indicator
            type_icons = {
                "task_complete": "✅",
                "abort": "🛑",
                "ready": "🟢",
                "checkpoint": "🔄",
                "error": "❌",
            }
            icon = type_icons.get(signal.signal_type, "📨")

            print(f"  {icon} {signal.signal_type}")
            print(f"      From:         {signal.source_agent}")
            print(f"      Target:       {signal.target_agent or '* (broadcast)'}")
            print(f"      Age:          {age:.1f}s")
            print(f"      Expires in:   {signal.ttl_seconds - age:.1f}s")

            # Show payload summary
            if signal.payload:
                payload_str = str(signal.payload)
                if len(payload_str) > 60:
                    payload_str = payload_str[:57] + "..."
                print(f"      Payload:      {payload_str}")
            print()

        print("-" * 70)
        return 0

    except ImportError as e:
        print(f"❌ Coordination signals not available: {e}")
        return 1
    except Exception as e:  # noqa: BLE001
        # INTENTIONAL: CLI commands should catch all errors and report gracefully
        logger.exception(f"Signals error: {e}")
        print(f"❌ Error: {e}")
        return 1


# =============================================================================
# Provider Commands
# =============================================================================


def cmd_provider_show(args: Namespace) -> int:
    """Show current provider configuration."""
    try:
        from empathy_os.models.provider_config import get_provider_config

        config = get_provider_config()

        print("\n🔧 Provider Configuration\n")
        print("-" * 60)
        print(f"  Mode:            {config.mode.value}")
        print(f"  Primary provider: {config.primary_provider}")
        print(f"  Cost optimization: {'✅ Enabled' if config.cost_optimization else '❌ Disabled'}")

        if config.available_providers:
            print("\n  Available providers:")
            for provider in config.available_providers:
                status = "✓" if provider == config.primary_provider else " "
                print(f"    [{status}] {provider}")
        else:
            print("\n  ⚠️  No API keys detected")
            print("  Set ANTHROPIC_API_KEY, OPENAI_API_KEY, or GOOGLE_API_KEY")

        print("-" * 60)
        return 0

    except ImportError:
        print("❌ Provider module not available")
        return 1
    except Exception as e:  # noqa: BLE001
        # INTENTIONAL: CLI commands should catch all errors and report gracefully
        logger.exception(f"Provider error: {e}")
        print(f"❌ Error: {e}")
        return 1


def cmd_provider_set(args: Namespace) -> int:
    """Set the LLM provider."""
    try:
        from empathy_os.models.provider_config import (
            ProviderMode,
            get_provider_config,
            set_provider_config,
        )

        # Get current config and update
        config = get_provider_config()

        if args.name == "hybrid":
            config.mode = ProviderMode.HYBRID
            print("✅ Provider mode set to: hybrid (multi-provider)")
        else:
            config.mode = ProviderMode.SINGLE
            config.primary_provider = args.name
            print(f"✅ Provider set to: {args.name}")

        set_provider_config(config)
        return 0

    except ImportError:
        print("❌ Provider module not available")
        return 1
    except Exception as e:  # noqa: BLE001
        # INTENTIONAL: CLI commands should catch all errors and report gracefully
        logger.exception(f"Provider error: {e}")
        print(f"❌ Error: {e}")
        return 1


# =============================================================================
# Dashboard Commands
# =============================================================================


def cmd_dashboard_start(args: Namespace) -> int:
    """Start the agent coordination dashboard."""
    try:
        from empathy_os.dashboard import run_standalone_dashboard

        # Get host and port from args
        host = args.host
        port = args.port

        print("\n🚀 Starting Agent Coordination Dashboard...")
        print(f"📊 Dashboard will be available at: http://{host}:{port}\n")
        print("💡 Make sure Redis is populated with test data:")
        print("   python scripts/populate_redis_direct.py\n")
        print("Press Ctrl+C to stop\n")

        # Start dashboard
        run_standalone_dashboard(host=host, port=port)
        return 0

    except KeyboardInterrupt:
        print("\n\n🛑 Dashboard stopped")
        return 0
    except ImportError as e:
        print(f"❌ Dashboard not available: {e}")
        print("   Install dashboard dependencies: pip install redis")
        return 1
    except Exception as e:  # noqa: BLE001
        # INTENTIONAL: CLI commands should catch all errors and report gracefully
        logger.exception(f"Dashboard error: {e}")
        print(f"❌ Error starting dashboard: {e}")
        return 1


# =============================================================================
# Utility Commands
# =============================================================================


def cmd_validate(args: Namespace) -> int:
    """Validate configuration."""
    print("\n🔍 Validating configuration...\n")

    errors = []
    warnings = []

    # Check config file
    config_paths = [
        Path("empathy.config.json"),
        Path("empathy.config.yml"),
        Path("empathy.config.yaml"),
    ]

    config_found = False
    for config_path in config_paths:
        if config_path.exists():
            config_found = True
            print(f"  ✅ Config file: {config_path}")
            break

    if not config_found:
        warnings.append("No empathy.config file found (using defaults)")

    # Check for API keys
    import os

    api_keys = {
        "ANTHROPIC_API_KEY": "Anthropic (Claude)",
        "OPENAI_API_KEY": "OpenAI (GPT)",
        "GOOGLE_API_KEY": "Google (Gemini)",
    }

    keys_found = 0
    for key, name in api_keys.items():
        if os.environ.get(key):
            print(f"  ✅ {name} API key set")
            keys_found += 1

    if keys_found == 0:
        errors.append(
            "No API keys found. Set at least one: ANTHROPIC_API_KEY, OPENAI_API_KEY, or GOOGLE_API_KEY"
        )

    # Check workflows directory
    try:
        from empathy_os.workflows import WORKFLOW_REGISTRY

        print(f"  ✅ {len(WORKFLOW_REGISTRY)} workflows registered")
    except ImportError as e:
        warnings.append(f"Could not load workflows: {e}")

    # Summary
    print("\n" + "-" * 60)

    if errors:
        print("\n❌ Validation failed:")
        for error in errors:
            print(f"   - {error}")
        return 1

    if warnings:
        print("\n⚠️  Warnings:")
        for warning in warnings:
            print(f"   - {warning}")

    print("\n✅ Configuration is valid")
    return 0


def cmd_version(args: Namespace) -> int:
    """Show version information."""
    version = get_version()
    print(f"empathy-framework {version}")

    if args.verbose:
        print(f"\nPython: {sys.version}")
        print(f"Platform: {sys.platform}")

        # Show installed extras
        try:
            from importlib.metadata import requires

            reqs = requires("empathy-framework") or []
            print(f"\nDependencies: {len(reqs)}")
        except Exception:  # noqa: BLE001
            pass

    return 0


# =============================================================================
# Convenience Commands (Keyword Shortcuts)
# =============================================================================
# Main Entry Point
# =============================================================================


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="empathy",
        description="Empathy Framework CLI (automation interface - for git hooks, scripts, CI/CD)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
NOTE: This CLI is for automation only. For interactive development,
use Claude Code skills in VSCode or Claude Desktop:

    /dev        Developer tools (commit, review, debug, refactor)
    /testing    Run tests, coverage, generate tests
    /workflows  AI-powered workflows (security, bug prediction)
    /learning   Session evaluation

Documentation: https://smartaimemory.com/framework-docs/
        """,
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- Workflow commands ---
    workflow_parser = subparsers.add_parser("workflow", help="Workflow management")
    workflow_sub = workflow_parser.add_subparsers(dest="workflow_command")

    # workflow list
    workflow_sub.add_parser("list", help="List available workflows")

    # workflow info
    info_parser = workflow_sub.add_parser("info", help="Show workflow details")
    info_parser.add_argument("name", help="Workflow name")

    # workflow run
    run_parser = workflow_sub.add_parser("run", help="Run a workflow")
    run_parser.add_argument("name", help="Workflow name")
    run_parser.add_argument("--input", "-i", help="JSON input data")
    run_parser.add_argument("--path", "-p", help="Target path")
    run_parser.add_argument("--target", "-t", help="Target value (e.g., coverage target)")
    run_parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")

    # --- Telemetry commands ---
    telemetry_parser = subparsers.add_parser("telemetry", help="Usage telemetry")
    telemetry_sub = telemetry_parser.add_subparsers(dest="telemetry_command")

    # telemetry show
    show_parser = telemetry_sub.add_parser("show", help="Display usage summary")
    show_parser.add_argument(
        "--days", "-d", type=int, default=30, help="Number of days (default: 30)"
    )

    # telemetry savings
    savings_parser = telemetry_sub.add_parser("savings", help="Show cost savings")
    savings_parser.add_argument(
        "--days", "-d", type=int, default=30, help="Number of days (default: 30)"
    )

    # telemetry export
    export_parser = telemetry_sub.add_parser("export", help="Export telemetry data")
    export_parser.add_argument("--output", "-o", required=True, help="Output file path")
    export_parser.add_argument(
        "--format", "-f", choices=["csv", "json"], default="json", help="Output format"
    )
    export_parser.add_argument(
        "--days", "-d", type=int, default=30, help="Number of days (default: 30)"
    )

    # telemetry routing-stats
    routing_stats_parser = telemetry_sub.add_parser(
        "routing-stats", help="Show adaptive routing statistics"
    )
    routing_stats_parser.add_argument("--workflow", "-w", help="Workflow name")
    routing_stats_parser.add_argument("--stage", "-s", help="Stage name")
    routing_stats_parser.add_argument(
        "--days", "-d", type=int, default=7, help="Number of days (default: 7)"
    )

    # telemetry routing-check
    routing_check_parser = telemetry_sub.add_parser(
        "routing-check", help="Check for tier upgrade recommendations"
    )
    routing_check_parser.add_argument("--workflow", "-w", help="Workflow name")
    routing_check_parser.add_argument(
        "--all", "-a", action="store_true", help="Check all workflows"
    )

    # telemetry models
    models_parser = telemetry_sub.add_parser("models", help="Show model performance by provider")
    models_parser.add_argument(
        "--provider",
        "-p",
        choices=["anthropic", "openai", "google"],
        help="Filter by provider",
    )
    models_parser.add_argument(
        "--days", "-d", type=int, default=7, help="Number of days (default: 7)"
    )

    # telemetry agents
    telemetry_sub.add_parser("agents", help="Show active agents and their status")

    # telemetry signals
    signals_parser = telemetry_sub.add_parser("signals", help="Show coordination signals")
    signals_parser.add_argument("--agent", "-a", required=True, help="Agent ID to view signals for")

    # --- Provider commands ---
    provider_parser = subparsers.add_parser("provider", help="LLM provider configuration")
    provider_sub = provider_parser.add_subparsers(dest="provider_command")

    # provider show
    provider_sub.add_parser("show", help="Show current provider")

    # provider set
    set_parser = provider_sub.add_parser("set", help="Set provider")
    set_parser.add_argument("name", choices=["anthropic", "openai", "hybrid"], help="Provider name")

    # --- Dashboard commands ---
    dashboard_parser = subparsers.add_parser("dashboard", help="Agent coordination dashboard")
    dashboard_sub = dashboard_parser.add_subparsers(dest="dashboard_command")

    # dashboard start
    start_parser = dashboard_sub.add_parser("start", help="Start dashboard web server")
    start_parser.add_argument("--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)")
    start_parser.add_argument("--port", type=int, default=8000, help="Port to bind to (default: 8000)")

    # --- Utility commands ---
    subparsers.add_parser("validate", help="Validate configuration")

    version_parser = subparsers.add_parser("version", help="Show version")
    version_parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed info")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)

    # Configure logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    # Route to command handlers
    if args.command == "workflow":
        if args.workflow_command == "list":
            return cmd_workflow_list(args)
        elif args.workflow_command == "info":
            return cmd_workflow_info(args)
        elif args.workflow_command == "run":
            return cmd_workflow_run(args)
        else:
            print("Usage: empathy workflow {list|info|run}")
            return 1

    elif args.command == "telemetry":
        if args.telemetry_command == "show":
            return cmd_telemetry_show(args)
        elif args.telemetry_command == "savings":
            return cmd_telemetry_savings(args)
        elif args.telemetry_command == "export":
            return cmd_telemetry_export(args)
        elif args.telemetry_command == "routing-stats":
            return cmd_telemetry_routing_stats(args)
        elif args.telemetry_command == "routing-check":
            return cmd_telemetry_routing_check(args)
        elif args.telemetry_command == "models":
            return cmd_telemetry_models(args)
        elif args.telemetry_command == "agents":
            return cmd_telemetry_agents(args)
        elif args.telemetry_command == "signals":
            return cmd_telemetry_signals(args)
        else:
            print("Usage: empathy telemetry {show|savings|export|routing-stats|routing-check|models|agents|signals}")
            return 1

    elif args.command == "provider":
        if args.provider_command == "show":
            return cmd_provider_show(args)
        elif args.provider_command == "set":
            return cmd_provider_set(args)
        else:
            print("Usage: empathy provider {show|set}")
            return 1

    elif args.command == "dashboard":
        if args.dashboard_command == "start":
            return cmd_dashboard_start(args)
        else:
            print("Usage: empathy dashboard start [--host HOST] [--port PORT]")
            return 1

    elif args.command == "validate":
        return cmd_validate(args)

    elif args.command == "version":
        return cmd_version(args)

    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
