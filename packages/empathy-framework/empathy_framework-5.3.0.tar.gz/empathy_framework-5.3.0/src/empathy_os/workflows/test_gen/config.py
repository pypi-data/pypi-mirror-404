"""Test Generation Configuration.

Default patterns and step configurations for test generation workflow.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

from ..step_config import WorkflowStepConfig

# =============================================================================
# Default Configuration
# =============================================================================

# Directories to skip during file scanning (configurable via input_data["skip_patterns"])
DEFAULT_SKIP_PATTERNS = [
    # Version control
    ".git",
    ".hg",
    ".svn",
    # Dependencies
    "node_modules",
    "bower_components",
    "vendor",
    # Python caches
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".hypothesis",
    # Virtual environments
    "venv",
    ".venv",
    "env",
    ".env",
    "virtualenv",
    ".virtualenv",
    # Build tools
    ".tox",
    ".nox",
    # Build outputs
    "build",
    "dist",
    "eggs",
    ".eggs",
    "site-packages",
    # IDE
    ".idea",
    ".vscode",
    # Framework-specific
    "migrations",
    "alembic",
    # Documentation
    "_build",
    "docs/_build",
]

# Define step configurations for executor-based execution
TEST_GEN_STEPS = {
    "identify": WorkflowStepConfig(
        name="identify",
        task_type="triage",  # Cheap tier task
        tier_hint="cheap",
        description="Identify files needing tests",
        max_tokens=2000,
    ),
    "analyze": WorkflowStepConfig(
        name="analyze",
        task_type="code_analysis",  # Capable tier task
        tier_hint="capable",
        description="Analyze code structure for test generation",
        max_tokens=3000,
    ),
    "generate": WorkflowStepConfig(
        name="generate",
        task_type="code_generation",  # Capable tier task
        tier_hint="capable",
        description="Generate test cases",
        max_tokens=4000,
    ),
    "review": WorkflowStepConfig(
        name="review",
        task_type="final_review",  # Premium tier task
        tier_hint="premium",
        description="Review and improve generated test suite",
        max_tokens=3000,
    ),
}
