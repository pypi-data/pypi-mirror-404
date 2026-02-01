"""Complete SEO Optimization Demo

Demonstrates:
1. Detailed SEO audit results
2. Socratic questioning flow
3. Dashboard integration setup

Usage:
    python examples/seo_optimization/complete_demo.py
"""

import asyncio
from pathlib import Path
from typing import Any

from empathy_os.workflows import SEOOptimizationWorkflow


def print_section(title: str, char: str = "="):
    """Print a formatted section header."""
    print(f"\n{char * 70}")
    print(f"{title.center(70)}")
    print(f"{char * 70}\n")


def print_seo_results_detailed(result: Any):
    """Print detailed SEO audit results in a user-friendly format."""
    print_section("📊 DETAILED SEO AUDIT RESULTS", "=")

    if not result.success:
        print(f"❌ Error: {result.error}\n")
        return

    # Extract results from stages
    scan_data = None
    analysis_data = None

    for stage in result.stages:
        if stage.name == "scan" and not stage.skipped:
            scan_data = stage.result if isinstance(stage.result, dict) else {}
        elif stage.name == "analyze" and not stage.skipped:
            analysis_data = stage.result if isinstance(stage.result, dict) else {}

    # 1. Summary Statistics
    print("📈 Summary")
    print("-" * 70)
    if scan_data:
        print(f"   📁 Files scanned: {scan_data.get('file_count', 0)}")
        print(f"   🌐 Site URL: {scan_data.get('site_url', 'N/A')}")

    if analysis_data:
        total_issues = analysis_data.get('total_issues', 0)
        files_analyzed = analysis_data.get('files_analyzed', 0)
        print(f"   ⚠️  Total SEO issues: {total_issues}")
        print(f"   📊 Files analyzed: {files_analyzed}")

        if files_analyzed > 0:
            avg_issues = total_issues / files_analyzed
            print(f"   📉 Average issues per file: {avg_issues:.1f}")

    print(f"\n   💰 Cost: ${result.cost_report.total_cost:.4f}")
    print(f"   💾 Savings: {result.cost_report.savings_percent:.1f}%")
    print(f"   ⏱️  Duration: {result.total_duration_ms / 1000:.2f}s")

    # 2. Issues Breakdown by Type
    if analysis_data and 'issues' in analysis_data:
        issues = analysis_data['issues']

        print(f"\n📋 Issues by Type")
        print("-" * 70)

        # Group by element type
        issues_by_type: dict[str, list] = {}
        for issue in issues:
            element = issue.get('element', 'unknown')
            if element not in issues_by_type:
                issues_by_type[element] = []
            issues_by_type[element].append(issue)

        for element, element_issues in sorted(issues_by_type.items()):
            count = len(element_issues)
            severity = element_issues[0].get('severity', 'unknown')

            # Emoji by severity
            emoji = "🔴" if severity == "critical" else "🟡" if severity == "warning" else "🔵"

            print(f"   {emoji} {element.replace('_', ' ').title()}: {count} files")

        # 3. Sample Issues (first 5)
        print(f"\n🔍 Sample Issues (showing first 5 of {len(issues)})")
        print("-" * 70)

        for i, issue in enumerate(issues[:5], 1):
            file_name = Path(issue['file']).name
            element = issue.get('element', 'unknown').replace('_', ' ').title()
            message = issue.get('message', 'No description')
            severity = issue.get('severity', 'unknown')

            print(f"   {i}. [{severity.upper()}] {file_name}")
            print(f"      Issue: {element}")
            print(f"      {message}\n")

    # 4. Cost Breakdown
    print(f"💸 Cost Breakdown by Stage")
    print("-" * 70)
    for stage_name, cost in result.cost_report.by_stage.items():
        print(f"   {stage_name:15} ${cost:.4f}")

    print(f"\n   Total:          ${result.cost_report.total_cost:.4f}")
    print(f"   Baseline:       ${result.cost_report.baseline_cost:.4f}")
    print(f"   Savings:        ${result.cost_report.savings:.4f} ({result.cost_report.savings_percent:.1f}%)")


