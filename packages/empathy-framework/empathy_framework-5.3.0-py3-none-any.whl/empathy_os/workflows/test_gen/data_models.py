"""Test Generation Data Models.

Dataclass definitions for function and class signatures.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

from dataclasses import dataclass, field


@dataclass
class FunctionSignature:
    """Detailed function analysis for test generation."""

    name: str
    params: list[tuple[str, str, str | None]]  # (name, type_hint, default)
    return_type: str | None
    is_async: bool
    raises: set[str]
    has_side_effects: bool
    docstring: str | None
    complexity: int = 1  # Rough complexity estimate
    decorators: list[str] = field(default_factory=list)


@dataclass
class ClassSignature:
    """Detailed class analysis for test generation."""

    name: str
    methods: list[FunctionSignature]
    init_params: list[tuple[str, str, str | None]]  # Constructor params
    base_classes: list[str]
    docstring: str | None
    is_enum: bool = False  # True if class inherits from Enum
    is_dataclass: bool = False  # True if class has @dataclass decorator
    required_init_params: int = 0  # Number of params without defaults
