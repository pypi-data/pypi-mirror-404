"""Hook System for Empathy Framework

Event-driven automation system for Empathy Framework.
Supports PreToolUse, PostToolUse, SessionStart, SessionEnd, PreCompact, and Stop events.

Architectural patterns inspired by everything-claude-code by Affaan Mustafa.
See: https://github.com/affaan-m/everything-claude-code (MIT License)
See: ACKNOWLEDGMENTS.md for full attribution.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

from empathy_llm_toolkit.hooks.config import HookConfig, HookDefinition, HookEvent
from empathy_llm_toolkit.hooks.executor import HookExecutor
from empathy_llm_toolkit.hooks.registry import HookRegistry

__all__ = [
    "HookConfig",
    "HookDefinition",
    "HookEvent",
    "HookExecutor",
    "HookRegistry",
]
