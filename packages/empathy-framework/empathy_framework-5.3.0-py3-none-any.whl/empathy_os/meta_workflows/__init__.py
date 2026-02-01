"""Meta-workflow system for dynamic agent team generation.

This package provides:
- Socratic form engine for requirements gathering
- Dynamic agent generation from templates
- Pattern learning from historical executions
- Template registry for reusable workflows

Created: 2026-01-17
Version: 1.0.0 (experimental)
"""

from empathy_os.meta_workflows.agent_creator import DynamicAgentCreator
from empathy_os.meta_workflows.form_engine import SocraticFormEngine
from empathy_os.meta_workflows.intent_detector import (
    IntentDetector,
    IntentMatch,
    auto_detect_template,
    detect_and_suggest,
)
from empathy_os.meta_workflows.models import (
    AgentCompositionRule,
    AgentExecutionResult,
    AgentSpec,
    FormQuestion,
    FormResponse,
    FormSchema,
    MetaWorkflowResult,
    MetaWorkflowTemplate,
    PatternInsight,
    QuestionType,
    TierStrategy,
)
from empathy_os.meta_workflows.pattern_learner import PatternLearner
from empathy_os.meta_workflows.template_registry import TemplateRegistry
from empathy_os.meta_workflows.workflow import (
    MetaWorkflow,
    list_execution_results,
    load_execution_result,
)

__version__ = "1.0.0"

__all__ = [
    # Enums
    "QuestionType",
    "TierStrategy",
    # Form components
    "FormQuestion",
    "FormSchema",
    "FormResponse",
    "SocraticFormEngine",
    # Agent components
    "AgentCompositionRule",
    "AgentSpec",
    "AgentExecutionResult",
    "DynamicAgentCreator",
    # Meta-workflow components
    "MetaWorkflowTemplate",
    "MetaWorkflowResult",
    "TemplateRegistry",
    "MetaWorkflow",
    # Helpers
    "list_execution_results",
    "load_execution_result",
    # Analytics
    "PatternInsight",
    "PatternLearner",
    # Intent detection
    "IntentDetector",
    "IntentMatch",
    "auto_detect_template",
    "detect_and_suggest",
]
