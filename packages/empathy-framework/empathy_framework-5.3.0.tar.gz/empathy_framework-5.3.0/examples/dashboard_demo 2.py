"""Dashboard Demo - Generate Test Data and Run Dashboard.

This script generates sample data for all 6 patterns and runs the dashboard
so you can see it in action.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

import random
import threading
import time

from empathy_os.telemetry import (
    ApprovalGate,
    CoordinationSignals,
    EventStreamer,
    FeedbackLoop,
    HeartbeatCoordinator,
)
from empathy_os.telemetry.feedback_loop import ModelTier


def generate_test_data():
    """Generate test data for all dashboard patterns."""
    print("=" * 70)
    print("GENERATING TEST DATA FOR DASHBOARD")
    print("=" * 70)
    print()

    # Pattern 1: Agent Heartbeats
    print("📊 Pattern 1: Creating test agent heartbeats...")
    for i in range(5):
        agent_id = f"agent-{i+1}"
        coordinator = HeartbeatCoordinator(agent_id=agent_id)

        status = random.choice(["running", "idle", "running", "running"])
        progress = random.random()
        tasks = [
            "Analyzing code quality",
            "Generating tests",
            "Running validation",
            "Processing workflow",
            "Idle - awaiting tasks",
        ]

        coordinator.report(
            status=status, progress=progress, current_task=random.choice(tasks), metadata={"demo": True}
        )

        print(f"  ✓ {agent_id}: {status} ({progress*100:.0f}%)")

    print()

    # Pattern 2: Coordination Signals
    print("📡 Pattern 2: Creating test coordination signals...")
    for i in range(10):
        source = f"agent-{random.randint(1, 5)}"
        target = f"agent-{random.randint(1, 5)}"
        signal_types = ["status_update", "task_complete", "request_help", "acknowledge"]

        signals = CoordinationSignals(agent_id=source)
        signals.signal(
            signal_type=random.choice(signal_types),
            source_agent=source,
            target_agent=target,
            payload={"message": f"Test signal {i+1}", "demo": True},
        )

        print(f"  ✓ Signal: {source} → {target}")

    print()

    # Pattern 4: Event Streaming
    print("📤 Pattern 4: Creating test events...")
    streamer = EventStreamer()

    for i in range(15):
        event_types = ["workflow_progress", "agent_heartbeat", "coordination_signal"]
        workflows = ["code-review", "test-generation", "refactoring"]

        streamer.publish_event(
            event_type=random.choice(event_types),
            data={
                "workflow": random.choice(workflows),
                "stage": random.choice(["analysis", "generation", "validation"]),
                "progress": random.random(),
                "demo": True,
            },
            source=f"agent-{random.randint(1, 5)}",
        )

        print(f"  ✓ Event {i+1} published")

    print()

    # Pattern 5: Approval Requests (create in background to avoid blocking)
    print("✋ Pattern 5: Creating test approval requests...")

    def create_approval():
        gate = ApprovalGate(agent_id="demo-workflow")
        # This will timeout after 60s if not approved
        gate.request_approval(
            approval_type=random.choice(["deploy_to_staging", "delete_old_data", "refactor_module"]),
            context={"version": "1.0.0", "demo": True},
            timeout=300.0,  # 5 minutes
        )

    # Create 2 approval requests in background
    for i in range(2):
        thread = threading.Thread(target=create_approval, daemon=True)
        thread.start()
        time.sleep(0.5)  # Stagger creation

    print(f"  ✓ 2 approval requests created (will timeout in 5 minutes)")
    print()

    # Pattern 6: Quality Feedback
    print("📊 Pattern 6: Creating test quality feedback...")
    feedback = FeedbackLoop()

    workflows = ["code-review", "test-generation", "refactoring"]
    stages = ["analysis", "generation", "validation"]
    tiers = [ModelTier.CHEAP, ModelTier.CAPABLE, ModelTier.PREMIUM]

    for workflow in workflows:
        for stage in stages:
            for tier in tiers:
                # Generate 10-15 samples per combination
                num_samples = random.randint(10, 15)

                for i in range(num_samples):
                    # Vary quality by tier
                    if tier == ModelTier.CHEAP:
                        base_quality = 0.65
                    elif tier == ModelTier.CAPABLE:
                        base_quality = 0.80
                    else:  # PREMIUM
                        base_quality = 0.90

                    # Add some randomness
                    quality = base_quality + (random.random() * 0.15 - 0.075)
                    quality = max(0.0, min(1.0, quality))  # Clamp to 0-1

                    feedback.record_feedback(
                        workflow_name=workflow,
                        stage_name=stage,
                        tier=tier,
                        quality_score=quality,
                        metadata={"demo": True, "tokens": random.randint(50, 300)},
                    )

                print(f"  ✓ {workflow}/{stage}/{tier.value}: {num_samples} samples")

    print()
    print("=" * 70)
    print("✅ TEST DATA GENERATION COMPLETE")
    print("=" * 70)
    print()


def run_dashboard_demo():
    """Run dashboard demo with test data."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 17 + "AGENT COORDINATION DASHBOARD DEMO" + " " * 18 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    print("This demo will:")
    print("  1. Generate test data for all 6 patterns")
    print("  2. Start the dashboard web server")
    print("  3. Open your browser to view the dashboard")
    print()

    # Generate test data
    try:
        generate_test_data()
    except Exception as e:
        print(f"\n❌ Failed to generate test data: {e}")
        print("    Make sure Redis is running: redis-server")
        print("    Or run: empathy memory start")
        return

    # Start dashboard
    print()
    print("=" * 70)
    print("STARTING DASHBOARD SERVER")
    print("=" * 70)
    print()
    print("📊 Dashboard will be available at: http://localhost:8000")
    print()
    print("💡 What you'll see:")
    print("  • 5 active agents with heartbeats (Pattern 1)")
    print("  • 10 coordination signals (Pattern 2)")
    print("  • 15 stream events (Pattern 4)")
    print("  • 2 pending approval requests (Pattern 5)")
    print("  • Quality metrics for 3 workflows × 3 stages × 3 tiers (Pattern 6)")
    print()
    print("🔄 Dashboard auto-refreshes every 5 seconds")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 70)
    print()

    # Import and run dashboard
    try:
        # Try simple server first (no dependencies)
        from empathy_os.dashboard import run_simple_dashboard

        run_simple_dashboard(host="127.0.0.1", port=8000)

    except KeyboardInterrupt:
        print("\n\n🛑 Dashboard stopped")
        print()

    except Exception as e:
        print(f"\n❌ Failed to start dashboard: {e}")
        print()
        print("📖 Troubleshooting:")
        print("  • Ensure Redis is running: redis-server")
        print("  • Check if port 8000 is available")
        print("  • For FastAPI version: pip install fastapi uvicorn")
        print()


if __name__ == "__main__":
    run_dashboard_demo()
