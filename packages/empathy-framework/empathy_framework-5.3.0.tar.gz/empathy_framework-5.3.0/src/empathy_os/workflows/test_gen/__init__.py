"""Test Generation Workflow Package.

Generates tests targeting areas with historical bugs and low coverage.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

# Core workflow
# AST analyzer
from .ast_analyzer import ASTFunctionAnalyzer

# Configuration
from .config import DEFAULT_SKIP_PATTERNS, TEST_GEN_STEPS

# Data models
from .data_models import ClassSignature, FunctionSignature

# Report formatter
from .report_formatter import format_test_gen_report

# Test generation templates
from .test_templates import (
    generate_test_cases_for_params,
    generate_test_for_class,
    generate_test_for_function,
    get_param_test_values,
    get_type_assertion,
)
from .workflow import TestGenerationWorkflow, main

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
