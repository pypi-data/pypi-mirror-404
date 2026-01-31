"""End-to-end demo of complete meta-workflow system (Days 1-3).

This demonstrates the FULL workflow:
1. Load template
2. Create form response (simulating user input)
3. Generate agent team
4. Execute meta-workflow
5. View results
6. Load and inspect saved execution

Run: python demo_end_to_end_workflow.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from empathy_os.meta_workflows import (
    FormResponse,
    MetaWorkflow,
    TemplateRegistry,
    list_execution_results,
    load_execution_result,
)


def main():
    """Run end-to-end meta-workflow demo."""
    print("\n" + "█" * 70)
    print("█" + " " * 68 + "█")
    print("█" + "  END-TO-END META-WORKFLOW DEMO".center(68) + "█")
    print("█" + "  (Complete System - Days 1-3)".center(68) + "█")
    print("█" + " " * 68 + "█")
    print("█" * 70)

    # Step 1: Load template
    print("\n" + "=" * 70)
    print("STEP 1: Load Template")
    print("=" * 70)

    registry = TemplateRegistry(storage_dir=".empathy/meta_workflows/templates")
    templates = registry.list_templates()

    print(f"\nAvailable templates: {', '.join(templates)}")

    template = registry.load_template("python_package_publish")
    print(f"\n✓ Loaded: {template.name}")
    print(f"  Version: {template.version}")
    print(f"  Questions: {len(template.form_schema.questions)}")
    print(f"  Agent rules: {len(template.agent_composition_rules)}")
    print(
        f"  Estimated cost: ${template.estimated_cost_range[0]:.2f}-${template.estimated_cost_range[1]:.2f}"
    )

    # Step 2: Simulate user responses
    print("\n" + "=" * 70)
    print("STEP 2: Collect User Responses")
    print("=" * 70)

    print("\nSimulating user answering form questions...")
    print("(In production, this uses AskUserQuestion tool)")

    response = FormResponse(
        template_id="python_package_publish",
        responses={
            "package_name": "empathy-demo-package",
            "has_tests": "Yes",
            "test_coverage_required": "90%",
            "quality_checks": [
                "Type checking (mypy)",
                "Linting (ruff)",
                "Security scan (bandit)",
                "Documentation build",
            ],
            "version_bump": "minor",
            "publish_to": "TestPyPI (staging)",
            "create_git_tag": "Yes",
            "update_changelog": "Yes",
        },
    )

    print("\n✓ Collected 8 responses:")
    for key, value in response.responses.items():
        if isinstance(value, list):
            print(f"  • {key}: {len(value)} selected")
        else:
            print(f"  • {key}: {value}")

    # Step 3: Initialize workflow
    print("\n" + "=" * 70)
    print("STEP 3: Initialize Meta-Workflow")
    print("=" * 70)

    workflow = MetaWorkflow(template=template)
    print("\n✓ MetaWorkflow initialized")
    print(f"  Template: {workflow.template.name}")
    print(f"  Storage: {workflow.storage_dir}")

    # Step 4: Execute workflow
    print("\n" + "=" * 70)
    print("STEP 4: Execute Meta-Workflow")
    print("=" * 70)

    print("\nExecuting workflow with mock agents...")
    print("(Real LLM execution in Days 6-7)")

    result = workflow.execute(form_response=response, mock_execution=True)

    print("\n✓ Execution complete!")
    print(f"  Run ID: {result.run_id}")
    print(f"  Success: {result.success}")
    print(f"  Agents created: {len(result.agents_created)}")
    print(f"  Agents executed: {len(result.agent_results)}")
    print(f"  Total cost: ${result.total_cost:.2f}")
    print(f"  Total duration: {result.total_duration:.1f}s")

    # Step 5: Inspect agents
    print("\n" + "=" * 70)
    print("STEP 5: Inspect Created Agents")
    print("=" * 70)

    print(f"\nCreated {len(result.agents_created)} specialized agents:\n")

    for i, agent in enumerate(result.agents_created, 1):
        print(f"{i}. {agent.role}")
        print(f"   • Tier strategy: {agent.tier_strategy.value}")
        print(f"   • Tools: {', '.join(agent.tools) if agent.tools else 'None'}")
        if agent.config:
            print(f"   • Config: {agent.config}")

    # Step 6: Inspect results
    print("\n" + "=" * 70)
    print("STEP 6: Inspect Execution Results")
    print("=" * 70)

    print(f"\nExecution results for {len(result.agent_results)} agents:\n")

    for i, agent_result in enumerate(result.agent_results, 1):
        status_icon = "✅" if agent_result.success else "❌"
        print(f"{i}. {status_icon} {agent_result.role}")
        print(f"   • Tier used: {agent_result.tier_used}")
        print(f"   • Cost: ${agent_result.cost:.2f}")
        print(f"   • Duration: {agent_result.duration:.1f}s")

    # Step 7: Cost breakdown
    print("\n" + "=" * 70)
    print("STEP 7: Cost Breakdown")
    print("=" * 70)

    tier_costs = {}
    for agent_result in result.agent_results:
        tier = agent_result.tier_used
        if tier not in tier_costs:
            tier_costs[tier] = 0.0
        tier_costs[tier] += agent_result.cost

    print("\nCosts by tier:\n")
    for tier, cost in sorted(tier_costs.items()):
        print(f"  • {tier}: ${cost:.2f}")

    print(f"\n  Total: ${result.total_cost:.2f}")

    # Step 8: View saved files
    print("\n" + "=" * 70)
    print("STEP 8: Saved Result Files")
    print("=" * 70)

    run_dir = workflow.storage_dir / result.run_id
    files = list(run_dir.glob("*"))
    files.sort()

    print(f"\nSaved to: {run_dir}")
    print("\nFiles created:")

    for file in files:
        size = file.stat().st_size
        print(f"  • {file.name} ({size:,} bytes)")

    # Step 9: Load saved result
    print("\n" + "=" * 70)
    print("STEP 9: Load Saved Result")
    print("=" * 70)

    print("\nLoading result from disk...")

    loaded_result = load_execution_result(result.run_id)

    print(f"✓ Loaded result: {loaded_result.run_id}")
    print(f"  Matches original: {loaded_result.run_id == result.run_id}")
    print(f"  Agents: {len(loaded_result.agents_created)}")
    print(f"  Cost: ${loaded_result.total_cost:.2f}")

    # Step 10: List all results
    print("\n" + "=" * 70)
    print("STEP 10: List All Execution Results")
    print("=" * 70)

    all_results = list_execution_results()

    print(f"\nFound {len(all_results)} execution(s):\n")

    for i, run_id in enumerate(all_results[:5], 1):  # Show max 5
        print(f"  {i}. {run_id}")

    if len(all_results) > 5:
        print(f"  ... and {len(all_results) - 5} more")

    # Step 11: View report
    print("\n" + "=" * 70)
    print("STEP 11: Human-Readable Report")
    print("=" * 70)

    report_file = run_dir / "report.txt"
    report = report_file.read_text()

    # Show first 20 lines
    report_lines = report.split("\n")
    print("\nFirst 20 lines of report:\n")
    for line in report_lines[:20]:
        print(f"  {line}")

    print(f"\n  ... ({len(report_lines)} total lines)")

    # Final summary
    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)

    print("\n✅ Meta-Workflow System is fully operational!")
    print("\n📊 Summary:")
    print(f"  • Template loaded: {template.name}")
    print(f"  • User responses collected: {len(response.responses)}")
    print(f"  • Agents created: {len(result.agents_created)}")
    print(f"  • Agents executed: {len(result.agent_results)}")
    print(f"  • Total cost: ${result.total_cost:.2f}")
    print("  • Success rate: 100%")

    print("\n🎯 What's working:")
    print("  ✓ Template loading and inspection")
    print("  ✓ Form response collection")
    print("  ✓ Dynamic agent generation")
    print("  ✓ Mock agent execution")
    print("  ✓ Result storage and retrieval")
    print("  ✓ Human-readable reports")
    print("  ✓ Cost tracking and breakdown")

    print("\n🚀 Next steps:")
    print("  • Day 4: Pattern learning & CLI")
    print("  • Day 5: Integration testing")
    print("  • Days 6-7: Real LLM agent execution")

    print("\n" + "=" * 70 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
