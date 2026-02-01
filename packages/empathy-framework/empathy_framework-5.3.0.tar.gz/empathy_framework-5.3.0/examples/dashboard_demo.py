"""Dashboard Demo - Generate Test Data and Run Dashboard.

This script generates sample data for all 6 patterns and runs the dashboard
so you can see it in action.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

import random
import threading
import time
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    # Load .env from project root
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # dotenv not installed, will use system environment

from empathy_os.telemetry import (
    ApprovalGate,
    CoordinationSignals,
    EventStreamer,
    FeedbackLoop,
    HeartbeatCoordinator,
)
from empathy_os.telemetry.feedback_loop import ModelTier


def keep_agents_alive(memory):
    """Continuously publish heartbeats to keep agents visible in dashboard.

    Runs in background thread, updating agent heartbeats every 3 seconds.
    """
    agent_configs = {
        "Code Analyzer": {"tasks": ["Analyzing code quality", "Running static analysis", "Checking dependencies"]},
        "Test Generator": {"tasks": ["Generating unit tests", "Creating test fixtures", "Validating coverage"]},
        "Refactoring Agent": {"tasks": ["Refactoring code", "Optimizing performance", "Improving readability"]},
        "CI/CD Pipeline": {"tasks": ["Running CI/CD pipeline", "Deploying to staging", "Idle - awaiting tasks"]},
        "System Monitor": {"tasks": ["Monitoring system health", "Processing metrics", "Generating reports"]},
    }

    coordinators = {}
    for agent_id, config in agent_configs.items():
        coordinator = HeartbeatCoordinator(memory=memory)
        coordinator.start_heartbeat(
            agent_id=f"agent-{list(agent_configs.keys()).index(agent_id) + 1}",  # Internal ID
            display_name=agent_id,  # Display name for dashboard
            metadata={"demo": True, "persistent": True}
        )
        coordinators[agent_id] = coordinator

    while True:
        for agent_id, config in agent_configs.items():
            coordinator = coordinators[agent_id]
            # Randomly vary status and progress for realistic simulation
            status = random.choice(["running", "running", "running", "idle"])  # Bias toward "running"
            progress = random.random()
            current_task = random.choice(config["tasks"])

            coordinator.beat(
                status=status,
                progress=progress,
                current_task=current_task
            )

        time.sleep(3)  # Update heartbeats every 3 seconds


def generate_test_data():
    """Generate test data for all dashboard patterns."""
    print("=" * 70)
    print("GENERATING TEST DATA FOR DASHBOARD")
    print("=" * 70)
    print()

    # Initialize Redis memory backend for all patterns
    try:
        from empathy_os.memory.short_term import RedisShortTermMemory

        memory = RedisShortTermMemory()
        print("✅ Connected to Redis memory backend")
        print()
    except Exception as e:
        print(f"❌ Failed to connect to Redis: {e}")
        print("   Make sure Redis is running and REDIS_ENABLED=true in .env")
        print()
        return None

    # Pattern 1: Agent Heartbeats (continuous in background)
    print("📊 Pattern 1: Setting up continuous agent heartbeats...")
    print("  ✓ 5 agents will publish heartbeats every 3 seconds")
    print("  ✓ Agents: Code Analyzer, Test Generator, Refactoring Agent, CI/CD Pipeline, System Monitor")
    print()

    # Pattern 2: Coordination Signals
    print("📡 Pattern 2: Creating test coordination signals...")
    for i in range(10):
        source = f"agent-{random.randint(1, 5)}"
        target = f"agent-{random.randint(1, 5)}"
        signal_types = ["status_update", "task_complete", "request_help", "acknowledge"]

        signals = CoordinationSignals(memory=memory, agent_id=source)
        signals.signal(
            signal_type=random.choice(signal_types),
            source_agent=source,
            target_agent=target,
            payload={"message": f"Test signal {i+1}", "demo": True},
            ttl_seconds=3600,  # 1 hour TTL for demo (default is 5 minutes)
        )

        print(f"  ✓ Signal: {source} → {target}")

    print()

    # Pattern 4: Event Streaming
    print("📤 Pattern 4: Creating test events...")
    streamer = EventStreamer(memory=memory)

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

    # Pattern 5: Approval Requests (create directly without blocking)
    print("✋ Pattern 5: Creating test approval requests...")

    # Create approval requests directly in Redis without blocking
    gate = ApprovalGate(memory=memory, agent_id="demo-workflow")

    # Manually store 2 approval requests without the blocking wait
    from uuid import uuid4
    from datetime import datetime
    import json

    for i in range(2):
        request_id = f"approval_{uuid4().hex[:8]}"
        approval_data = {
            "request_id": request_id,
            "approval_type": random.choice(["deploy_to_staging", "delete_old_data", "refactor_module"]),
            "agent_id": "demo-workflow",
            "context": {"version": "1.0.0", "demo": True, "number": i+1},
            "timestamp": datetime.utcnow().isoformat(),
            "timeout_seconds": 300.0,
            "status": "pending"
        }

        # Store in Redis (without empathy: prefix for approval gates)
        request_key = f"approval_request:{request_id}"
        memory._client.setex(request_key, 360, json.dumps(approval_data))
        print(f"  ✓ Approval request {i+1}: {approval_data['approval_type']}")

    print()

    # Pattern 6: Quality Feedback
    print("📊 Pattern 6: Creating test quality feedback...")
    feedback = FeedbackLoop(memory=memory)

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

    return memory


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
        memory = generate_test_data()
        if memory is None:
            return  # Failed to connect to Redis
    except Exception as e:
        print(f"\n❌ Failed to generate test data: {e}")
        print("    Make sure Redis is running: redis-server")
        print("    Or run: empathy memory start")
        return

    # Start background thread for continuous agent heartbeats
    heartbeat_thread = threading.Thread(target=keep_agents_alive, args=(memory,), daemon=True)
    heartbeat_thread.start()
    print("🔄 Background thread started: Agents will remain active")
    print()

    # Start dashboard
    print()
    print("=" * 70)
    print("STARTING DASHBOARD SERVER")
    print("=" * 70)
    print()
    print("📊 Dashboard will be available at: http://localhost:8000")
    print()
    print("💡 What you'll see:")
    print("  • 5 active agents with live heartbeats (updating every 3s)")
    print("  • 10 coordination signals (Pattern 2)")
    print("  • 15 stream events (Pattern 4)")
    print("  • 2 pending approval requests (Pattern 5)")
    print("  • Quality metrics for 3 workflows × 3 stages × 3 tiers (Pattern 6)")
    print()
    print("🔄 Dashboard auto-refreshes every 5 seconds")
    print("💓 Agent heartbeats update continuously in background")
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
