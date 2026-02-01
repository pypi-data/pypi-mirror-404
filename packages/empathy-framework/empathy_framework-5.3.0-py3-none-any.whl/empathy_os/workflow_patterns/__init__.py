"""Workflow Pattern Library.

Extracted patterns from 17 existing workflows for rapid workflow generation.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

from .behavior import CodeScannerPattern, ConditionalTierPattern, ConfigDrivenPattern
from .core import PatternCategory, WorkflowComplexity, WorkflowPattern
from .output import ResultDataclassPattern
from .registry import WorkflowPatternRegistry, get_workflow_pattern_registry
from .structural import CrewBasedPattern, MultiStagePattern, SingleStagePattern

__all__ = [
    # Core
    "WorkflowPattern",
    "PatternCategory",
    "WorkflowComplexity",
    # Structural
    "SingleStagePattern",
    "MultiStagePattern",
    "CrewBasedPattern",
    # Behavioral
    "ConditionalTierPattern",
    "ConfigDrivenPattern",
    "CodeScannerPattern",
    # Output
    "ResultDataclassPattern",
    # Registry
    "WorkflowPatternRegistry",
    "get_workflow_pattern_registry",
]
