"""CLI commands for Anthropic Batch API operations (50% cost savings).

Provides commands to submit, monitor, and retrieve results from batch processing jobs.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

import asyncio
import json
import logging
import os
from pathlib import Path

from empathy_os.config import _validate_file_path
from empathy_os.workflows.batch_processing import BatchProcessingWorkflow

logger = logging.getLogger(__name__)


def cmd_batch_submit(args):
    """Submit a batch processing job from JSON file.

    Args:
        args: Arguments with input_file path

    File format:
        [
            {
                "task_id": "task_1",
                "task_type": "analyze_logs",
                "input_data": {"logs": "ERROR: ..."},
                "model_tier": "capable"
            },
            ...
        ]
    """
    input_file = Path(args.input_file)
    if not input_file.exists():
        print(f"❌ Error: Input file not found: {input_file}")
        return 1

    print(f"📤 Submitting batch from {input_file}...")

    try:
        # Get API key from environment
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
            return 1

        # Load requests from file
        workflow = BatchProcessingWorkflow(api_key=api_key)
        requests = workflow.load_requests_from_file(str(input_file))

        print(f"  Found {len(requests)} requests")

        # Create batch (sync operation)
        batch_id = workflow.batch_provider.create_batch(
            [
                {
                    "custom_id": req.task_id,
                    "params": {
                        "model": "claude-sonnet-4-5-20250929",  # Default model
                        "messages": workflow._format_messages(req),
                        "max_tokens": 4096,
                    },
                }
                for req in requests
            ]
        )

        print("\n✅ Batch submitted successfully!")
        print(f"   Batch ID: {batch_id}")
        print(f"\nMonitor status with: empathy batch status {batch_id}")
        print(f"Retrieve results with: empathy batch results {batch_id} output.json")
        print(
            f"Or wait for completion: empathy batch wait {batch_id} output.json --poll-interval 300"
        )

        return 0

    except Exception as e:
        logger.exception("Failed to submit batch")
        print(f"❌ Error: {e}")
        return 1


def cmd_batch_status(args):
    """Check status of a batch processing job.

    Args:
        args: Arguments with batch_id
    """
    batch_id = args.batch_id

    print(f"🔍 Checking status for batch {batch_id}...")

    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
            return 1

        workflow = BatchProcessingWorkflow(api_key=api_key)
        status = workflow.batch_provider.get_batch_status(batch_id)

        print("\n📊 Batch Status:")
        print(f"   ID: {status.id}")
        print(f"   Processing Status: {status.processing_status}")
        print(f"   Created: {status.created_at}")

        if hasattr(status, "ended_at") and status.ended_at:
            print(f"   Ended: {status.ended_at}")

        print("\n📈 Request Counts:")
        counts = status.request_counts
        print(f"   Processing: {counts.processing}")
        print(f"   Succeeded: {counts.succeeded}")
        print(f"   Errored: {counts.errored}")
        print(f"   Canceled: {counts.canceled}")
        print(f"   Expired: {counts.expired}")

        if status.processing_status == "ended":
            print("\n✅ Batch processing completed!")
            print(f"   Retrieve results with: empathy batch results {batch_id} output.json")
        else:
            print("\n⏳ Batch still processing...")

        # Output JSON if requested
        if args.json:
            print("\n" + json.dumps(status.__dict__, indent=2, default=str))

        return 0

    except Exception as e:
        logger.exception("Failed to get batch status")
        print(f"❌ Error: {e}")
        return 1


def cmd_batch_results(args):
    """Retrieve results from a completed batch.

    Args:
        args: Arguments with batch_id and output_file
    """
    batch_id = args.batch_id
    output_file = args.output_file

    print(f"📥 Retrieving results for batch {batch_id}...")

    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
            return 1

        workflow = BatchProcessingWorkflow(api_key=api_key)

        # Check status first
        status = workflow.batch_provider.get_batch_status(batch_id)

        if status.processing_status != "ended":
            print(f"❌ Error: Batch has not ended processing (status: {status.processing_status})")
            print(f"   Wait for completion with: empathy batch wait {batch_id} {output_file}")
            return 1

        # Get results
        results = workflow.batch_provider.get_batch_results(batch_id)

        # Save to file
        validated_path = _validate_file_path(output_file)
        with open(validated_path, "w") as f:
            json.dump([dict(r) for r in results], f, indent=2, default=str)

        print(f"\n✅ Results saved to {validated_path}")
        print(f"   Total: {len(results)} results")

        # Summary
        succeeded = sum(
            1 for r in results if r.get("result", {}).get("type") == "succeeded"
        )
        errored = sum(
            1 for r in results if r.get("result", {}).get("type") == "errored"
        )

        print(f"   Succeeded: {succeeded}")
        print(f"   Errored: {errored}")

        return 0

    except Exception as e:
        logger.exception("Failed to retrieve results")
        print(f"❌ Error: {e}")
        return 1


def cmd_batch_wait(args):
    """Wait for batch to complete and retrieve results.

    Args:
        args: Arguments with batch_id, output_file, poll_interval, timeout
    """
    batch_id = args.batch_id
    output_file = args.output_file
    poll_interval = args.poll_interval
    timeout = args.timeout

    print(f"⏳ Waiting for batch {batch_id} to complete...")
    print(f"   Polling every {poll_interval}s (max {timeout}s)")

    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
            return 1

        workflow = BatchProcessingWorkflow(api_key=api_key)

        # Wait for completion (async)
        results = asyncio.run(
            workflow.batch_provider.wait_for_batch(
                batch_id, poll_interval=poll_interval, timeout=timeout
            )
        )

        # Save results
        validated_path = _validate_file_path(output_file)
        with open(validated_path, "w") as f:
            json.dump([dict(r) for r in results], f, indent=2, default=str)

        print(f"\n✅ Batch completed! Results saved to {validated_path}")
        print(f"   Total: {len(results)} results")

        # Summary
        succeeded = sum(
            1 for r in results if r.get("result", {}).get("type") == "succeeded"
        )
        errored = sum(
            1 for r in results if r.get("result", {}).get("type") == "errored"
        )

        print(f"   Succeeded: {succeeded}")
        print(f"   Errored: {errored}")

        return 0

    except TimeoutError:
        print(f"\n⏰ Timeout: Batch did not complete within {timeout}s")
        print(f"   Check status with: empathy batch status {batch_id}")
        return 1
    except Exception as e:
        logger.exception("Failed to wait for batch")
        print(f"❌ Error: {e}")
        return 1
