#!/usr/bin/env python3
"""Demonstration of Adaptive Model Routing (Pattern 3).

This script shows how the AdaptiveModelRouter uses historical telemetry
to select the best model for each workflow/stage combination.

Run this after you've accumulated some telemetry data:
    python examples/adaptive_routing_demo.py

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

from empathy_os.models import AdaptiveModelRouter
from empathy_os.telemetry import UsageTracker


def demo_adaptive_routing():
    """Demonstrate adaptive model routing based on telemetry."""
    print("=" * 70)
    print("ADAPTIVE MODEL ROUTING DEMONSTRATION")
    print("=" * 70)

    # Initialize router with telemetry
    tracker = UsageTracker.get_instance()
    router = AdaptiveModelRouter(telemetry=tracker)

    # Example 1: Get best model for code-review workflow
    print("\n📊 Example 1: Get Best Model for Code Review")
    print("-" * 70)

    model = router.get_best_model(
        workflow="code-review",
        stage="analysis",
        max_cost=0.01,  # Budget constraint: $0.01 per call
        min_success_rate=0.9,  # Require 90% success rate
    )

    print(f"✓ Selected model: {model}")
    print(f"  Constraints: max_cost=$0.01, min_success_rate=90%")

    # Example 2: Check if tier upgrade is recommended
    print("\n⚠️  Example 2: Check for Tier Upgrade Recommendations")
    print("-" * 70)

    should_upgrade, reason = router.recommend_tier_upgrade(
        workflow="code-review", stage="analysis"
    )

    if should_upgrade:
        print(f"🔴 UPGRADE RECOMMENDED: {reason}")
        print("  Action: Upgrading from CHEAP → CAPABLE tier")
    else:
        print(f"✓ No upgrade needed: {reason}")

    # Example 3: Get routing statistics
    print("\n📈 Example 3: Routing Statistics (Last 7 Days)")
    print("-" * 70)

    stats = router.get_routing_stats(workflow="code-review", days=7)

    print(f"Workflow: {stats['workflow']}")
    print(f"Total calls: {stats['total_calls']}")
    print(f"Average cost: ${stats['avg_cost']:.4f}")
    print(f"Average success rate: {stats['avg_success_rate']:.1%}")
    print(f"\nModels used: {', '.join(stats['models_used'])}")

    print("\nPer-Model Performance:")
    for model, perf in stats["performance_by_model"].items():
        print(f"  {model}:")
        print(f"    Calls: {perf['calls']}")
        print(f"    Success rate: {perf['success_rate']:.1%}")
        print(f"    Avg cost: ${perf['avg_cost']:.4f}")
        print(f"    Avg latency: {perf['avg_latency_ms']:.0f}ms")

    # Example 4: Compare multiple workflows
    print("\n🔍 Example 4: Compare Workflows")
    print("-" * 70)

    workflows = ["code-review", "bug-predict", "test-gen"]

    for workflow_name in workflows:
        try:
            stats = router.get_routing_stats(workflow=workflow_name, days=7)
            if stats["total_calls"] > 0:
                print(f"\n{workflow_name}:")
                print(f"  Calls: {stats['total_calls']}")
                print(f"  Avg cost: ${stats['avg_cost']:.4f}")
                print(f"  Success rate: {stats['avg_success_rate']:.1%}")
        except Exception:
            print(f"\n{workflow_name}: No data available")

    # Example 5: Show telemetry summary
    print("\n📊 Example 5: Overall Telemetry Summary")
    print("-" * 70)

    telemetry_stats = tracker.get_stats(days=7)

    print(f"Total LLM calls: {telemetry_stats['total_calls']:,}")
    print(f"Total cost: ${telemetry_stats['total_cost']:.2f}")
    print(f"Cache hit rate: {telemetry_stats['cache_hit_rate']:.1f}%")

    print("\nCost by tier:")
    for tier, cost in telemetry_stats["by_tier"].items():
        pct = (cost / telemetry_stats["total_cost"] * 100) if telemetry_stats["total_cost"] > 0 else 0
        print(f"  {tier}: ${cost:.2f} ({pct:.1f}%)")

    print("\nCost by workflow:")
    for workflow_name, cost in list(telemetry_stats["by_workflow"].items())[:5]:
        pct = (cost / telemetry_stats["total_cost"] * 100) if telemetry_stats["total_cost"] > 0 else 0
        print(f"  {workflow_name}: ${cost:.2f} ({pct:.1f}%)")

    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\n💡 Key Insights:")
    print("  • Adaptive routing selects the cheapest model that meets requirements")
    print("  • System automatically recommends tier upgrades on high failure rates")
    print("  • Telemetry history informs all routing decisions")
    print("  • No manual configuration needed - learns from experience")


if __name__ == "__main__":
    try:
        demo_adaptive_routing()
    except FileNotFoundError:
        print("⚠️  No telemetry data found.")
        print("Run some workflows first to generate telemetry:")
        print("  empathy workflow run code-review --input '{\"path\": \".\"}'")
        print("  empathy workflow run bug-predict")
        print("\nThen run this demo again.")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
