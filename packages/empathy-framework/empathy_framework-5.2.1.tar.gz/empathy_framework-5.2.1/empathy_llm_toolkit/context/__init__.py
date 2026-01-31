"""Context Management for Empathy Framework

Strategic compaction to preserve critical state through context window resets.
Ensures trust levels, detected patterns, and session continuity survive compaction events.

Architectural patterns inspired by everything-claude-code by Affaan Mustafa.
See: https://github.com/affaan-m/everything-claude-code (MIT License)
See: ACKNOWLEDGMENTS.md for full attribution.

Copyright 2025 Smart AI Memory, LLC
Licensed under Fair Source 0.9
"""

from empathy_llm_toolkit.context.compaction import CompactionStateManager, CompactState, SBARHandoff
from empathy_llm_toolkit.context.manager import ContextManager

__all__ = [
    "CompactionStateManager",
    "CompactState",
    "ContextManager",
    "SBARHandoff",
]
