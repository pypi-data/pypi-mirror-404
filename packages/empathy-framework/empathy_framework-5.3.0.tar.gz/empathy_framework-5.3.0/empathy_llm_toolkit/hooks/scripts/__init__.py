"""Hook Scripts

Pre-built hook scripts for common Empathy Framework events.

Architectural patterns inspired by everything-claude-code by Affaan Mustafa.
See: https://github.com/affaan-m/everything-claude-code (MIT License)
See: ACKNOWLEDGMENTS.md for full attribution.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

from empathy_llm_toolkit.hooks.scripts.evaluate_session import (
    apply_learned_patterns,
    get_learning_summary,
    run_evaluate_session,
)
from empathy_llm_toolkit.hooks.scripts.first_time_init import (
    check_init,
    handle_init_response,
    initialize_project,
)
from empathy_llm_toolkit.hooks.scripts.pre_compact import run_pre_compact
from empathy_llm_toolkit.hooks.scripts.session_end import main as session_end
from empathy_llm_toolkit.hooks.scripts.session_start import main as session_start
from empathy_llm_toolkit.hooks.scripts.suggest_compact import main as suggest_compact

__all__ = [
    "session_start",
    "session_end",
    "suggest_compact",
    "run_pre_compact",
    "run_evaluate_session",
    "get_learning_summary",
    "apply_learned_patterns",
    "check_init",
    "handle_init_response",
    "initialize_project",
]
