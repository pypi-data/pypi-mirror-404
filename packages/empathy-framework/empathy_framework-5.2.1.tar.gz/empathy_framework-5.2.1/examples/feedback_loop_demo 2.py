"""Agent-to-LLM Feedback Loop Demo (Pattern 6).

This script demonstrates quality-based learning and adaptive routing:
- Recording quality feedback after LLM responses
- Getting tier recommendations based on historical performance
- Analyzing quality statistics and trends
- Identifying underperforming workflow stages

Requires Redis running locally.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

import random
import time
from empathy_os.telemetry import FeedbackLoop
from empathy_os.telemetry.feedback_loop import ModelTier


def demo_record_feedback():
    """Demo: Recording quality feedback for workflow stages."""
    print("=" * 70)
    print("DEMO 1: RECORDING QUALITY FEEDBACK")
    print("=" * 70)
    print()

    feedback = FeedbackLoop()

    print("📊 Recording quality feedback for code-review workflow...")
    print()

    # Simulate quality ratings for "cheap" tier over time
    print("🔵 Cheap tier performance (10 samples):")
    for i in range(10):
        # Cheap tier: variable quality (0.55-0.75)
        quality = 0.55 + (random.random() * 0.2)

        feedback_id = feedback.record_feedback(
            workflow_name="code-review",
            stage_name="analysis",
            tier=ModelTier.CHEAP,
            quality_score=quality,
            metadata={"tokens": 100 + i * 10, "latency_ms": 800 + i * 50},
        )

        if feedback_id:
            print(f"  Sample {i+1}: Quality {quality:.2f} → Recorded {feedback_id}")

    print()

    # Simulate quality ratings for "capable" tier
    print("🟢 Capable tier performance (10 samples):")
    for i in range(10):
        # Capable tier: better quality (0.75-0.95)
        quality = 0.75 + (random.random() * 0.2)

        feedback_id = feedback.record_feedback(
            workflow_name="code-review",
            stage_name="analysis",
            tier=ModelTier.CAPABLE,
            quality_score=quality,
            metadata={"tokens": 200 + i * 20, "latency_ms": 1200 + i * 100},
        )

        if feedback_id:
            print(f"  Sample {i+1}: Quality {quality:.2f} → Recorded {feedback_id}")

    print()


def demo_get_quality_stats():
    """Demo: Analyzing quality statistics."""
    print("=" * 70)
    print("DEMO 2: QUALITY STATISTICS ANALYSIS")
    print("=" * 70)
    print()

    feedback = FeedbackLoop()

    # Get stats for cheap tier
    cheap_stats = feedback.get_quality_stats("code-review", "analysis", tier="cheap")

    if cheap_stats:
        print("📉 Cheap Tier Statistics:")
        print(f"  Average Quality: {cheap_stats.avg_quality:.2f}")
        print(f"  Quality Range: {cheap_stats.min_quality:.2f} - {cheap_stats.max_quality:.2f}")
        print(f"  Sample Count: {cheap_stats.sample_count}")
        print(f"  Recent Trend: {cheap_stats.recent_trend:+.2f} ({'📈 improving' if cheap_stats.recent_trend > 0 else '📉 declining'})")
    else:
        print("No stats available for cheap tier")

    print()

    # Get stats for capable tier
    capable_stats = feedback.get_quality_stats("code-review", "analysis", tier="capable")

    if capable_stats:
        print("📈 Capable Tier Statistics:")
        print(f"  Average Quality: {capable_stats.avg_quality:.2f}")
        print(f"  Quality Range: {capable_stats.min_quality:.2f} - {capable_stats.max_quality:.2f}")
        print(f"  Sample Count: {capable_stats.sample_count}")
        print(f"  Recent Trend: {capable_stats.recent_trend:+.2f} ({'📈 improving' if capable_stats.recent_trend > 0 else '📉 declining'})")
    else:
        print("No stats available for capable tier")

    print()


def demo_tier_recommendation():
    """Demo: Getting tier recommendations based on quality."""
    print("=" * 70)
    print("DEMO 3: TIER RECOMMENDATIONS")
    print("=" * 70)
    print()

    feedback = FeedbackLoop()

    # Get recommendation for cheap tier
    print("🤔 Asking: Should we upgrade from CHEAP tier?")
    recommendation = feedback.recommend_tier(
        workflow_name="code-review", stage_name="analysis", current_tier="cheap"
    )

    print()
    print("💡 Recommendation:")
    print(f"  Current Tier: {recommendation.current_tier.upper()}")
    print(f"  Recommended Tier: {recommendation.recommended_tier.upper()}")
    print(f"  Confidence: {recommendation.confidence:.1%}")
    print(f"  Reason: {recommendation.reason}")

    if recommendation.recommended_tier != recommendation.current_tier:
        print()
        print(f"✅ Action: Upgrade to {recommendation.recommended_tier.upper()} tier for better quality")
    else:
        print()
        print("✅ Action: Continue using current tier")

    print()

    # Get recommendation for capable tier
    print("🤔 Asking: Is CAPABLE tier performing well?")
    recommendation2 = feedback.recommend_tier(
        workflow_name="code-review", stage_name="analysis", current_tier="capable"
    )

    print()
    print("💡 Recommendation:")
    print(f"  Current Tier: {recommendation2.current_tier.upper()}")
    print(f"  Recommended Tier: {recommendation2.recommended_tier.upper()}")
    print(f"  Confidence: {recommendation2.confidence:.1%}")
    print(f"  Reason: {recommendation2.reason}")

    print()


def demo_underperforming_stages():
    """Demo: Identifying underperforming workflow stages."""
    print("=" * 70)
    print("DEMO 4: IDENTIFYING UNDERPERFORMING STAGES")
    print("=" * 70)
    print()

    feedback = FeedbackLoop()

    # Create feedback for multiple stages with varying quality
    print("📊 Creating feedback for multiple workflow stages...")

    # Stage 1: Good performance
    for i in range(10):
        quality = 0.8 + (random.random() * 0.1)  # 0.8-0.9
        feedback.record_feedback(
            workflow_name="multi-stage-workflow",
            stage_name="validation",
            tier="cheap",
            quality_score=quality,
        )

    # Stage 2: Poor performance
    for i in range(10):
        quality = 0.5 + (random.random() * 0.15)  # 0.5-0.65
        feedback.record_feedback(
            workflow_name="multi-stage-workflow",
            stage_name="generation",
            tier="cheap",
            quality_score=quality,
        )

    # Stage 3: Acceptable performance
    for i in range(10):
        quality = 0.72 + (random.random() * 0.08)  # 0.72-0.80
        feedback.record_feedback(
            workflow_name="multi-stage-workflow",
            stage_name="review",
            tier="cheap",
            quality_score=quality,
        )

    print()

    # Find underperforming stages
    print("🔍 Finding stages with quality < 0.7...")
    underperforming = feedback.get_underperforming_stages(
        workflow_name="multi-stage-workflow", quality_threshold=0.7
    )

    print()
    if underperforming:
        print(f"❌ Found {len(underperforming)} underperforming stage(s):")
        print()
        for stage_name, stats in underperforming:
            print(f"  Stage: {stage_name}")
            print(f"    Average Quality: {stats.avg_quality:.2f} (below 0.7 threshold)")
            print(f"    Sample Count: {stats.sample_count}")
            print(f"    Range: {stats.min_quality:.2f} - {stats.max_quality:.2f}")
            print()
    else:
        print("✅ All stages performing above threshold!")

    print()


def demo_feedback_history():
    """Demo: Retrieving feedback history."""
    print("=" * 70)
    print("DEMO 5: FEEDBACK HISTORY")
    print("=" * 70)
    print()

    feedback = FeedbackLoop()

    # Get recent feedback for code-review
    print("📜 Recent feedback for code-review/analysis (last 5)...")
    history = feedback.get_feedback_history("code-review", "analysis", limit=5)

    print()
    if history:
        print(f"Found {len(history)} recent feedback entries:")
        print()
        for i, entry in enumerate(history, 1):
            print(f"  {i}. {entry.feedback_id}")
            print(f"     Tier: {entry.tier.upper()}")
            print(f"     Quality: {entry.quality_score:.2f}")
            print(f"     Time: {entry.timestamp.strftime('%H:%M:%S')}")
            if entry.metadata:
                print(f"     Metadata: {entry.metadata}")
            print()
    else:
        print("No feedback history available")

    print()


def demo_adaptive_routing():
    """Demo: Using feedback for adaptive routing decisions."""
    print("=" * 70)
    print("DEMO 6: ADAPTIVE ROUTING IN ACTION")
    print("=" * 70)
    print()

    feedback = FeedbackLoop()

    # Simulate a workflow that adapts based on feedback
    print("🔄 Simulating adaptive workflow routing...")
    print()

    workflow_name = "adaptive-workflow"
    stage_name = "processing"

    # Start with cheap tier
    current_tier = "cheap"
    print(f"Starting with: {current_tier.upper()} tier")

    # Simulate 3 iterations
    for iteration in range(1, 4):
        print()
        print(f"--- Iteration {iteration} ---")

        # Simulate LLM response quality (degrading over time for demo)
        quality = max(0.5, 0.9 - (iteration * 0.15))

        print(f"LLM Response Quality: {quality:.2f}")

        # Record feedback
        feedback_id = feedback.record_feedback(
            workflow_name=workflow_name,
            stage_name=stage_name,
            tier=current_tier,
            quality_score=quality,
        )

        if feedback_id:
            print(f"Recorded: {feedback_id}")

        # Get recommendation after sufficient samples
        if iteration >= 2:
            recommendation = feedback.recommend_tier(
                workflow_name=workflow_name, stage_name=stage_name, current_tier=current_tier
            )

            print()
            print(f"Recommendation: {recommendation.recommended_tier.upper()}")
            print(f"Confidence: {recommendation.confidence:.1%}")
            print(f"Reason: {recommendation.reason}")

            # Apply recommendation
            if recommendation.recommended_tier != current_tier:
                print()
                print(f"⬆️  Upgrading: {current_tier.upper()} → {recommendation.recommended_tier.upper()}")
                current_tier = recommendation.recommended_tier

        time.sleep(0.5)

    print()
    print(f"Final tier: {current_tier.upper()}")
    print()


def main():
    """Run all feedback loop demos."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 13 + "AGENT-TO-LLM FEEDBACK LOOP (PATTERN 6)" + " " * 16 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    print("This demo shows quality-based learning and adaptive routing.")
    print()

    try:
        # Demo 1: Record feedback
        demo_record_feedback()

        # Demo 2: Analyze quality stats
        demo_get_quality_stats()

        # Demo 3: Get tier recommendations
        demo_tier_recommendation()

        # Demo 4: Find underperforming stages
        demo_underperforming_stages()

        # Demo 5: View feedback history
        demo_feedback_history()

        # Demo 6: Adaptive routing
        demo_adaptive_routing()

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("    Make sure Redis is running: redis-server")
        print("    Or run: empathy memory start")
        import traceback

        traceback.print_exc()
        return

    print()
    print("=" * 70)
    print("✅ FEEDBACK LOOP DEMO COMPLETE")
    print("=" * 70)
    print()
    print("💡 Key Takeaways:")
    print("  1. Record quality scores (0.0-1.0) after LLM responses")
    print("  2. System recommends tier upgrades when quality < 0.7")
    print("  3. System recommends downgrades when quality > 0.9 for cost savings")
    print("  4. Quality trends track improvement/decline over time")
    print("  5. Identify underperforming stages for optimization")
    print()
    print("📖 Next Steps:")
    print("  - Integrate feedback recording into workflows")
    print("  - Use tier recommendations for adaptive routing")
    print("  - Monitor quality trends to detect regressions")
    print("  - Optimize underperforming stages")
    print()
    print("📚 Documentation:")
    print("  - docs/AGENT_TRACKING_AND_COORDINATION.md")
    print("  - Pattern 6: Agent-to-LLM Feedback Loop")
    print()


if __name__ == "__main__":
    main()
