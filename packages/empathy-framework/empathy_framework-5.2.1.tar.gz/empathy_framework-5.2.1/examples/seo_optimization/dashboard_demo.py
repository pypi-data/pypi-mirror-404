"""SEO Optimization with Dashboard Integration.

This script demonstrates how to run the SEO workflow with the Agent Coordination
Dashboard so you can see real-time agent activity.

Setup:
1. Terminal 1: python examples/dashboard_demo.py (start dashboard)
2. Terminal 2: python examples/seo_optimization/dashboard_demo.py (run this)
3. Open browser to http://localhost:8000
"""

import asyncio
from pathlib import Path

from empathy_os.coordination import InMemoryHeartbeatBackend
from empathy_os.workflows import SEOOptimizationWorkflow


async def main():
    """Run SEO workflow with dashboard integration."""
    print("=" * 70)
    print("SEO Optimization with Dashboard Integration")
    print("=" * 70)
    print()
    print("📊 Setting up in-memory backend for dashboard tracking...")

    # Initialize in-memory backend for heartbeat tracking
    backend = InMemoryHeartbeatBackend()

    print("✅ Backend initialized")
    print()
    print("🚀 Starting SEO workflow...")
    print()
    print("👉 Open the dashboard at http://localhost:8000 to see:")
    print("   • Agent card: 'seo-optimization-[run-id]'")
    print("   • Real-time heartbeat updates")
    print("   • Stage progress: scan → analyze → recommend → implement")
    print("   • Live cost tracking")
    print()

    # Run workflow
    workflow = SEOOptimizationWorkflow()
    result = await workflow.execute(
        docs_path=Path("../../docs"),
        site_url="https://smartaimemory.com",
        mode="audit",
        interactive=False,
    )

    print()
    print("=" * 70)
    print("✅ Workflow Complete")
    print("=" * 70)
    print()

    if result.success:
        # Get results from stages
        scan_data = None
        analyze_data = None

        for stage in result.stages:
            if stage.name == "scan":
                scan_data = stage.result if isinstance(stage.result, dict) else {}
            elif stage.name == "analyze":
                analyze_data = stage.result if isinstance(stage.result, dict) else {}

        print(f"📁 Files scanned: {scan_data.get('file_count', 0) if scan_data else 0}")
        print(f"⚠️  Issues found: {analyze_data.get('total_issues', 0) if analyze_data else 0}")
        print(f"💰 Cost: ${result.cost_report.total_cost:.4f}")
        print(f"💾 Savings: {result.cost_report.savings_percent:.1f}%")
        print()
        print("🎯 Check the dashboard to see the agent activity!")
    else:
        print(f"❌ Error: {result.error}")

    print()
    print("💡 To see this in the dashboard:")
    print("   1. Keep this script running")
    print("   2. In another terminal: python examples/dashboard_demo.py")
    print("   3. Open http://localhost:8000")
    print()


if __name__ == "__main__":
    asyncio.run(main())
