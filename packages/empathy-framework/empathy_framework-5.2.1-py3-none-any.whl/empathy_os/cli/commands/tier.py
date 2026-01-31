"""Tier management commands for intelligent model selection.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""


def cmd_tier_recommend(args):
    """Get intelligent tier recommendation for a bug/task.

    Analyzes bug description and historical patterns to recommend
    the most cost-effective tier (HAIKU/SONNET/OPUS).

    Args:
        args: Namespace object from argparse with attributes:
            - description (str): Bug or task description to analyze.
            - files (str | None): Comma-separated list of affected files.
            - complexity (str | None): Complexity hint (low/medium/high).

    Returns:
        None: Prints tier recommendation with confidence and expected cost.
    """
    from empathy_os.tier_recommender import TierRecommender

    recommender = TierRecommender()

    # Get recommendation
    result = recommender.recommend(
        bug_description=args.description,
        files_affected=args.files.split(",") if args.files else None,
        complexity_hint=args.complexity,
    )

    # Display results
    print()
    print("=" * 60)
    print("  TIER RECOMMENDATION")
    print("=" * 60)
    print()
    print(f"  Bug/Task: {args.description}")
    print()
    print(f"  📍 Recommended Tier: {result.tier}")
    print(f"  🎯 Confidence: {result.confidence * 100:.1f}%")
    print(f"  💰 Expected Cost: ${result.expected_cost:.3f}")
    print(f"  🔄 Expected Attempts: {result.expected_attempts:.1f}")
    print()
    print("  📊 Reasoning:")
    print(f"     {result.reasoning}")
    print()

    if result.similar_patterns_count > 0:
        print(f"  ✅ Based on {result.similar_patterns_count} similar patterns")
    else:
        print("  ⚠️  No historical data - using conservative default")

    if result.fallback_used:
        print()
        print("  💡 Tip: As more patterns are collected, recommendations")
        print("     will become more accurate and personalized.")

    print()
    print("=" * 60)
    print()


def cmd_tier_stats(args):
    """Show tier pattern learning statistics.

    Displays statistics about collected patterns and tier distribution.

    Args:
        args: Namespace object from argparse (no additional attributes used).

    Returns:
        None: Prints tier statistics, savings percentages, and bug type distribution.
    """
    from empathy_os.tier_recommender import TierRecommender

    recommender = TierRecommender()
    stats = recommender.get_stats()

    print()
    print("=" * 60)
    print("  TIER PATTERN LEARNING STATS")
    print("=" * 60)
    print()

    if stats.get("total_patterns", 0) == 0:
        print("  No patterns collected yet.")
        print()
        print("  💡 Patterns are automatically collected as you use")
        print("     cascading workflows with enhanced tracking enabled.")
        print()
        print("=" * 60)
        print()
        return

    print(f"  Total Patterns: {stats['total_patterns']}")
    print(f"  Avg Savings: {stats['avg_savings_percent']}%")
    print()

    print("  TIER DISTRIBUTION")
    print("  " + "-" * 40)
    for tier, count in stats["patterns_by_tier"].items():
        percent = (count / stats["total_patterns"]) * 100
        bar = "█" * int(percent / 5)
        print(f"  {tier:10} {count:3} ({percent:5.1f}%) {bar}")
    print()

    print("  BUG TYPE DISTRIBUTION")
    print("  " + "-" * 40)
    sorted_types = sorted(
        stats["bug_type_distribution"].items(), key=lambda x: x[1], reverse=True
    )
    for bug_type, count in sorted_types[:10]:
        percent = (count / stats["total_patterns"]) * 100
        print(f"  {bug_type:20} {count:3} ({percent:5.1f}%)")

    print()
    print("=" * 60)
    print()
