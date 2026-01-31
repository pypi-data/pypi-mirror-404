"""Demo: Memory-Enhanced Meta-Workflow Pattern Learning

This demonstrates the hybrid storage architecture where execution results
are stored in both:
1. File system: Persistent, human-readable JSON/text files
2. Memory system: Rich semantic queries and relationship modeling

The memory integration enables:
- Natural language searches ("find successful workflows with high test coverage")
- Context-aware recommendations based on similar past executions
- Semantic relationship modeling across workflow runs

Run: python demo_memory_integration.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from empathy_os.memory.unified import UnifiedMemory
from empathy_os.meta_workflows import FormResponse, MetaWorkflow, PatternLearner, TemplateRegistry


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_hybrid_storage():
    """Demo 1: Hybrid Storage Architecture."""
    print_section("DEMO 1: Hybrid Storage - File + Memory")

    # Initialize memory system
    print("\n📦 Initializing memory system...")
    memory = UnifiedMemory(
        user_id="meta_workflow_demo",
        # Will use mock Redis for short-term, file storage for long-term
    )

    # Check backend status
    status = memory.get_backend_status()
    print(f"   Environment: {status['environment']}")
    print(f"   Short-term: {'✅' if status['short_term']['available'] else '❌'}")
    print(f"   Long-term: {'✅' if status['long_term']['available'] else '❌'}")

    # Initialize pattern learner with memory
    print("\n🧠 Initializing pattern learner with memory...")
    learner = PatternLearner(memory=memory)

    # Load template (using built-in release-prep template)
    registry = TemplateRegistry(storage_dir=".empathy/meta_workflows/templates")
    template = registry.load_template("release-prep")  # Built-in template

    # Create workflow with pattern learner
    print("\n🤖 Creating meta-workflow with memory integration...")
    workflow = MetaWorkflow(
        template=template,
        pattern_learner=learner,  # This enables memory storage
    )

    # Execute multiple workflows with different configurations
    print("\n▶️  Executing 3 workflows with different configurations...\n")

    configs = [
        {
            "name": "Minimal Quality",
            "responses": {
                "security_scan": "No",
                "test_coverage_check": "No",
                "quality_review": "No",
                "doc_verification": "No",
            },
        },
        {
            "name": "Medium Quality",
            "responses": {
                "security_scan": "Yes",
                "test_coverage_check": "Yes",
                "coverage_threshold": "80%",
                "quality_review": "No",
                "doc_verification": "No",
            },
        },
        {
            "name": "High Quality",
            "responses": {
                "security_scan": "Yes",
                "test_coverage_check": "Yes",
                "coverage_threshold": "90%",
                "quality_review": "Yes",
                "doc_verification": "Yes",
            },
        },
    ]

    results = []
    for config in configs:
        print(f"   Executing: {config['name']}...")

        response = FormResponse(
            template_id="release-prep",
            responses=config["responses"],
        )

        result = workflow.execute(form_response=response, mock_execution=True)
        results.append(result)

        print(f"      ✓ {result.run_id}")
        print(f"        Agents: {len(result.agents_created)}")
        print(f"        Cost: ${result.total_cost:.2f}")
        print(f"        Storage: File ✅ | Memory {'✅' if learner.memory else '❌'}\n")

    return learner, results


def demo_memory_queries(learner: PatternLearner):
    """Demo 2: Memory-Enhanced Querying."""
    print_section("DEMO 2: Memory-Enhanced Semantic Queries")

    if not learner.memory:
        print("\n   ⚠️  Memory not available - skipping memory queries")
        return

    # Example 1: Search by natural language query
    print("\n🔍 Example 1: Natural language search")
    print('   Query: "successful workflows"')

    successful = learner.search_executions_by_context(
        query="successful workflows",
        limit=5,
    )

    print(f"\n   Found {len(successful)} results:")
    for result in successful:
        print(f"      • {result.run_id}")
        print(f"        Success: {'✅' if result.success else '❌'}")
        print(f"        Agents: {len(result.agents_created)}")

    # Example 2: Search with specific criteria
    print("\n🔍 Example 2: Context-specific search")
    print('   Query: "workflows with high test coverage"')

    high_coverage = learner.search_executions_by_context(
        query="workflows with test coverage 90%",
        template_id="python_package_publish",
        limit=3,
    )

    print(f"\n   Found {len(high_coverage)} results:")
    for result in high_coverage:
        coverage = result.form_responses.responses.get("test_coverage_required", "N/A")
        print(f"      • {result.run_id}")
        print(f"        Coverage: {coverage}")
        print(f"        Cost: ${result.total_cost:.2f}")


def demo_smart_recommendations(learner: PatternLearner):
    """Demo 3: Memory-Enhanced Recommendations."""
    print_section("DEMO 3: Smart Recommendations (Memory-Enhanced)")

    # Create a new form response to get recommendations for
    new_response = FormResponse(
        template_id="python_package_publish",
        responses={
            "has_tests": "Yes",
            "test_coverage_required": "85%",
            "quality_checks": ["Linting (ruff)", "Type checking (mypy)"],
            "version_bump": "minor",
        },
    )

    print("\n📋 Getting recommendations for new configuration:")
    print("   - has_tests: Yes")
    print("   - test_coverage_required: 85%")
    print("   - quality_checks: Linting + Type checking")
    print("   - version_bump: minor")

    # Get memory-enhanced recommendations
    print("\n💡 Smart Recommendations (combining stats + memory):\n")

    recommendations = learner.get_smart_recommendations(
        template_id="python_package_publish",
        form_response=new_response,
        min_confidence=0.5,
    )

    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    else:
        print("   (No recommendations available yet - need more execution data)")

    # Compare with base recommendations (no memory)
    print("\n📊 Base Recommendations (stats only):\n")

    base_recommendations = learner.get_recommendations(
        template_id="python_package_publish",
        min_confidence=0.5,
    )

    if base_recommendations:
        for i, rec in enumerate(base_recommendations, 1):
            print(f"   {i}. {rec}")
    else:
        print("   (No statistical patterns yet - need more data)")


def demo_file_vs_memory():
    """Demo 4: Comparison of File vs Memory Storage."""
    print_section("DEMO 4: File Storage vs Memory Storage")

    print("\n📁 File-Based Storage:")
    print("   ✅ Persistent across sessions")
    print("   ✅ Human-readable (JSON, text reports)")
    print("   ✅ Easy backup/export")
    print("   ✅ Simple debugging")
    print("   ❌ Slower queries")
    print("   ❌ Limited semantic search")
    print("   ❌ No relationship modeling")

    print("\n🧠 Memory-Based Storage (Long-Term):")
    print("   ✅ Rich semantic queries")
    print("   ✅ Relationship modeling")
    print("   ✅ Context-aware recommendations")
    print("   ✅ Cross-workflow pattern recognition")
    print("   ✅ Natural language queries")
    print("   ❌ Requires memory system setup")

    print("\n🔄 Hybrid Architecture (Best of Both):")
    print("   ✅ Files for persistence")
    print("   ✅ Memory for intelligence")
    print("   ✅ Automatic synchronization")
    print("   ✅ Graceful fallback (memory optional)")
    print("   ✅ No data loss if memory unavailable")


def demo_analytics_report(learner: PatternLearner):
    """Demo 5: Analytics Report with Memory Insights."""
    print_section("DEMO 5: Comprehensive Analytics Report")

    print("\n📊 Generating analytics report...\n")

    report = learner.generate_analytics_report(template_id="python_package_publish")

    # Print summary
    summary = report["summary"]
    print("## Summary")
    print(f"\n   Total Runs: {summary['total_runs']}")
    print(f"   Successful: {summary['successful_runs']} ({summary['success_rate']:.0%})")
    print(f"   Total Cost: ${summary['total_cost']:.2f}")
    print(f"   Avg Cost/Run: ${summary['avg_cost_per_run']:.2f}")
    print(f"   Total Agents: {summary['total_agents_created']}")
    print(f"   Avg Agents/Run: {summary['avg_agents_per_run']:.1f}")

    # Print insights
    insights = report.get("insights", {})

    if insights.get("tier_performance"):
        print("\n## Tier Performance Insights")
        for insight in insights["tier_performance"][:3]:  # Top 3
            print(f"\n   • {insight['description']}")
            print(f"     Confidence: {insight['confidence']:.0%}")

    if insights.get("cost_analysis"):
        print("\n## Cost Analysis")
        for insight in insights["cost_analysis"]:
            print(f"\n   • {insight['description']}")

    # Print recommendations
    if report.get("recommendations"):
        print("\n## Recommendations")
        for rec in report["recommendations"]:
            print(f"\n   {rec}")


def main():
    """Run all demos."""
    print("\n" + "█" * 70)
    print("█" + " " * 68 + "█")
    print("█" + "  MEMORY-ENHANCED META-WORKFLOW SYSTEM".center(68) + "█")
    print("█" + "  Hybrid Storage: Files + Memory".center(68) + "█")
    print("█" + " " * 68 + "█")
    print("█" * 70)

    try:
        # Demo 1: Execute workflows with hybrid storage
        learner, results = demo_hybrid_storage()

        # Demo 2: Memory-enhanced queries
        demo_memory_queries(learner)

        # Demo 3: Smart recommendations
        demo_smart_recommendations(learner)

        # Demo 4: File vs Memory comparison
        demo_file_vs_memory()

        # Demo 5: Analytics report
        demo_analytics_report(learner)

        # Final summary
        print_section("DEMO COMPLETE")
        print("\n✅ All demos executed successfully!")
        print("\n📌 Key Takeaways:")
        print("   1. Hybrid storage provides best of both worlds")
        print("   2. Files ensure persistence, memory enables intelligence")
        print("   3. Memory integration is optional - graceful fallback")
        print("   4. Smart recommendations leverage historical patterns")
        print("   5. Semantic queries enable natural language search")
        print("\n🚀 Meta-workflow system with memory integration working!\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
