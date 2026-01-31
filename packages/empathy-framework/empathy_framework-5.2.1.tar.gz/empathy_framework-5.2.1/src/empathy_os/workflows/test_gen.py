"""Test Generation Workflow (Backward Compatible Entry Point).

This module maintains backward compatibility by re-exporting all public APIs
from the test_gen package.

For new code, import from the package directly:
    from empathy_os.workflows.test_gen import TestGenerationWorkflow

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

# Re-export all public APIs from the package for backward compatibility
from .test_gen import (
    DEFAULT_SKIP_PATTERNS,
    TEST_GEN_STEPS,
    ASTFunctionAnalyzer,
    ClassSignature,
    FunctionSignature,
    TestGenerationWorkflow,
    format_test_gen_report,
    generate_test_cases_for_params,
    generate_test_for_class,
    generate_test_for_function,
    get_param_test_values,
    get_type_assertion,
    main,
)

__all__ = [
    # Workflow
    "TestGenerationWorkflow",
    "main",
    # Data models
    "FunctionSignature",
    "ClassSignature",
    # AST analyzer
    "ASTFunctionAnalyzer",
    # Configuration
    "DEFAULT_SKIP_PATTERNS",
    "TEST_GEN_STEPS",
    # Test templates
    "generate_test_for_function",
    "generate_test_for_class",
    "generate_test_cases_for_params",
    "get_type_assertion",
    "get_param_test_values",
    # Report formatter
    "format_test_gen_report",
]


if __name__ == "__main__":
    main()