async def demonstrate_socratic_flow():
    """Demonstrate the Socratic questioning flow."""
    print_section("🎓 SOCRATIC QUESTIONING DEMONSTRATION", "=")

    print("The SEO workflow uses Socratic questioning to guide users through")
    print("optimization decisions. Here's how it works:\n")

    # 1. Initial Discovery
    print("1️⃣  INITIAL DISCOVERY QUESTION")
    print("-" * 70)
    print("\nQuestion: What's most important to you right now with your documentation SEO?")
    print("\nOptions:")
    print("   🚀 Launch preparation")
    print("      Getting the site ready for public release - comprehensive coverage")
    print("\n   🔍 Search visibility")
    print("      Improving rankings for specific keywords - focus on high-impact changes")
    print("\n   ✅ Health check (Recommended)")
    print("      Regular maintenance and catching issues - balanced approach")
    print("\n   🎯 Specific issue")
    print("      You've noticed something that needs fixing - targeted investigation")

    print("\n💡 User selects: 'Health check'\n")

    # 2. Confidence-Based Branching
    print("\n2️⃣  CONFIDENCE-BASED RECOMMENDATIONS")
    print("-" * 70)
    print("\nAfter analysis, the workflow calculates confidence scores for each recommendation:\n")

    print("   HIGH CONFIDENCE (≥80%) → Proceed with recommendation")
    print("   ✓ Missing meta descriptions (60% confidence)")
    print("     Impact: High - directly affects search rankings")
    print("     Time: 2-3 minutes per page")
    print("     Why: Search engines display this in results")
    print()

    print("   LOW CONFIDENCE (<80%) → Ask clarifying question")
    print("   ? Heading structure (65% confidence)")
    print("     Question: Should I prioritize SEO optimization or preserve")
    print("               your current content organization?")
    print()

    # 3. Educational Explanations
    print("\n3️⃣  EDUCATIONAL EXPLANATIONS")
    print("-" * 70)
    print("\nEvery recommendation includes:")
    print("   • Impact: How it affects your SEO")
    print("   • Time: Realistic estimate")
    print("   • Why: Educational context about the issue")
    print("   • Confidence: Percentage confidence in the fix\n")

    print("Example:")
    print("   Issue: Missing meta description in README.md")
    print("   Impact: High - directly affects search rankings")
    print("   Time: 2-3 minutes")
    print("   Why: Search engines display this in results. A compelling")
    print("        description improves click-through rate by 20-30%.")
    print("   Confidence: 60% confident")

    # 4. Batch Operations
    print("\n4️⃣  BATCH OPERATION DETECTION")
    print("-" * 70)
    print("\nWhen the workflow detects repetitive work:\n")

    print("Question: You have 12 pages without descriptions. Should I:")
    print("\n   Options:")
    print("   📝 Continue asking for each one")
    print("      Ensures accuracy - I'll show you each one")
    print("\n   🤖 Auto-generate all of them (Recommended)")
    print("      Faster - I'll use the same approach, you review after")
    print("\n   📊 Batch approve")
    print("      Show me 5 at once, approve/reject in bulk")

    print("\n💡 User selects: 'Auto-generate all of them'")

    # 5. Interactive Approval
    print("\n5️⃣  INTERACTIVE APPROVAL (Fix Mode)")
    print("-" * 70)
    print("\nIn fix mode, the workflow shows before/after previews:\n")

    print("   File: installation.md")
    print("   ─────────────────────────────")
    print("   BEFORE:")
    print("   # Installation")
    print("   Steps to install the framework...")
    print()
    print("   AFTER:")
    print("   ---")
    print("   description: Learn how to install Empathy Framework with pip,")
    print("                configure Redis, and verify your setup in under 5 minutes.")
    print("   ---")
    print("   # Installation")
    print("   Steps to install the framework...")
    print()
    print("   ✓ Apply this change? [Yes / No / Edit]")


