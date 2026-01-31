#!/usr/bin/env python3
"""Demonstration of BaseWorkflow with Agent Tracking & Coordination.

Shows how to use Pattern 1 (Heartbeat Tracking) and Pattern 2 (Coordination Signals)
with the BaseWorkflow class for multi-agent orchestration.

Run: python examples/coordinated_workflow_demo.py

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from empathy_os.workflows.base import BaseWorkflow, ModelTier


class ProducerWorkflow(BaseWorkflow):
    """Producer workflow that generates data and signals completion."""

    name = "producer"
    description = "Generates data and signals completion to consumer"
    stages = ["generate", "validate", "notify"]
    tier_map = {
        "generate": ModelTier.CHEAP,
        "validate": ModelTier.CAPABLE,
        "notify": ModelTier.CHEAP,
    }

    async def run_stage(self, stage_name: str, tier: ModelTier, input_data: dict):
        """Run a workflow stage with heartbeat tracking.

        Heartbeat tracking is automatic via BaseWorkflow.execute() integration.
        This method just implements stage logic.
        """
        if stage_name == "generate":
            # Simulate data generation
            await asyncio.sleep(2)
            result = {
                "data": ["item1", "item2", "item3"],
                "count": 3,
                "timestamp": "2026-01-27T12:00:00Z",
            }
            return result, 100, 50  # output, input_tokens, output_tokens

        elif stage_name == "validate":
            # Simulate validation
            await asyncio.sleep(1)
            result = {
                "valid": True,
                "data": input_data.get("data", []),
                "validation_score": 95,
            }
            return result, 80, 40

        elif stage_name == "notify":
            # Signal completion to consumer
            self.send_signal(
                signal_type="task_complete",
                target_agent="consumer",
                payload={
                    "result": "success",
                    "data": input_data.get("data", []),
                    "count": input_data.get("count", 0),
                },
            )
            print(f"[{self.name}] Sent task_complete signal to consumer")

            result = {"notified": True}
            return result, 50, 20


class ConsumerWorkflow(BaseWorkflow):
    """Consumer workflow that waits for producer signal."""

    name = "consumer"
    description = "Waits for producer signal and processes data"
    stages = ["wait", "process", "report"]
    tier_map = {
        "wait": ModelTier.CHEAP,
        "process": ModelTier.CAPABLE,
        "report": ModelTier.CHEAP,
    }

    async def run_stage(self, stage_name: str, tier: ModelTier, input_data: dict):
        """Run a workflow stage with coordination."""

        if stage_name == "wait":
            print(f"[{self.name}] Waiting for producer signal...")

            # Wait for producer to signal completion (Pattern 2)
            signal = self.wait_for_signal(
                signal_type="task_complete", source_agent="producer", timeout=30.0
            )

            if signal is None:
                raise TimeoutError("Producer did not signal completion")

            print(f"[{self.name}] Received signal from producer!")
            result = {
                "signal_received": True,
                "data": signal.payload.get("data", []),
                "producer_result": signal.payload.get("result"),
            }
            return result, 50, 20

        elif stage_name == "process":
            # Process the data from producer
            await asyncio.sleep(2)
            data = input_data.get("data", [])
            result = {
                "processed": True,
                "items": [f"processed_{item}" for item in data],
                "count": len(data),
            }
            return result, 120, 60

        elif stage_name == "report":
            # Final report
            result = {
                "status": "completed",
                "items_processed": input_data.get("count", 0),
                "success": True,
            }
            return result, 80, 40


class OrchestratorWorkflow(BaseWorkflow):
    """Orchestrator that coordinates multiple agents via broadcasts."""

    name = "orchestrator"
    description = "Coordinates multiple agents with checkpoints"
    stages = ["launch", "checkpoint", "finalize"]
    tier_map = {
        "launch": ModelTier.CHEAP,
        "checkpoint": ModelTier.CAPABLE,
        "finalize": ModelTier.CHEAP,
    }

    async def run_stage(self, stage_name: str, tier: ModelTier, input_data: dict):
        """Run orchestrator stage with coordination."""

        if stage_name == "launch":
            print(f"[{self.name}] Launching agents...")

            # Broadcast start signal to all agents
            self.send_signal(
                signal_type="start",
                target_agent=None,  # Broadcast
                payload={"timestamp": "2026-01-27T12:00:00Z"},
            )

            result = {"launched": True, "agents": ["worker-1", "worker-2", "worker-3"]}
            return result, 50, 20

        elif stage_name == "checkpoint":
            print(f"[{self.name}] Waiting for agents to reach checkpoint...")

            # Simulate waiting for multiple agents
            # In real scenario, would wait for multiple checkpoint signals
            await asyncio.sleep(3)

            result = {"checkpoint_reached": True, "agents_ready": 3}
            return result, 100, 50

        elif stage_name == "finalize":
            print(f"[{self.name}] Finalizing orchestration...")

            # Broadcast completion to all agents
            self.send_signal(
                signal_type="complete",
                target_agent=None,  # Broadcast
                payload={"status": "success"},
            )

            result = {"finalized": True, "total_agents": 3}
            return result, 80, 40


async def demo_producer_consumer():
    """Demonstrate producer-consumer pattern with coordination."""
    print("=" * 70)
    print("PRODUCER-CONSUMER WORKFLOW DEMONSTRATION")
    print("=" * 70)
    print()

    # Create producer with heartbeat tracking and coordination
    producer = ProducerWorkflow(
        enable_heartbeat_tracking=True,
        enable_coordination=True,
        agent_id="producer",
    )

    # Create consumer with heartbeat tracking and coordination
    consumer = ConsumerWorkflow(
        enable_heartbeat_tracking=True,
        enable_coordination=True,
        agent_id="consumer",
    )

    # Run both workflows concurrently
    print("Starting producer and consumer workflows...")
    print()

    producer_task = asyncio.create_task(producer.execute())
    consumer_task = asyncio.create_task(consumer.execute())

    # Wait for both to complete
    producer_result, consumer_result = await asyncio.gather(producer_task, consumer_task)

    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Producer: {'✅ Success' if producer_result.success else '❌ Failed'}")
    print(f"Consumer: {'✅ Success' if consumer_result.success else '❌ Failed'}")
    print()


async def demo_orchestrator():
    """Demonstrate orchestrator pattern with broadcasts."""
    print("=" * 70)
    print("ORCHESTRATOR WORKFLOW DEMONSTRATION")
    print("=" * 70)
    print()

    orchestrator = OrchestratorWorkflow(
        enable_heartbeat_tracking=True,
        enable_coordination=True,
        agent_id="orchestrator",
    )

    print("Starting orchestrator workflow...")
    print()

    result = await orchestrator.execute()

    print()
    print("=" * 70)
    print("RESULT")
    print("=" * 70)
    print(f"Orchestrator: {'✅ Success' if result.success else '❌ Failed'}")
    print(f"Total cost: ${result.cost_report.total_cost:.4f}")
    print()


async def demo_abort_handling():
    """Demonstrate abort signal handling."""
    print("=" * 70)
    print("ABORT SIGNAL DEMONSTRATION")
    print("=" * 70)
    print()

    class AbortableWorkflow(BaseWorkflow):
        """Workflow that checks for abort signals."""

        name = "abortable"
        description = "Checks for abort signals between stages"
        stages = ["stage1", "stage2", "stage3"]
        tier_map = {
            "stage1": ModelTier.CHEAP,
            "stage2": ModelTier.CAPABLE,
            "stage3": ModelTier.CHEAP,
        }

        async def run_stage(self, stage_name: str, tier: ModelTier, input_data: dict):
            """Run stage with abort checking."""
            # Check for abort signal before processing
            abort_signal = self.check_signal(signal_type="abort")
            if abort_signal:
                reason = abort_signal.payload.get("reason", "unknown")
                print(f"[{self.name}] Received abort signal: {reason}")
                raise RuntimeError(f"Workflow aborted: {reason}")

            # Simulate work
            await asyncio.sleep(1)
            print(f"[{self.name}] Completed {stage_name}")

            result = {"stage": stage_name, "completed": True}
            return result, 50, 20

    workflow = AbortableWorkflow(
        enable_heartbeat_tracking=True,
        enable_coordination=True,
        agent_id="abortable-worker",
    )

    # Simulate abort after 2 seconds
    async def send_abort():
        await asyncio.sleep(2)
        workflow.send_signal(
            signal_type="abort",
            target_agent="abortable-worker",
            payload={"reason": "user_cancelled"},
        )
        print("[Abort Sender] Sent abort signal")

    print("Starting abortable workflow...")
    print("(Abort signal will be sent after 2 seconds)")
    print()

    # Run workflow and abort sender concurrently
    abort_task = asyncio.create_task(send_abort())
    workflow_task = asyncio.create_task(workflow.execute())

    result = await workflow_task
    await abort_task

    print()
    print("=" * 70)
    print("RESULT")
    print("=" * 70)
    print(f"Workflow: {'✅ Success' if result.success else '❌ Aborted (expected)'}")
    if result.error:
        print(f"Error: {result.error}")
    print()


if __name__ == "__main__":
    print()
    print("ℹ️  This demo requires Redis to be running.")
    print("  If you see errors, start Redis first:")
    print()
    print("    redis-server")
    print("    # or")
    print("    empathy memory start")
    print()

    try:
        # Demo 1: Producer-Consumer pattern
        asyncio.run(demo_producer_consumer())

        # Demo 2: Orchestrator pattern
        asyncio.run(demo_orchestrator())

        # Demo 3: Abort handling
        asyncio.run(demo_abort_handling())

        print("=" * 70)
        print("ALL DEMONSTRATIONS COMPLETE")
        print("=" * 70)
        print()
        print("💡 CLI Commands:")
        print("  # View active agents")
        print("  empathy telemetry agents")
        print()
        print("  # View signals for an agent")
        print("  empathy telemetry signals --agent producer")
        print("  empathy telemetry signals --agent consumer")
        print()

    except KeyboardInterrupt:
        print("\n\n❌ Demo interrupted.")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
