#!/usr/bin/env python3
"""Analyze telemetry and suggest if adaptive routing would save money.

This script checks your telemetry data and recommends enabling adaptive
routing if it would provide significant cost savings.

Run: python examples/suggest_adaptive_routing.py

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from empathy_os.models import AdaptiveModelRouter
from empathy_os.telemetry import UsageTracker


def analyze_savings_potential():
    """Analyze telemetry and suggest adaptive routing if beneficial."""
    print("=" * 70)
    print("ADAPTIVE ROUTING SAVINGS ANALYSIS")
    print("=" * 70)

    try:
        tracker = UsageTracker.get_instance()
        router = AdaptiveModelRouter(tracker)
    except Exception as e:
        print(f"\n❌ Could not initialize: {e}")
        print("Ensure Redis is running or use mock mode.")
        return

    # Get telemetry stats
    stats = tracker.get_stats(days=30)

    if stats["total_calls"] == 0:
        print("\n📊 No telemetry data found.")
        print("Run some workflows first to generate data:")
        print("  empathy workflow run code-review")
        print("  empathy workflow run bug-predict")
        return

    print(f"\n📊 Telemetry Data (Last 30 Days):")
    print(f"  Total calls: {stats['total_calls']:,}")
    print(f"  Total cost: ${stats['total_cost']:.2f}")
    print(f"  Cache hit rate: {stats['cache_hit_rate']:.1f}%")

    print(f"\n💰 Current Cost Distribution:")
    for tier, cost in sorted(stats["by_tier"].items(), key=lambda x: x[1], reverse=True):
        pct = (cost / stats["total_cost"] * 100) if stats["total_cost"] > 0 else 0
        print(f"  {tier:8s}: ${cost:6.2f} ({pct:5.1f}%)")

    # Analyze workflows for potential savings
    print(f"\n🔍 Analyzing Workflow Efficiency...")
    print("-" * 70)

    workflows = list(stats["by_workflow"].keys())
    total_potential_savings = 0.0
    recommendations = []

    for workflow_name in workflows[:10]:  # Top 10 workflows
        try:
            wf_stats = router.get_routing_stats(workflow_name, days=30)

            if wf_stats["total_calls"] < 10:
                continue  # Not enough data

            current_cost = wf_stats["avg_cost"]
            total_cost = wf_stats["total_calls"] * current_cost

            # Estimate if 50% could use cheaper models
            if current_cost > 0.002:  # More expensive than Haiku
                haiku_cost = 0.0016
                potential_per_call = (current_cost - haiku_cost) * 0.5
                potential_total = potential_per_call * wf_stats["total_calls"]

                if potential_total > 0.5:  # Only significant savings
                    total_potential_savings += potential_total
                    recommendations.append(
                        {
                            "workflow": workflow_name,
                            "calls": wf_stats["total_calls"],
                            "current_cost": current_cost,
                            "potential_savings": potential_total,
                        }
                    )

        except Exception:
            continue

    # Show recommendations
    if recommendations:
        print(f"\n💡 Top Opportunities for Adaptive Routing:\n")

        recommendations.sort(key=lambda x: x["potential_savings"], reverse=True)

        for i, rec in enumerate(recommendations[:5], 1):
            print(
                f"{i}. {rec['workflow']}: ${rec['potential_savings']:.2f} potential savings"
            )
            print(
                f"   ({rec['calls']} calls @ ${rec['current_cost']:.4f} avg, "
                f"could use cheaper models)"
            )
            print()

        # Calculate annualized savings
        days_analyzed = 30
        annual_multiplier = 365 / days_analyzed
        annual_savings = total_potential_savings * annual_multiplier

        print("=" * 70)
        print("💰 SAVINGS POTENTIAL")
        print("=" * 70)
        print(f"  Last 30 days: ${total_potential_savings:.2f}")
        print(f"  Annualized: ${annual_savings:.2f}")

        if annual_savings > 500:
            print(f"\n✅ RECOMMENDATION: Enable adaptive routing!")
            print(f"   Potential savings: ${annual_savings:.2f}/year")
            print(f"\n   How to enable:")
            print(f"   1. Add to workflow: enable_adaptive_routing=True")
            print(
                f"   2. Or set env var: export EMPATHY_ADAPTIVE_ROUTING=true"
            )
            print(
                f"   3. Or add to config: adaptive_routing.enabled = true"
            )
        else:
            print(f"\n📊 Current routing is fairly optimal.")
            print(f"   Adaptive routing would save ~${annual_savings:.2f}/year")
            print(f"   May not be worth enabling unless cost is a concern.")

    else:
        print("\n✅ Your workflows are already cost-optimized!")
        print("   Adaptive routing would provide minimal benefit.")

    print(f"\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    try:
        analyze_savings_potential()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
