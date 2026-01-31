"""Human Approval Gates Demo (Pattern 5).

This script demonstrates approval gates for workflow control:
- Requesting approval from workflow
- Responding to approval requests from UI
- Timeout handling
- Approval workflow integration

Requires Redis running locally.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

import asyncio
import threading
import time
from datetime import datetime

from empathy_os.telemetry import ApprovalGate
from empathy_os.workflows.base import BaseWorkflow, ModelTier


def demo_basic_approval_request():
    """Demo: Basic approval request with manual response."""
    print("=" * 70)
    print("DEMO 1: BASIC APPROVAL REQUEST")
    print("=" * 70)
    print()

    gate = ApprovalGate(agent_id="demo-workflow-001")

    print("📋 Workflow requesting approval for deployment...")
    print("   Approval type: deploy_to_production")
    print("   Context: version=2.0.0, risk=medium")
    print()

    # Simulate UI responding in background
    def respond_after_delay():
        time.sleep(2)
        print("✅ [UI] User approved the deployment request")
        ui_gate = ApprovalGate()
        ui_gate.respond_to_approval(
            request_id="approval_demo",  # Would come from get_pending_approvals()
            approved=True,
            responder="user@example.com",
            reason="Looks good to deploy",
        )

    # Note: In real usage, UI would call get_pending_approvals() and respond

    print("⏳ Workflow waiting for approval (timeout: 10 seconds)...")
    print()


def demo_approval_timeout():
    """Demo: Approval request with timeout."""
    print("=" * 70)
    print("DEMO 2: APPROVAL TIMEOUT")
    print("=" * 70)
    print()

    gate = ApprovalGate(agent_id="demo-workflow-002")

    print("📋 Workflow requesting approval for deletion...")
    print("   Approval type: delete_resource")
    print("   Context: resource_id=res-123")
    print("   Timeout: 3 seconds")
    print()

    print("⏳ Waiting for approval...")
    start_time = time.time()

    # Request approval with short timeout (no response)
    response = gate.request_approval(
        approval_type="delete_resource",
        context={"resource_id": "res-123"},
        timeout=3.0,
    )

    elapsed = time.time() - start_time

    print()
    if not response.approved:
        print(f"❌ Approval timed out after {elapsed:.1f} seconds")
        print(f"   Reason: {response.reason}")
    else:
        print("✅ Approval received")

    print()


def demo_approval_rejection():
    """Demo: Approval request with rejection."""
    print("=" * 70)
    print("DEMO 3: APPROVAL REJECTION")
    print("=" * 70)
    print()

    gate = ApprovalGate(agent_id="demo-workflow-003")

    print("📋 Workflow requesting approval for refactoring...")
    print("   Approval type: refactor_code")
    print("   Context: files=['api.py', 'models.py']")
    print()

    # Simulate rejection in background
    def reject_after_delay():
        time.sleep(1)
        print("🚫 [UI] User rejected the refactoring request")
        ui_gate = ApprovalGate()

        # In real usage: get pending approvals first
        pending = ui_gate.get_pending_approvals(approval_type="refactor_code")
        if pending:
            ui_gate.respond_to_approval(
                request_id=pending[0].request_id,
                approved=False,
                responder="tech_lead@example.com",
                reason="Too risky for current sprint",
            )

    response_thread = threading.Thread(target=reject_after_delay)
    response_thread.start()

    print("⏳ Waiting for approval...")
    response = gate.request_approval(
        approval_type="refactor_code",
        context={"files": ["api.py", "models.py"]},
        timeout=5.0,
    )

    response_thread.join()

    print()
    if response.approved:
        print("✅ Approval received")
    else:
        print(f"❌ Approval rejected by {response.responder}")
        print(f"   Reason: {response.reason}")

    print()


def demo_get_pending_approvals():
    """Demo: UI retrieving pending approval requests."""
    print("=" * 70)
    print("DEMO 4: UI RETRIEVING PENDING APPROVALS")
    print("=" * 70)
    print()

    # Create multiple approval requests
    print("📋 Creating 3 approval requests...")

    gate1 = ApprovalGate(agent_id="workflow-001")
    gate2 = ApprovalGate(agent_id="workflow-002")
    gate3 = ApprovalGate(agent_id="workflow-003")

    # Start approval requests in background threads
    def request_approval_1():
        gate1.request_approval(
            approval_type="deploy_to_staging",
            context={"version": "1.5.0"},
            timeout=60.0,
        )

    def request_approval_2():
        gate2.request_approval(
            approval_type="delete_old_data",
            context={"data_older_than": "90 days"},
            timeout=60.0,
        )

    def request_approval_3():
        gate3.request_approval(
            approval_type="upgrade_dependencies",
            context={"packages": ["django", "requests"]},
            timeout=60.0,
        )

    threads = [
        threading.Thread(target=request_approval_1),
        threading.Thread(target=request_approval_2),
        threading.Thread(target=request_approval_3),
    ]

    for thread in threads:
        thread.start()

    # Give requests time to be stored
    time.sleep(1)

    # UI: Retrieve pending approvals
    print()
    print("🔍 [UI] Retrieving pending approval requests...")
    ui_gate = ApprovalGate()
    pending = ui_gate.get_pending_approvals()

    print(f"   Found {len(pending)} pending approvals:")
    print()

    for i, request in enumerate(pending, 1):
        print(f"   {i}. {request.approval_type}")
        print(f"      Agent: {request.agent_id}")
        print(f"      Context: {request.context}")
        print(f"      Requested: {request.timestamp.strftime('%H:%M:%S')}")
        print(f"      Timeout: {request.timeout_seconds}s")
        print()

    # Cleanup: respond to all requests
    print("✅ [UI] Responding to all approval requests...")
    for request in pending:
        ui_gate.respond_to_approval(
            request_id=request.request_id,
            approved=True,
            responder="admin@example.com",
            reason="Batch approved",
        )

    # Wait for threads to complete
    for thread in threads:
        thread.join(timeout=1)

    print()


def demo_workflow_integration():
    """Demo: Approval gate integrated with workflow."""
    print("=" * 70)
    print("DEMO 5: WORKFLOW INTEGRATION")
    print("=" * 70)
    print()

    class DeploymentWorkflow(BaseWorkflow):
        """Workflow that requires approval before deployment."""

        name = "deployment-workflow"
        description = "Deploy with approval gate"
        stages = ["prepare", "request_approval", "deploy"]
        tier_map = {
            "prepare": ModelTier.CHEAP,
            "request_approval": ModelTier.CHEAP,
            "deploy": ModelTier.CHEAP,
        }

        async def run_stage(self, stage_name: str, tier: ModelTier, input_data: dict):
            if stage_name == "prepare":
                print("📦 [Workflow] Preparing deployment...")
                await asyncio.sleep(0.5)
                return {"prepared": True}, 0, 0

            elif stage_name == "request_approval":
                print("🔐 [Workflow] Requesting approval...")
                gate = ApprovalGate(agent_id=self._agent_id)

                # Start background responder
                def auto_approve():
                    time.sleep(2)
                    print("✅ [Auto-Approver] Approving deployment...")
                    ui_gate = ApprovalGate()
                    pending = ui_gate.get_pending_approvals(approval_type="deploy")
                    if pending:
                        ui_gate.respond_to_approval(
                            request_id=pending[0].request_id,
                            approved=True,
                            responder="automation@example.com",
                            reason="Auto-approved by CI",
                        )

                threading.Thread(target=auto_approve).start()

                response = gate.request_approval(
                    approval_type="deploy",
                    context={"version": input_data.get("version", "1.0.0")},
                    timeout=10.0,
                )

                if not response.approved:
                    raise ValueError(f"Deployment rejected: {response.reason}")

                print(f"✅ [Workflow] Approval received from {response.responder}")
                return {"approved": True, "responder": response.responder}, 0, 0

            elif stage_name == "deploy":
                print("🚀 [Workflow] Deploying to production...")
                await asyncio.sleep(0.5)
                return {"deployed": True}, 0, 0

    print("🏗️  Starting deployment workflow with approval gate...")
    print()

    workflow = DeploymentWorkflow()

    async def run_workflow():
        result = await workflow.execute({"version": "2.0.0"})
        return result

    result = asyncio.run(run_workflow())

    print()
    if result.success:
        print("✅ Workflow completed successfully")
        print(f"   Stages completed: {len(result.stage_results)}")
    else:
        print(f"❌ Workflow failed: {result.error}")

    print()


def main():
    """Run all approval gates demos."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 14 + "APPROVAL GATES DEMONSTRATION (PATTERN 5)" + " " * 14 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    print("This demo shows human approval gates for workflow control.")
    print()

    try:
        # Demo 2: Approval timeout (doesn't require responses)
        demo_approval_timeout()

        # Demo 4: Get pending approvals (creates and responds to requests)
        demo_get_pending_approvals()

        # Demo 5: Workflow integration
        demo_workflow_integration()

        # Note: Demo 1 and 3 are commented out as they require manual interaction
        # In production, these would be integrated with a web UI

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("    Make sure Redis is running: redis-server")
        print("    Or run: empathy memory start")
        import traceback
        traceback.print_exc()
        return

    print()
    print("=" * 70)
    print("✅ APPROVAL GATES DEMO COMPLETE")
    print("=" * 70)
    print()
    print("💡 Key Takeaways:")
    print("  1. Workflows can pause and wait for human approval")
    print("  2. UI can retrieve pending approvals via get_pending_approvals()")
    print("  3. Approvals have configurable timeout (default 5 minutes)")
    print("  4. Rejection includes reason from approver")
    print("  5. Approval gates use coordination signals under the hood")
    print()
    print("📖 Next Steps:")
    print("  - Build web UI for approval management")
    print("  - Add approval to critical workflow operations")
    print("  - Configure timeout based on operation risk level")
    print()
    print("📚 Documentation:")
    print("  - docs/AGENT_TRACKING_AND_COORDINATION.md")
    print("  - Pattern 5: Human Approval Gates")
    print()


if __name__ == "__main__":
    main()
