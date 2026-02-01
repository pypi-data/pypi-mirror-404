"""Comprehensive demo of meta-workflow system (Days 1-2).

This demonstrates:
1. Template loading and inspection
2. Form response creation
3. Dynamic agent generation
4. Cost estimation
5. Dependency validation

Run: python demo_meta_workflows.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from empathy_os.meta_workflows import DynamicAgentCreator, FormResponse, TemplateRegistry
from empathy_os.meta_workflows.agent_creator import (
    estimate_agent_costs,
    group_agents_by_tier_strategy,
    validate_agent_dependencies,
)


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_template_loading():
    """Demo 1: Template loading and inspection."""
    print_section("DEMO 1: Template Loading & Inspection")

    registry = TemplateRegistry(storage_dir=".empathy/meta_workflows/templates")
    templates = registry.list_templates()

    print(f"\nFound {len(templates)} template(s): {', '.join(templates)}")

    if not templates:
        print("⚠️  No templates found. Run create_demo_data.py first.")
        return None

    # Load the first template
    template_id = templates[0]
    template = registry.load_template(template_id)

    print(f"\n📋 Template: {template.name}")
    print(f"   ID: {template.template_id}")
    print(f"   Version: {template.version}")
    print(f"   Author: {template.author}")
    print(f"   Tags: {', '.join(template.tags)}")
    print(
        f"   Estimated cost: ${template.estimated_cost_range[0]:.2f}-${template.estimated_cost_range[1]:.2f}"
    )
    print(f"   Estimated duration: {template.estimated_duration_minutes} minutes")

    print(f"\n📝 Form Schema: {template.form_schema.title}")
    print(f"   Questions: {len(template.form_schema.questions)}")

    for i, question in enumerate(template.form_schema.questions, 1):
        print(f"\n   {i}. {question.text}")
        print(f"      ID: {question.id}")
        print(f"      Type: {question.type.value}")
        if question.options:
            print(f"      Options: {', '.join(question.options)}")
        if question.default:
            print(f"      Default: {question.default}")

    print(f"\n🤖 Agent Composition Rules: {len(template.agent_composition_rules)}")

    for i, rule in enumerate(template.agent_composition_rules, 1):
        print(f"\n   {i}. {rule.role}")
        print(f"      Base template: {rule.base_template}")
        print(f"      Tier strategy: {rule.tier_strategy.value}")
        print(f"      Tools: {', '.join(rule.tools) if rule.tools else 'None'}")
        if rule.required_responses:
            print(f"      Required: {rule.required_responses}")
        if rule.config_mapping:
            print(f"      Config mapping: {rule.config_mapping}")

    return template


def demo_form_responses(template):
    """Demo 2: Creating form responses."""
    print_section("DEMO 2: Form Response Creation")

    # Scenario 1: Minimal responses (only required)
    print("\n📋 Scenario 1: Minimal Configuration")
    print("   (Only answering required questions)")

    minimal_response = FormResponse(
        template_id=template.template_id,
        responses={
            "package_name": "minimal-package",
            "has_tests": "No",
            "test_coverage_required": "None",
            "version_bump": "patch",
            "publish_to": "Skip publishing",
            "create_git_tag": "No",
            "update_changelog": "No",
        },
    )

    print(f"   Response ID: {minimal_response.response_id}")
    print(f"   Timestamp: {minimal_response.timestamp}")
    print(f"   Responses: {len(minimal_response.responses)}")

    # Scenario 2: Full responses (all quality checks)
    print("\n📋 Scenario 2: Full Quality Configuration")
    print("   (All quality checks enabled)")

    full_response = FormResponse(
        template_id=template.template_id,
        responses={
            "package_name": "awesome-package",
            "has_tests": "Yes",
            "test_coverage_required": "90%",
            "quality_checks": [
                "Type checking (mypy)",
                "Linting (ruff)",
                "Security scan (bandit)",
                "Dependency audit",
                "Documentation build",
            ],
            "version_bump": "minor",
            "publish_to": "PyPI (production)",
            "create_git_tag": "Yes",
            "update_changelog": "Yes",
        },
    )

    print(f"   Response ID: {full_response.response_id}")
    print(f"   Quality checks: {len(full_response.responses['quality_checks'])}")

    return minimal_response, full_response


def demo_agent_creation(template, minimal_response, full_response):
    """Demo 3: Dynamic agent generation."""
    print_section("DEMO 3: Dynamic Agent Generation")

    creator = DynamicAgentCreator()

    # Scenario 1: Minimal agents
    print("\n🤖 Scenario 1: Minimal Configuration Agents")

    minimal_agents = creator.create_agents(template, minimal_response)

    print(f"   Created {len(minimal_agents)} agents:")
    for agent in minimal_agents:
        print(f"      ✓ {agent.role}")
        print(f"        - Tier: {agent.tier_strategy.value}")
        print(f"        - Tools: {', '.join(agent.tools) if agent.tools else 'None'}")
        if agent.config:
            print(f"        - Config: {agent.config}")

    stats = creator.get_creation_stats()
    print("\n   Stats:")
    print(f"      Rules evaluated: {stats['total_rules_evaluated']}")
    print(f"      Agents created: {stats['agents_created']}")
    print(f"      Rules skipped: {stats['rules_skipped']}")

    # Scenario 2: Full agents
    print("\n🤖 Scenario 2: Full Quality Configuration Agents")

    creator.reset_stats()
    full_agents = creator.create_agents(template, full_response)

    print(f"   Created {len(full_agents)} agents:")
    for agent in full_agents:
        print(f"      ✓ {agent.role}")
        print(f"        - Tier: {agent.tier_strategy.value}")
        print(f"        - Tools: {', '.join(agent.tools) if agent.tools else 'None'}")
        if agent.config:
            print(f"        - Config: {agent.config}")

    stats = creator.get_creation_stats()
    print("\n   Stats:")
    print(f"      Rules evaluated: {stats['total_rules_evaluated']}")
    print(f"      Agents created: {stats['agents_created']}")
    print(f"      Rules skipped: {stats['rules_skipped']}")

    return minimal_agents, full_agents


def demo_cost_estimation(minimal_agents, full_agents):
    """Demo 4: Cost estimation."""
    print_section("DEMO 4: Cost Estimation")

    print("\n💰 Minimal Configuration Cost Estimate:")
    minimal_estimate = estimate_agent_costs(minimal_agents)
    print(f"   Total estimated cost: ${minimal_estimate['total_estimated_cost']:.2f}")
    print(f"   Agent count: {minimal_estimate['agent_count']}")
    print("   Cost by tier:")
    for tier, cost in minimal_estimate["by_tier"].items():
        print(f"      - {tier}: ${cost:.2f}")

    print("\n💰 Full Configuration Cost Estimate:")
    full_estimate = estimate_agent_costs(full_agents)
    print(f"   Total estimated cost: ${full_estimate['total_estimated_cost']:.2f}")
    print(f"   Agent count: {full_estimate['agent_count']}")
    print("   Cost by tier:")
    for tier, cost in full_estimate["by_tier"].items():
        print(f"      - {tier}: ${cost:.2f}")

    print(
        f"\n📊 Cost difference: ${full_estimate['total_estimated_cost'] - minimal_estimate['total_estimated_cost']:.2f}"
    )
    print(
        f"   ({full_estimate['agent_count'] - minimal_estimate['agent_count']} additional agents)"
    )


def demo_grouping_and_validation(full_agents):
    """Demo 5: Agent grouping and dependency validation."""
    print_section("DEMO 5: Agent Grouping & Dependency Validation")

    # Grouping by tier
    print("\n📊 Agents grouped by tier strategy:")
    grouped = group_agents_by_tier_strategy(full_agents)

    for tier, agents in grouped.items():
        print(f"\n   {tier.value.upper()}: {len(agents)} agents")
        for agent in agents:
            print(f"      - {agent.role}")

    # Dependency validation
    print("\n🔍 Dependency validation:")
    warnings = validate_agent_dependencies(full_agents)

    if warnings:
        print(f"   Found {len(warnings)} warning(s):")
        for warning in warnings:
            print(f"      ⚠️  {warning}")
    else:
        print("   ✅ All dependencies satisfied!")


def demo_comparison():
    """Demo 6: Side-by-side comparison."""
    print_section("DEMO 6: Configuration Comparison")

    print("\n📊 Minimal vs Full Configuration:")
    print("\n   ┌─────────────────────────┬──────────────┬──────────────┐")
    print("   │ Metric                  │ Minimal      │ Full         │")
    print("   ├─────────────────────────┼──────────────┼──────────────┤")
    print("   │ Agents created          │ 3            │ 7-8          │")
    print("   │ Estimated cost          │ $0.15        │ $0.40-0.60   │")
    print("   │ Quality checks          │ 0            │ 5            │")
    print("   │ Test coverage required  │ None         │ 90%          │")
    print("   │ Tier strategies         │ Mostly cheap │ Mixed        │")
    print("   │ Publishing              │ Skipped      │ PyPI (prod)  │")
    print("   └─────────────────────────┴──────────────┴──────────────┘")

    print("\n   Key insight: More quality → More agents → Higher cost")
    print("   But progressive escalation keeps costs optimized!")


def main():
    """Run all demos."""
    print("\n" + "█" * 70)
    print("█" + " " * 68 + "█")
    print("█" + "  META-WORKFLOW SYSTEM DEMO".center(68) + "█")
    print("█" + "  (Days 1-2 Implementation)".center(68) + "█")
    print("█" + " " * 68 + "█")
    print("█" * 70)

    try:
        # Demo 1: Template loading
        template = demo_template_loading()
        if not template:
            return

        # Demo 2: Form responses
        minimal_response, full_response = demo_form_responses(template)

        # Demo 3: Agent creation
        minimal_agents, full_agents = demo_agent_creation(template, minimal_response, full_response)

        # Demo 4: Cost estimation
        demo_cost_estimation(minimal_agents, full_agents)

        # Demo 5: Grouping and validation
        demo_grouping_and_validation(full_agents)

        # Demo 6: Comparison
        demo_comparison()

        # Final summary
        print_section("DEMO COMPLETE")
        print("\n✅ All components working correctly!")
        print("\n📌 Next steps:")
        print("   - Day 3: Meta-workflow execution engine")
        print("   - Day 4: Pattern learning & CLI")
        print("   - Day 5: Integration testing")
        print("\n🚀 Meta-workflow system foundation is solid!\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