async def demonstrate_dashboard_setup():
    """Demonstrate dashboard setup for agent tracking."""
    print_section("📊 DASHBOARD INTEGRATION SETUP", "=")

    print("To see SEO agents in the Agent Coordination Dashboard:\n")

    print("OPTION 1: In-Memory Backend (Testing)")
    print("-" * 70)
    print("Quick setup for local testing:\n")
    print("```python")
    print("# In your dashboard startup (examples/dashboard_demo.py)")
    print("from empathy_os.coordination import InMemoryHeartbeatBackend")
    print()
    print("# Initialize backend")
    print("backend = InMemoryHeartbeatBackend()")
    print()
    print("# Workflow automatically uses this backend")
    print("workflow = SEOOptimizationWorkflow()  # Already configured!")
    print("```\n")

    print("OPTION 2: Redis Backend (Production)")
    print("-" * 70)
    print("For production use with persistence:\n")
    print("```bash")
    print("# Terminal 1: Start Redis")
    print("redis-server")
    print()
    print("# Terminal 2: Start Dashboard")
    print("python examples/dashboard_demo.py")
    print()
    print("# Terminal 3: Run SEO Workflow")
    print("python examples/seo_optimization/live_demo.py")
    print("```\n")

    print("What You'll See in Dashboard:")
    print("-" * 70)
    print("  • Agent Card: 'seo-optimization-[run-id]'")
    print("  • Heartbeat Updates: Real-time status as it processes")
    print("  • Stage Progress: scan → analyze → recommend → implement")
    print("  • Cost Tracking: Live cost accumulation")
    print("  • Coordination Status: Heartbeat patterns (Pattern 1)\n")

    print("Current Status:")
    print("-" * 70)
    print("  ✅ SEO workflow configured with heartbeat tracking")
    print("  ⚠️  Memory backend needs Redis or in-memory setup")
    print("  💡 Workflow works perfectly without dashboard - tracking is optional\n")


async def main():
    """Run complete SEO optimization demonstration."""
    print_section("🎯 COMPLETE SEO OPTIMIZATION DEMONSTRATION", "█")

    print("This demonstration covers:")
    print("  1. Detailed SEO audit results with actionable insights")
    print("  2. Socratic questioning flow for user guidance")
    print("  3. Dashboard integration setup (optional)\n")

    print("Starting demonstration...\n")

    # Part 1: Run SEO Audit and Show Detailed Results
    print_section("PART 1: SEO AUDIT WITH DETAILED RESULTS", "=")

    print("Running SEO audit on Empathy Framework documentation...\n")

    workflow = SEOOptimizationWorkflow()
    result = await workflow.execute(
        docs_path=Path("../../docs"),
        site_url="https://smartaimemory.com",
        mode="audit",
        interactive=False,  # Non-interactive for demo
    )

    print_seo_results_detailed(result)

    print("\n\n")

    # Part 2: Demonstrate Socratic Flow
    await demonstrate_socratic_flow()

    print("\n\n")

    # Part 3: Dashboard Setup
    await demonstrate_dashboard_setup()

    # Summary
    print_section("✅ DEMONSTRATION COMPLETE", "=")

    print("What You Learned:")
    print("  ✓ How the SEO workflow audits your documentation")
    print("  ✓ How Socratic questioning guides decision-making")
    print("  ✓ How to set up dashboard tracking (optional)")
    print()
    print("Next Steps:")
    print("  • Run: /docs seo-audit (for quick audit)")
    print("  • Run: /docs seo-optimize (for interactive fixes)")
    print("  • Run: /workflows run seo-optimization --mode suggest (for recommendations)")
    print()
    print("Documentation:")
    print("  • User Experience: examples/seo_optimization/SOCRATIC_DEMO.md")
    print("  • Agent Spec: agents_md/seo-optimizer.md")
    print("  • Integration: See .claude/commands/docs.md")
    print()


if __name__ == "__main__":
    asyncio.run(main())
