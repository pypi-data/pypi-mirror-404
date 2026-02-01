#!/usr/bin/env python3
"""Demonstration of Agent Heartbeat Tracking (Pattern 1).

Shows how to use HeartbeatCoordinator to track agent execution status
and monitor active agents via TTL-based heartbeats.

Run: python examples/agent_tracking_demo.py

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

import asyncio
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from empathy_os.telemetry import HeartbeatCoordinator


async def simulate_agent_work(agent_id: str, duration: float, fail: bool = False):
    """Simulate an agent performing work with heartbeat updates.

    Args:
        agent_id: Agent identifier
        duration: Simulated work duration in seconds
        fail: Whether to simulate failure
    """
    coordinator = HeartbeatCoordinator()

    # Start heartbeat
    print(f"[{agent_id}] Starting...")
    coordinator.start_heartbeat(
        agent_id=agent_id, metadata={"workflow": "demo-workflow", "type": "simulation"}
    )

    try:
        # Simulate work with progress updates
        steps = 5
        for i in range(steps):
            await asyncio.sleep(duration / steps)
            progress = (i + 1) / steps

            coordinator.beat(
                status="running", progress=progress, current_task=f"Processing step {i+1}/{steps}"
            )

            print(f"[{agent_id}] Progress: {progress*100:.0f}%")

        if fail:
            raise Exception("Simulated failure")

        # Complete successfully
        coordinator.stop_heartbeat(final_status="completed")
        print(f"[{agent_id}] Completed!")

    except Exception as e:
        # Report failure
        coordinator.stop_heartbeat(final_status="failed")
        print(f"[{agent_id}] Failed: {e}")


async def demo_heartbeat_tracking():
    """Demonstrate heartbeat tracking with multiple agents."""
    print("=" * 70)
    print("AGENT HEARTBEAT TRACKING DEMONSTRATION")
    print("=" * 70)

    coordinator = HeartbeatCoordinator()

    # Check initial state
    print("\n📊 Initial State:")
    active = coordinator.get_active_agents()
    print(f"  Active agents: {len(active)}")

    # Launch multiple simulated agents
    print("\n🚀 Launching 3 agents...")

    tasks = [
        simulate_agent_work("agent-fast", duration=3.0, fail=False),
        simulate_agent_work("agent-slow", duration=6.0, fail=False),
        simulate_agent_work("agent-fail", duration=2.0, fail=True),
    ]

    # Wait a moment for agents to start
    await asyncio.sleep(1)

    # Check active agents
    print("\n\n📊 Agents After 1 Second:")
    active = coordinator.get_active_agents()
    print(f"  Active agents: {len(active)}")
    for agent in active:
        print(f"    - {agent.agent_id}: {agent.status} ({agent.progress*100:.0f}%)")

    # Wait for all agents to complete
    await asyncio.gather(*tasks)

    # Final status
    print("\n\n📊 Final Status:")
    active = coordinator.get_active_agents()
    print(f"  Active agents: {len(active)}")

    if active:
        for agent in active:
            time_since = (coordinator._get_time() - agent.last_beat).total_seconds()
            print(f"    - {agent.agent_id}: {agent.status} (last seen {time_since:.1f}s ago)")

    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)

    print("\n💡 CLI Commands:")
    print("  # View active agents")
    print("  empathy telemetry agents")
    print()
    print("  # Check if specific agent is alive")
    print(f"  empathy telemetry agents --agent agent-fast")


async def demo_stale_detection():
    """Demonstrate stale agent detection."""
    print("\n\n" + "=" * 70)
    print("STALE AGENT DETECTION")
    print("=" * 70)

    coordinator = HeartbeatCoordinator()

    # Start an agent that will become stale
    print("\n🚀 Starting agent that will become stale...")
    coordinator.start_heartbeat(agent_id="stale-agent", metadata={"test": "stale"})
    coordinator.beat(status="running", progress=0.5, current_task="Working...")

    print("  Agent started. Waiting 5 seconds...")
    await asyncio.sleep(5)

    # Check for stale agents (threshold: 3 seconds)
    stale = coordinator.get_stale_agents(threshold_seconds=3.0)
    print(f"\n📊 Stale agents (no update in >3s): {len(stale)}")

    for agent in stale:
        from datetime import datetime

        time_since = (datetime.utcnow() - agent.last_beat).total_seconds()
        print(f"  ⚠️  {agent.agent_id}: last beat {time_since:.1f}s ago")

    # Clean up
    coordinator.stop_heartbeat()


if __name__ == "__main__":
    print("\nℹ️  This demo requires Redis to be running.")
    print("  If you see 'No memory backend available', start Redis first:\n")
    print("    redis-server")
    print("    # or")
    print("    empathy memory start\n")

    try:
        asyncio.run(demo_heartbeat_tracking())
        asyncio.run(demo_stale_detection())
    except KeyboardInterrupt:
        print("\n\n❌ Demo interrupted.")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
