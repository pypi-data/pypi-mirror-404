"""Document Generation Workflow (Backward Compatible Entry Point).

This module maintains backward compatibility by re-exporting all public APIs
from the document_gen package.

For new code, import from the package directly:
    from empathy_os.workflows.document_gen import DocumentGenerationWorkflow

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

# Re-export all public APIs from the package for backward compatibility
from .document_gen import (
    DOC_GEN_STEPS,
    TOKEN_COSTS,
    DocumentGenerationWorkflow,
    format_doc_gen_report,
)

__all__ = [
    # Workflow
    "DocumentGenerationWorkflow",
    # Configuration
    "DOC_GEN_STEPS",
    "TOKEN_COSTS",
    # Report formatter
    "format_doc_gen_report",
]
