"""Empathy Framework Routing Module

Intelligent request routing to workflows using LLM classification.

Usage:
    from empathy_os.routing import SmartRouter, quick_route

    # Full router
    router = SmartRouter()
    decision = await router.route("Fix security issue in auth.py")
    print(f"Use: {decision.primary_workflow}")

    # Quick helper
    decision = await quick_route("Optimize database queries")

Copyright 2025 Smart AI Memory, LLC
Licensed under Fair Source 0.9
"""

from .chain_executor import ChainConfig, ChainExecution, ChainExecutor, ChainStep, ChainTrigger
from .classifier import ClassificationResult, HaikuClassifier
from .smart_router import RoutingDecision, SmartRouter, quick_route
from .workflow_registry import WORKFLOW_REGISTRY, WorkflowInfo, WorkflowRegistry

__all__ = [
    "WORKFLOW_REGISTRY",
    "ChainConfig",
    "ChainExecution",
    # Chain Executor
    "ChainExecutor",
    "ChainStep",
    "ChainTrigger",
    "ClassificationResult",
    # Classifier
    "HaikuClassifier",
    "RoutingDecision",
    # Smart Router
    "SmartRouter",
    "WorkflowInfo",
    # Workflow Registry
    "WorkflowRegistry",
    "quick_route",
]
