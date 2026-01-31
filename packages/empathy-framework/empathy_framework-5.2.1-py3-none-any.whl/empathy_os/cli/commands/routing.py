"""CLI commands for adaptive model routing statistics.

Provides commands to analyze model routing performance and get tier upgrade
recommendations based on historical telemetry data.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

import logging
from typing import Any

from empathy_os.models import AdaptiveModelRouter
from empathy_os.telemetry import UsageTracker

logger = logging.getLogger(__name__)


def cmd_routing_stats(args: Any) -> int:
    """Show routing statistics for a workflow.

    Args:
        args: Arguments with workflow, stage (optional), days

    Returns:
        0 on success, 1 on error
    """
    try:
        # Get telemetry and router
        tracker = UsageTracker.get_instance()
        router = AdaptiveModelRouter(telemetry=tracker)

        # Get routing stats
        stats = router.get_routing_stats(
            workflow=args.workflow,
            stage=args.stage if hasattr(args, "stage") and args.stage else None,
            days=args.days,
        )

        if stats["total_calls"] == 0:
            print(f"❌ No data found for workflow '{args.workflow}'")
            print(f"   (searched last {args.days} days)")
            return 1

        # Display stats
        print("\n" + "=" * 70)
        print(f"ADAPTIVE ROUTING STATISTICS - {stats['workflow']}")
        if stats["stage"] != "all":
            print(f"Stage: {stats['stage']}")
        print("=" * 70)

        print(f"\n📊 Overview (Last {stats['days_analyzed']} days)")
        print(f"  Total calls: {stats['total_calls']:,}")
        print(f"  Average cost: ${stats['avg_cost']:.4f}")
        print(f"  Average success rate: {stats['avg_success_rate']:.1%}")
        print(f"  Models used: {len(stats['models_used'])}")

        # Per-model performance
        print("\n📈 Per-Model Performance")
        print("-" * 70)

        for model in stats["models_used"]:
            perf = stats["performance_by_model"][model]
            print(f"\n  {model}:")
            print(f"    Calls: {perf['calls']:,}")
            print(f"    Success rate: {perf['success_rate']:.1%}")
            print(f"    Avg cost: ${perf['avg_cost']:.4f}")
            print(f"    Avg latency: {perf['avg_latency_ms']:.0f}ms")

            # Quality score calculation (from AdaptiveModelRouter)
            quality_score = (perf["success_rate"] * 100) - (perf["avg_cost"] * 10)
            print(f"    Quality score: {quality_score:.2f}")

        # Recommendations
        print("\n💡 Recommendations")
        print("-" * 70)

        # Find best model
        best_model = max(
            stats["performance_by_model"].items(),
            key=lambda x: (x[1]["success_rate"] * 100) - (x[1]["avg_cost"] * 10),
        )

        print(f"  Best model: {best_model[0]}")
        print(f"    ({best_model[1]['success_rate']:.1%} success, ${best_model[1]['avg_cost']:.4f}/call)")

        # Cost savings potential
        if len(stats["models_used"]) > 1:
            cheapest = min(
                stats["performance_by_model"].items(),
                key=lambda x: x[1]["avg_cost"],
            )
            most_expensive = max(
                stats["performance_by_model"].items(),
                key=lambda x: x[1]["avg_cost"],
            )

            if cheapest[0] != most_expensive[0]:
                savings_per_call = most_expensive[1]["avg_cost"] - cheapest[1]["avg_cost"]
                print("\n  💰 Potential savings:")
                print(f"    Using {cheapest[0]} instead of {most_expensive[0]}")
                print(f"    ${savings_per_call:.4f} per call")
                if stats["total_calls"] > 0:
                    weekly_calls = (stats["total_calls"] / stats["days_analyzed"]) * 7
                    weekly_savings = savings_per_call * weekly_calls
                    print(f"    ~${weekly_savings:.2f}/week potential")

        return 0

    except Exception as e:
        logger.exception("Failed to get routing stats")
        print(f"❌ Error: {e}")
        return 1


def cmd_routing_check(args: Any) -> int:
    """Check if tier upgrades are recommended for workflows.

    Args:
        args: Arguments with workflow (or --all), stage (optional)

    Returns:
        0 on success, 1 on error
    """
    try:
        # Get telemetry and router
        tracker = UsageTracker.get_instance()
        router = AdaptiveModelRouter(telemetry=tracker)

        print("\n" + "=" * 70)
        print("ADAPTIVE ROUTING - TIER UPGRADE RECOMMENDATIONS")
        print("=" * 70)

        if hasattr(args, "all") and args.all:
            # Check all workflows
            stats = tracker.get_stats(days=args.days)
            workflows = list(stats["by_workflow"].keys())

            if not workflows:
                print("\n❌ No workflow data found")
                return 1

            print(f"\nChecking {len(workflows)} workflows (last {args.days} days)...\n")

            upgrades_needed = []
            upgrades_ok = []

            for workflow_name in workflows:
                should_upgrade, reason = router.recommend_tier_upgrade(
                    workflow=workflow_name, stage=None
                )

                if should_upgrade:
                    upgrades_needed.append((workflow_name, reason))
                else:
                    upgrades_ok.append((workflow_name, reason))

            # Show workflows needing upgrades
            if upgrades_needed:
                print(f"⚠️  {len(upgrades_needed)} workflow(s) need tier upgrade:")
                print("-" * 70)
                for workflow_name, reason in upgrades_needed:
                    print(f"  • {workflow_name}")
                    print(f"    {reason}")
                print()

            # Show workflows performing well
            if upgrades_ok:
                print(f"✓ {len(upgrades_ok)} workflow(s) performing well:")
                print("-" * 70)
                for workflow_name, reason in upgrades_ok:
                    print(f"  • {workflow_name}: {reason}")
                print()

            # Summary
            if upgrades_needed:
                print("💡 Recommendation:")
                print("   Enable adaptive routing to automatically upgrade tiers:")
                print("   workflow = MyWorkflow(enable_adaptive_routing=True)")
                return 0
            else:
                print("✓ All workflows performing well - no upgrades needed")
                return 0

        else:
            # Check specific workflow
            workflow_name = args.workflow

            should_upgrade, reason = router.recommend_tier_upgrade(
                workflow=workflow_name,
                stage=args.stage if hasattr(args, "stage") and args.stage else None,
            )

            print(f"\nWorkflow: {workflow_name}")
            if hasattr(args, "stage") and args.stage:
                print(f"Stage: {args.stage}")
            print(f"Analysis period: Last {args.days} days")
            print()

            if should_upgrade:
                print("⚠️  TIER UPGRADE RECOMMENDED")
                print(f"   {reason}")
                print()
                print("💡 Action:")
                print("   1. Enable adaptive routing:")
                print("      workflow = MyWorkflow(enable_adaptive_routing=True)")
                print("   2. Or manually upgrade tier in workflow config")
                return 0
            else:
                print("✓ NO UPGRADE NEEDED")
                print(f"   {reason}")
                return 0

    except Exception as e:
        logger.exception("Failed to check routing recommendations")
        print(f"❌ Error: {e}")
        return 1


def cmd_routing_models(args: Any) -> int:
    """Show model performance comparison.

    Args:
        args: Arguments with provider, days

    Returns:
        0 on success, 1 on error
    """
    try:
        # Get telemetry
        tracker = UsageTracker.get_instance()

        # Get recent entries
        entries = tracker.get_recent_entries(limit=100000, days=args.days)

        if args.provider:
            entries = [e for e in entries if e.get("provider") == args.provider]

        if not entries:
            print(f"❌ No data found for provider '{args.provider}'")
            return 1

        # Group by model
        by_model: dict[str, list] = {}
        for entry in entries:
            model = entry["model"]
            if model not in by_model:
                by_model[model] = []
            by_model[model].append(entry)

        print("\n" + "=" * 70)
        print(f"MODEL PERFORMANCE COMPARISON - {args.provider.upper()}")
        print(f"Last {args.days} days")
        print("=" * 70)

        # Sort by total calls
        models_sorted = sorted(by_model.items(), key=lambda x: len(x[1]), reverse=True)

        print(f"\n📊 {len(models_sorted)} model(s) used\n")

        for model, model_entries in models_sorted:
            total = len(model_entries)
            successes = sum(1 for e in model_entries if e.get("success", True))
            success_rate = successes / total

            avg_cost = sum(e.get("cost", 0.0) for e in model_entries) / total
            avg_latency = sum(e.get("duration_ms", 0) for e in model_entries) / total

            # Quality score
            quality_score = (success_rate * 100) - (avg_cost * 10)

            print(f"  {model}")
            print(f"    Calls: {total:,}")
            print(f"    Success rate: {success_rate:.1%}")
            print(f"    Avg cost: ${avg_cost:.4f}")
            print(f"    Avg latency: {avg_latency:.0f}ms")
            print(f"    Quality score: {quality_score:.2f}")
            print()

        return 0

    except Exception as e:
        logger.exception("Failed to get model performance")
        print(f"❌ Error: {e}")
        return 1
