"""Markdown Agent System

Define agents in Markdown files with YAML frontmatter for portability.
Integrates with Empathy Framework's UnifiedAgentConfig and model tier system.

Markdown agent format inspired by everything-claude-code by Affaan Mustafa.
See: https://github.com/affaan-m/everything-claude-code (MIT License)
See: ACKNOWLEDGMENTS.md for full attribution.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

from empathy_llm_toolkit.agents_md.loader import AgentLoader
from empathy_llm_toolkit.agents_md.parser import MarkdownAgentParser
from empathy_llm_toolkit.agents_md.registry import AgentRegistry

__all__ = [
    "MarkdownAgentParser",
    "AgentLoader",
    "AgentRegistry",
]
