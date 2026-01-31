"""Demo: Progressive Test Generation with Tier Escalation.

This example demonstrates how to use the ProgressiveTestGenWorkflow to
generate tests with automatic cost-efficient tier escalation.

Run this script to see progressive escalation in action.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from empathy_os.workflows.progressive import (EscalationConfig,
                                              ProgressiveTestGenWorkflow, Tier)


def create_sample_file() -> Path:
    """Create a sample Python file to generate tests for.

    Returns:
        Path to created file
    """
    sample_code = '''"""Sample module for progressive test generation demo."""


def calculate_total(prices: list[float], tax_rate: float = 0.0) -> float:
    """Calculate total price with tax.

    Args:
        prices: List of item prices
        tax_rate: Tax rate as decimal (e.g., 0.08 for 8%)

    Returns:
        Total price including tax

    Example:
        >>> calculate_total([10.0, 20.0], 0.08)
        32.4
    """
    if not prices:
        return 0.0

    subtotal = sum(prices)
    tax = subtotal * tax_rate
    return subtotal + tax


def format_currency(amount: float, symbol: str = "$") -> str:
    """Format amount as currency string.

    Args:
        amount: Dollar amount
        symbol: Currency symbol

    Returns:
        Formatted currency string

    Example:
        >>> format_currency(32.40)
        '$32.40'
    """
    return f"{symbol}{amount:.2f}"


async def fetch_prices(product_ids: list[str]) -> list[float]:
    """Fetch prices for products (async example).

    Args:
        product_ids: List of product IDs

    Returns:
        List of prices

    Note:
        This is a placeholder - real implementation would call an API.
    """
    # Simulate API call
    return [10.0] * len(product_ids)
'''

    sample_file = Path("sample_module.py")
    sample_file.write_text(sample_code)

    return sample_file


def main():
    """Run progressive test generation demo."""
    print("=" * 70)
    print("PROGRESSIVE TEST GENERATION DEMO")
    print("=" * 70)
    print()

    # Create sample file
    print("Creating sample Python file...")
    sample_file = create_sample_file()
    print(f"✓ Created: {sample_file}")
    print()

    # Configure progressive escalation
    config = EscalationConfig(
        enabled=True,
        tiers=[Tier.CHEAP, Tier.CAPABLE, Tier.PREMIUM],
        cheap_min_attempts=2,
        capable_max_attempts=6,
        max_cost=5.00,
        auto_approve_under=2.00,  # Auto-approve under $2
        save_tier_results=True
    )

    print("Progressive Escalation Configuration:")
    print(f"  Enabled: {config.enabled}")
    print(f"  Tiers: {[t.value for t in config.tiers]}")
    print(f"  Max Cost: ${config.max_cost:.2f}")
    print(f"  Auto-Approve Under: ${config.auto_approve_under:.2f}")
    print()

    # Create workflow
    print("Initializing ProgressiveTestGenWorkflow...")
    workflow = ProgressiveTestGenWorkflow(config)
    print("✓ Workflow ready")
    print()

    # Execute test generation
    print(f"Generating tests for {sample_file}...")
    print("-" * 70)

    try:
        result = workflow.execute(target_file=str(sample_file))

        print("-" * 70)
        print()

        # Display results
        print("RESULTS:")
        print(f"  Success: {result.success}")
        print(f"  Total Cost: ${result.total_cost:.2f}")
        print(f"  Total Duration: {result.total_duration:.1f}s")
        print(f"  Cost Savings: ${result.cost_savings:.2f} ({result.cost_savings_percent:.0f}%)")
        print()

        print(f"Tier Progression ({len(result.tier_results)} tiers used):")
        for i, tier_result in enumerate(result.tier_results, 1):
            print(f"  {i}. {tier_result.tier.value.upper()} Tier ({tier_result.model})")
            print(f"     - Generated: {len(tier_result.generated_items)} tests")
            print(f"     - Quality: CQS={tier_result.quality_score:.1f}")
            print(f"     - Success Rate: {tier_result.success_rate:.1%}")
            print(f"     - Cost: ${tier_result.cost:.2f}")
            print(f"     - Duration: {tier_result.duration:.1f}s")

            if tier_result.escalated:
                print(f"     - Escalated: {tier_result.escalation_reason}")

        print()

        # Show generated tests
        if result.final_result.generated_items:
            print("Generated Tests (sample):")
            for item in result.final_result.generated_items[:3]:
                print(f"  - test_{item['function_name']}() "
                      f"(quality: {item['quality_score']:.1f})")

        print()

        # Display progression report
        print("=" * 70)
        print("FULL PROGRESSION REPORT")
        print("=" * 70)
        print(result.generate_report())

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    finally:
        # Cleanup
        if sample_file.exists():
            sample_file.unlink()
            print(f"Cleaned up: {sample_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
