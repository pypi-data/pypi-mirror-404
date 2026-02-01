#!/usr/bin/env python3
"""Demonstration of Agent Coordination Signals (Pattern 2).

Shows how to use CoordinationSignals for TTL-based inter-agent communication,
including targeted signals, broadcasts, and waiting for signals.

Run: python examples/agent_coordination_demo.py

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

import asyncio
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from empathy_os.telemetry import CoordinationSignals


async def agent_producer(agent_id: str):
    """Simulate an agent that produces results and signals completion.

    Args:
        agent_id: Agent identifier
    """
    coordinator = CoordinationSignals(agent_id=agent_id)

    print(f"[{agent_id}] Starting work...")
    await asyncio.sleep(2)

    print(f"[{agent_id}] Work complete. Signaling consumer...")

    # Signal completion to consumer
    signal_id = coordinator.signal(
        signal_type="task_complete",
        source_agent=agent_id,
        target_agent="agent-consumer",
        payload={"result": "success", "data": {"value": 42}},
    )

    print(f"[{agent_id}] Signal sent: {signal_id}")


async def agent_consumer(agent_id: str):
    """Simulate an agent that waits for a signal from producer.

    Args:
        agent_id: Agent identifier
    """
    coordinator = CoordinationSignals(agent_id=agent_id)

    print(f"[{agent_id}] Waiting for task completion signal...")

    # Wait for signal (with timeout)
    signal = coordinator.wait_for_signal(
        signal_type="task_complete", source_agent="agent-producer", timeout=10.0
    )

    if signal:
        print(f"[{agent_id}] Received signal!")
        print(f"  From: {signal.source_agent}")
        print(f"  Type: {signal.signal_type}")
        print(f"  Payload: {signal.payload}")

        # Process result
        result = signal.payload.get("result")
        if result == "success":
            print(f"[{agent_id}] Processing successful result...")
        else:
            print(f"[{agent_id}] Handling error...")
    else:
        print(f"[{agent_id}] Timeout waiting for signal!")


async def demo_targeted_signals():
    """Demonstrate targeted signals between agents."""
    print("=" * 70)
    print("TARGETED AGENT SIGNALS DEMONSTRATION")
    print("=" * 70)

    # Run producer and consumer in parallel
    await asyncio.gather(agent_producer("agent-producer"), agent_consumer("agent-consumer"))


async def demo_broadcast_signals():
    """Demonstrate broadcast signals to all agents."""
    print("\n\n" + "=" * 70)
    print("BROADCAST SIGNALS DEMONSTRATION")
    print("=" * 70)

    # Create 3 consumer agents
    coordinators = {
        "agent-1": CoordinationSignals(agent_id="agent-1"),
        "agent-2": CoordinationSignals(agent_id="agent-2"),
        "agent-3": CoordinationSignals(agent_id="agent-3"),
    }

    print("\n📡 Broadcasting abort signal to all agents...")

    # Orchestrator broadcasts abort
    orchestrator = CoordinationSignals(agent_id="orchestrator")
    orchestrator.broadcast(
        signal_type="abort",
        source_agent="orchestrator",
        payload={"reason": "user_cancelled", "timestamp": time.time()},
    )

    # Small delay for signal propagation
    await asyncio.sleep(0.5)

    # Each agent checks for broadcast
    for agent_id, coord in coordinators.items():
        signal = coord.check_signal(signal_type="abort", consume=False)

        if signal:
            print(f"\n  ✅ {agent_id} received abort signal")
            print(f"     Reason: {signal.payload.get('reason')}")
        else:
            print(f"\n  ❌ {agent_id} did not receive signal")


async def demo_checkpoint_coordination():
    """Demonstrate checkpoint coordination pattern."""
    print("\n\n" + "=" * 70)
    print("CHECKPOINT COORDINATION DEMONSTRATION")
    print("=" * 70)

    print("\n📋 Scenario: 3 agents must reach checkpoint before continuing\n")

    # Create checkpoint coordinator
    checkpoint_coord = CoordinationSignals(agent_id="checkpoint-monitor")

    # Simulate agents reaching checkpoint
    agents = ["agent-alpha", "agent-beta", "agent-gamma"]

    for i, agent_id in enumerate(agents):
        await asyncio.sleep(1)  # Stagger arrivals

        coord = CoordinationSignals(agent_id=agent_id)
        coord.signal(
            signal_type="checkpoint",
            source_agent=agent_id,
            target_agent="checkpoint-monitor",
            payload={"arrived_at": time.time(), "status": "ready"},
        )

        print(f"  🟢 {agent_id} reached checkpoint ({i+1}/{len(agents)})")

    # Check how many agents reached checkpoint
    print("\n  Checking checkpoint status...")
    await asyncio.sleep(0.5)

    checkpoint_signals = checkpoint_coord.get_pending_signals(signal_type="checkpoint")
    print(f"  ✅ {len(checkpoint_signals)}/{len(agents)} agents at checkpoint")

    if len(checkpoint_signals) == len(agents):
        print("  🚀 All agents ready! Proceeding...")
    else:
        print("  ⏳ Waiting for remaining agents...")


async def demo_error_propagation():
    """Demonstrate error signal propagation."""
    print("\n\n" + "=" * 70)
    print("ERROR PROPAGATION DEMONSTRATION")
    print("=" * 70)

    print("\n⚠️  Agent encounters error and signals failure...\n")

    failing_agent = CoordinationSignals(agent_id="agent-worker")

    # Simulate work then error
    await asyncio.sleep(1)

    failing_agent.signal(
        signal_type="error",
        source_agent="agent-worker",
        target_agent="orchestrator",
        payload={
            "error_type": "ValidationError",
            "message": "Invalid input data",
            "stack_trace": "...(truncated)...",
        },
    )

    print("  ❌ Error signal sent to orchestrator")

    # Orchestrator receives error
    await asyncio.sleep(0.5)
    orchestrator = CoordinationSignals(agent_id="orchestrator")
    error_signal = orchestrator.check_signal(signal_type="error")

    if error_signal:
        print(f"\n  Orchestrator received error from {error_signal.source_agent}:")
        print(f"    Type: {error_signal.payload.get('error_type')}")
        print(f"    Message: {error_signal.payload.get('message')}")
        print("\n  Orchestrator action: Aborting workflow and notifying user...")


if __name__ == "__main__":
    print("\nℹ️  This demo requires Redis to be running.")
    print("  If you see errors, start Redis first:\n")
    print("    redis-server")
    print("    # or")
    print("    empathy memory start\n")

    try:
        asyncio.run(demo_targeted_signals())
        asyncio.run(demo_broadcast_signals())
        asyncio.run(demo_checkpoint_coordination())
        asyncio.run(demo_error_propagation())

        print("\n\n" + "=" * 70)
        print("ALL DEMONSTRATIONS COMPLETE")
        print("=" * 70)

        print("\n💡 CLI Commands:")
        print("  # View signals for an agent")
        print("  empathy telemetry signals --agent agent-consumer")
        print()
        print("  # View signals for orchestrator")
        print("  empathy telemetry signals --agent orchestrator")

    except KeyboardInterrupt:
        print("\n\n❌ Demo interrupted.")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
