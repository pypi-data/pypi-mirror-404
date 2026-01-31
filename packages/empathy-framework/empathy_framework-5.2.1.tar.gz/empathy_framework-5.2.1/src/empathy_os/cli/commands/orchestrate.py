"""Orchestration commands for meta-workflows.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

import asyncio
import json

from empathy_os.logging_config import get_logger

logger = get_logger(__name__)


def cmd_orchestrate(args):
    """Run meta-orchestration workflows.

    Orchestrates teams of agents to accomplish complex tasks through
    intelligent composition patterns.

    Args:
        args: Namespace object from argparse with attributes:
            - workflow (str): Orchestration workflow name.
            - path (str): Target path for orchestration.
            - mode (str | None): Execution mode (e.g., 'daily', 'weekly', 'release').
            - json (bool): If True, output as JSON format.
            - dry_run (bool): If True, show plan without executing.
            - verbose (bool): If True, show detailed output.

    Returns:
        int: 0 on success, 1 on failure.
    """
    from empathy_os.workflows.orchestrated_health_check import OrchestratedHealthCheckWorkflow
    from empathy_os.workflows.orchestrated_release_prep import OrchestratedReleasePrepWorkflow

    # Get workflow type
    workflow_type = args.workflow

    # Only print header in non-JSON mode
    if not (hasattr(args, "json") and args.json):
        print()
        print("=" * 60)
        print(f"  META-ORCHESTRATION: {workflow_type.upper()}")
        print("=" * 60)
        print()

    if workflow_type == "release-prep":
        # Release Preparation workflow
        path = args.path or "."
        quality_gates = {}

        # Collect custom quality gates
        if hasattr(args, "min_coverage") and args.min_coverage is not None:
            quality_gates["min_coverage"] = args.min_coverage
        if hasattr(args, "min_quality") and args.min_quality is not None:
            quality_gates["min_quality_score"] = args.min_quality
        if hasattr(args, "max_critical") and args.max_critical is not None:
            quality_gates["max_critical_issues"] = args.max_critical

        # Only print details in non-JSON mode
        if not (hasattr(args, "json") and args.json):
            print(f"  Project Path: {path}")
            if quality_gates:
                print(f"  Quality Gates: {quality_gates}")
            print()
            print("  🔍 Parallel Validation Agents:")
            print("    • Security Auditor (vulnerability scan)")
            print("    • Test Coverage Analyzer (gap analysis)")
            print("    • Code Quality Reviewer (best practices)")
            print("    • Documentation Writer (completeness)")
            print()

        # Create workflow
        workflow = OrchestratedReleasePrepWorkflow(
            quality_gates=quality_gates if quality_gates else None
        )

        try:
            # Execute workflow
            report = asyncio.run(workflow.execute(path=path))

            # Display results
            if hasattr(args, "json") and args.json:
                print(json.dumps(report.to_dict(), indent=2))
            else:
                print(report.format_console_output())

            # Return appropriate exit code
            return 0 if report.approved else 1

        except Exception as e:
            print(f"  ❌ Error executing release prep workflow: {e}")
            print()
            logger.exception("Release prep workflow failed")
            return 1

    elif workflow_type == "test-coverage":
        # Test Coverage Boost workflow - DISABLED in v4.0.0
        print("  ⚠️  FEATURE DISABLED")
        print("  " + "-" * 56)
        print()
        print("  The test-coverage workflow has been disabled in v4.0.0")
        print("  due to poor quality (0% test pass rate).")
        print()
        print("  This feature is being redesigned and will return in a")
        print("  future release with improved test generation quality.")
        print()
        print("  Available v4.0 workflows:")
        print("    • health-check - Real-time codebase health analysis")
        print("    • release-prep - Quality gate validation")
        print()
        return 1

    elif workflow_type == "health-check":
        # Health Check workflow
        mode = args.mode or "daily"
        project_root = args.project_root or "."
        focus_area = getattr(args, "focus", None)

        # Only print details in non-JSON mode
        if not (hasattr(args, "json") and args.json):
            print(f"  Mode: {mode.upper()}")
            print(f"  Project Root: {project_root}")
            if focus_area:
                print(f"  Focus Area: {focus_area}")
            print()

            # Show agents for mode
            mode_agents = {
                "daily": ["Security", "Coverage", "Quality"],
                "weekly": ["Security", "Coverage", "Quality", "Performance", "Documentation"],
                "release": [
                    "Security",
                    "Coverage",
                    "Quality",
                    "Performance",
                    "Documentation",
                    "Architecture",
                ],
            }

            print(f"  🔍 {mode.capitalize()} Check Agents:")
            for agent in mode_agents.get(mode, []):
                print(f"    • {agent}")
            print()

        # Create workflow
        workflow = OrchestratedHealthCheckWorkflow(mode=mode, project_root=project_root)

        try:
            # Execute workflow
            report = asyncio.run(workflow.execute())

            # Display results
            if hasattr(args, "json") and args.json:
                print(json.dumps(report.to_dict(), indent=2))
            else:
                print(report.format_console_output())

            # Return appropriate exit code (70+ is passing)
            return 0 if report.overall_health_score >= 70 else 1

        except Exception as e:
            print(f"  ❌ Error executing health check workflow: {e}")
            print()
            logger.exception("Health check workflow failed")
            return 1

    else:
        print(f"  ❌ Unknown workflow type: {workflow_type}")
        print()
        print("  Available workflows:")
        print("    - release-prep: Release readiness validation (parallel agents)")
        print("    - health-check: Project health assessment (daily/weekly/release modes)")
        print()
        print("  Note: test-coverage workflow disabled in v4.0.0 (being redesigned)")
        print()
        return 1

    print()
    print("=" * 60)
    print()

    return 0
