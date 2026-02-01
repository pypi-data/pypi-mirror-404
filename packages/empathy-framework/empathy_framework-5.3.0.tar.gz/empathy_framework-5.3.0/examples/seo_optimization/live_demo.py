"""Live demo showing SEO workflow in Agent Coordination Dashboard.

Run this alongside the dashboard to see agents coordinating in real-time.

Usage:
    # Terminal 1: Start the dashboard
    python examples/dashboard_demo.py

    # Terminal 2: Run this script
    python examples/seo_optimization/live_demo.py
"""

import asyncio
from pathlib import Path

from empathy_os.workflows import SEOOptimizationWorkflow


async def main():
    """Run SEO optimization workflow with dashboard visibility."""
    print("=" * 70)
    print("SEO Optimization - Live Agent Coordination Demo")
    print("=" * 70)
    print("\n📊 Open the Agent Coordination Dashboard in your browser:")
    print("   http://localhost:8000")
    print("\n💡 You should see the seo-optimization agent appear shortly...")
    print("\nStarting in 5 seconds...")
    await asyncio.sleep(5)

    # Initialize workflow with coordination enabled
    workflow = SEOOptimizationWorkflow()

    print("\n🚀 Running SEO audit on Empathy Framework documentation...")
    print("   Watch the dashboard to see:")
    print("   - Agent heartbeat updates")
    print("   - Stage progression (scan → analyze)")
    print("   - Cost accumulation\n")

    # Run the workflow
    result = await workflow.execute(
        docs_path=Path("../../docs"),
        site_url="https://smartaimemory.com",
        mode="audit",
    )

    print("\n" + "=" * 70)
    print("Results:")
    print("=" * 70)

    if result.success:
        # Extract results from stages
        for stage in result.stages:
            if stage.name == "scan" and not stage.skipped:
                scan_output = stage.result if isinstance(stage.result, dict) else {}
                files_scanned = scan_output.get("file_count", 0)
                print(f"📁 Files scanned: {files_scanned}")

            elif stage.name == "analyze" and not stage.skipped:
                analyze_output = stage.result if isinstance(stage.result, dict) else {}
                issues_found = analyze_output.get("total_issues", 0)
                print(f"⚠️  SEO issues found: {issues_found}")

        print(f"\n💰 Total cost: ${result.cost_report.total_cost:.4f}")
        print(f"💾 Savings: {result.cost_report.savings_percent:.1f}%")

        print(f"\n⏱️  Execution time: {result.total_duration_ms / 1000:.2f}s")
        print(f"🎯 Provider: {result.provider}")

    else:
        print(f"❌ Error: {result.error}")

    print("\n" + "=" * 70)
    print("✅ Demo complete!")
    print("=" * 70)
    print("\n💡 The agent should now appear as 'completed' in the dashboard.")
    print("   Check the coordination patterns and heartbeat history.\n")


if __name__ == "__main__":
    asyncio.run(main())
