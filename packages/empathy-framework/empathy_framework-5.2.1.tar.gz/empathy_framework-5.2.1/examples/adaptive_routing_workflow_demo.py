#!/usr/bin/env python3
"""Demonstration of Adaptive Routing integration with BaseWorkflow.

Shows how workflows automatically use adaptive routing for cost optimization
and quality improvement when enable_adaptive_routing=True.

Run this after you've accumulated telemetry data:
    python examples/adaptive_routing_workflow_demo.py

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from empathy_os.workflows.base import BaseWorkflow, ModelTier


class DemoWorkflow(BaseWorkflow):
    """Demo workflow that uses adaptive routing."""

    name = "demo-workflow"
    description = "Demonstrates adaptive routing integration"
    stages = ["classify", "analyze", "summarize"]

    # Static tier map (adaptive routing may override these)
    tier_map = {
        "classify": ModelTier.CHEAP,
        "analyze": ModelTier.CAPABLE,
        "summarize": ModelTier.CHEAP,
    }

    async def run_stage(self, stage_name: str, tier: ModelTier, input_data: dict):
        """Required abstract method - implement stage logic."""
        # Simulate stage execution (demo only)
        return {"stage": stage_name, "tier": tier.value}, 100, 50

    async def run(self, task: str) -> dict:
        """Run the demo workflow.

        This is a simple workflow that shows how adaptive routing works.
        """
        result = {"task": task, "stages": {}}

        print(f"\n📋 Task: {task}")
        print(f"🔄 Running {len(self.stages)} stages...")

        # Simulate stage execution
        for stage_name in self.stages:
            # Get tier (may be upgraded by adaptive routing)
            tier = self._get_tier_with_routing(
                stage_name=stage_name,
                input_data={"task": task},
                budget_remaining=1.0,
            )

            print(f"\n  Stage: {stage_name}")
            print(f"  Tier: {tier.value}")

            # Get adaptive router to show recommendations
            router = self._get_adaptive_router()
            if router:
                # Show routing stats for this workflow/stage
                try:
                    stats = router.get_routing_stats(
                        workflow=self.name, stage=stage_name, days=7
                    )

                    if stats["total_calls"] > 0:
                        print(
                            f"  Historical performance: {stats['total_calls']} calls, "
                            f"${stats['avg_cost']:.4f} avg cost, "
                            f"{stats['avg_success_rate']:.1%} success"
                        )

                        # Check for upgrade recommendation
                        should_upgrade, reason = router.recommend_tier_upgrade(
                            workflow=self.name, stage=stage_name
                        )

                        if should_upgrade:
                            print(f"  ⚠️  Upgrade recommended: {reason}")
                        else:
                            print(f"  ✅ {reason}")
                    else:
                        print(f"  No historical data (using default tier)")
                except Exception as e:
                    print(f"  No telemetry data available: {e}")

            result["stages"][stage_name] = {"tier": tier.value}

        return result


async def main():
    """Run the demo."""
    print("=" * 70)
    print("ADAPTIVE ROUTING WORKFLOW INTEGRATION DEMO")
    print("=" * 70)

    # Test 1: Without adaptive routing (static tier map)
    print("\n🧪 Test 1: WITHOUT Adaptive Routing (Static Tier Map)")
    print("-" * 70)

    workflow_static = DemoWorkflow(enable_adaptive_routing=False)
    result1 = await workflow_static.run("Analyze code quality")

    # Test 2: WITH adaptive routing (telemetry-driven)
    print("\n\n🧪 Test 2: WITH Adaptive Routing (Telemetry-Driven)")
    print("-" * 70)

    workflow_adaptive = DemoWorkflow(enable_adaptive_routing=True)
    result2 = await workflow_adaptive.run("Analyze code quality")

    # Summary
    print("\n\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    print("\n📊 Tier Comparison:")
    print(f"{'Stage':<15} {'Static Tier':<15} {'Adaptive Tier':<15} {'Change'}")
    print("-" * 60)

    for stage in workflow_static.stages:
        static_tier = result1["stages"][stage]["tier"]
        adaptive_tier = result2["stages"][stage]["tier"]

        if static_tier != adaptive_tier:
            change = f"⚠️  Upgraded"
        else:
            change = "✅ Same"

        print(f"{stage:<15} {static_tier:<15} {adaptive_tier:<15} {change}")

    print("\n💡 Key Insights:")
    print("  • Adaptive routing analyzes telemetry to detect high failure rates")
    print("  • Automatically upgrades tiers when failure rate > 20%")
    print("  • Works alongside existing routing_strategy if configured")
    print("  • Opt-in feature: set enable_adaptive_routing=True")

    print("\n✅ Demo complete!")


if __name__ == "__main__":
    import asyncio

    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
