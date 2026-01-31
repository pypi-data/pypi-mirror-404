"""Meta-orchestration system for dynamic agent composition.

This package provides the infrastructure for dynamically composing
agent teams based on task requirements. It enables intelligent task
analysis, agent spawning, and execution strategy selection.

Example:
    >>> from empathy_os.orchestration import AgentTemplate, get_template
    >>> template = get_template("test_coverage_analyzer")
    >>> print(template.role)
    Test Coverage Expert

    >>> from empathy_os.orchestration import get_strategy
    >>> strategy = get_strategy("tool_enhanced")
    >>> print(strategy.__class__.__name__)
    ToolEnhancedStrategy
"""

from empathy_os.orchestration.agent_templates import (
    AgentCapability,
    AgentTemplate,
    ResourceRequirements,
    get_all_templates,
    get_template,
    get_templates_by_capability,
    get_templates_by_tier,
)
from empathy_os.orchestration.execution_strategies import (
    DelegationChainStrategy,
    ExecutionStrategy,
    PromptCachedSequentialStrategy,
    ToolEnhancedStrategy,
    get_strategy,
)
from empathy_os.orchestration.meta_orchestrator import (
    CompositionPattern,
    ExecutionPlan,
    MetaOrchestrator,
    TaskComplexity,
    TaskDomain,
    TaskRequirements,
)

__all__ = [
    # Agent Templates
    "AgentTemplate",
    "AgentCapability",
    "ResourceRequirements",
    "get_template",
    "get_all_templates",
    "get_templates_by_capability",
    "get_templates_by_tier",
    # Execution Strategies
    "ExecutionStrategy",
    "get_strategy",
    # Anthropic-Inspired Patterns (Patterns 8-10)
    "ToolEnhancedStrategy",
    "PromptCachedSequentialStrategy",
    "DelegationChainStrategy",
    # Meta-Orchestrator & Types
    "MetaOrchestrator",
    "ExecutionPlan",
    "CompositionPattern",
    "TaskComplexity",
    "TaskDomain",
    "TaskRequirements",
]
