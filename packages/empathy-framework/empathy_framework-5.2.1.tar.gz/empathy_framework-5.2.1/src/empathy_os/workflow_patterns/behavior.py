"""Behavioral workflow patterns.

Patterns for conditional execution and dynamic behavior.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

from typing import Any

from .core import CodeSection, PatternCategory, WorkflowComplexity, WorkflowPattern


class ConditionalTierPattern(WorkflowPattern):
    """Dynamic tier routing based on complexity or conditions.

    Use for: Cost optimization by downgrading/skipping expensive stages.
    Examples: bug-predict (skip premium if low risk), code-review (conditional architect review).
    """

    id: str = "conditional-tier"
    name: str = "Conditional Tier Routing"
    category: PatternCategory = PatternCategory.BEHAVIOR
    description: str = "Dynamically adjust model tiers based on conditions"
    complexity: WorkflowComplexity = WorkflowComplexity.MODERATE
    use_cases: list[str] = [
        "Cost optimization",
        "Conditional premium tier usage",
        "Complexity-based routing",
    ]
    examples: list[str] = ["bug-predict", "code-review", "pr-review"]
    requires: list[str] = ["multi-stage"]
    risk_weight: float = 3.0

    def generate_code_sections(self, context: dict[str, Any]) -> list[CodeSection]:
        """Generate code for conditional tier routing."""
        threshold_param = context.get("threshold_param", "complexity_threshold")
        threshold_default = context.get("threshold_default", "0.7")
        metric_name = context.get("metric_name", "complexity_score")

        return [
            CodeSection(
                location="init_method",
                code=f"""        self.{threshold_param} = {threshold_param} if {threshold_param} is not None else {threshold_default}
        self._{metric_name}: float = 0.0""",
                priority=1,
            ),
            CodeSection(
                location="methods",
                code=f'''    def should_skip_stage(self, stage_name: str, input_data: Any) -> tuple[bool, str | None]:
        """Conditionally downgrade or skip stages based on {metric_name}.

        Args:
            stage_name: Name of the stage to check
            input_data: Current workflow data

        Returns:
            Tuple of (should_skip, reason)

        """
        # Example: Downgrade premium stage if metric below threshold
        if stage_name == "recommend" or stage_name == "architect_review":
            if self._{metric_name} < self.{threshold_param}:
                # Downgrade to CAPABLE instead of skipping
                self.tier_map[stage_name] = ModelTier.CAPABLE
                logger.info(f"Downgraded {{stage_name}} to CAPABLE ({metric_name}: {{self._{metric_name}:.2f}})")
                return False, None
        return False, None''',
                priority=2,
            ),
        ]


class ConfigDrivenPattern(WorkflowPattern):
    """Load configuration from empathy.config.yml.

    Use for: Configurable thresholds, options, and behavior.
    Examples: bug-predict (risk threshold), health-check (check toggles).
    """

    id: str = "config-driven"
    name: str = "Configuration-Driven Workflow"
    category: PatternCategory = PatternCategory.BEHAVIOR
    description: str = "Loads settings from empathy.config.yml"
    complexity: WorkflowComplexity = WorkflowComplexity.SIMPLE
    use_cases: list[str] = [
        "Configurable thresholds",
        "User-customizable behavior",
        "Environment-specific settings",
    ]
    examples: list[str] = ["bug-predict", "health-check", "security-audit"]
    risk_weight: float = 1.5

    def generate_code_sections(self, context: dict[str, Any]) -> list[CodeSection]:
        """Generate code for configuration loading."""
        workflow_name = context.get("workflow_name", "my-workflow")
        config_key = workflow_name.replace("-", "_")
        config_params = context.get(
            "config_params",
            {
                "threshold": 0.7,
                "enabled": True,
            },
        )

        # Generate defaults dict
        defaults_code = "    defaults = {\n"
        for key, value in config_params.items():
            if isinstance(value, str):
                defaults_code += f'        "{key}": "{value}",\n'
            else:
                defaults_code += f'        "{key}": {value},\n'
        defaults_code += "    }"

        # Generate config loading
        return [
            CodeSection(
                location="imports",
                code="import yaml\nfrom pathlib import Path",
                priority=1,
            ),
            CodeSection(
                location="helper_functions",
                code=f'''def _load_{config_key}_config() -> dict:
    """Load {config_key} configuration from empathy.config.yml.

    Returns:
        Dict with {config_key} settings, or defaults if not found.

    """
{defaults_code}

    config_paths = [
        Path("empathy.config.yml"),
        Path("empathy.config.yaml"),
        Path(".empathy.yml"),
        Path(".empathy.yaml"),
    ]

    for config_path in config_paths:
        if config_path.exists():
            try:
                with open(config_path) as f:
                    config = yaml.safe_load(f)
                    if config and "{config_key}" in config:
                        return {{**defaults, **config["{config_key}"]}}
            except (yaml.YAMLError, OSError):
                pass

    return defaults''',
                priority=1,
            ),
            CodeSection(
                location="init_method",
                code=f"""        # Load configuration
        self._config = _load_{config_key}_config()""",
                priority=1,
            ),
        ]


class CodeScannerPattern(WorkflowPattern):
    """File scanning and analysis capabilities.

    Use for: Code analysis workflows that scan files.
    Examples: bug-predict, security-audit, test-gen.
    """

    id: str = "code-scanner"
    name: str = "Code Scanner"
    category: PatternCategory = PatternCategory.BEHAVIOR
    description: str = "Scan and analyze code files with pattern matching"
    complexity: WorkflowComplexity = WorkflowComplexity.MODERATE
    use_cases: list[str] = [
        "Bug detection",
        "Security scanning",
        "Code analysis",
    ]
    examples: list[str] = ["bug-predict", "security-audit"]
    risk_weight: float = 2.0

    def generate_code_sections(self, context: dict[str, Any]) -> list[CodeSection]:
        """Generate code for file scanning."""
        scan_pattern = context.get("scan_pattern", "*.py")

        return [
            CodeSection(
                location="imports",
                code="import fnmatch\nfrom pathlib import Path",
                priority=1,
            ),
            CodeSection(
                location="helper_functions",
                code=f'''def _should_exclude_file(file_path: str, exclude_patterns: list[str]) -> bool:
    """Check if a file should be excluded based on glob patterns.

    Args:
        file_path: Path to the file
        exclude_patterns: List of glob patterns (e.g., "**/test_*.py")

    Returns:
        True if the file matches any exclusion pattern.

    """
    for pattern in exclude_patterns:
        if "**" in pattern:
            parts = pattern.split("**")
            if len(parts) == 2:
                prefix, suffix = parts
                if prefix and not file_path.startswith(prefix.rstrip("/")):
                    continue
                if suffix and fnmatch.fnmatch(file_path, f"*{{suffix}}"):
                    return True
        elif fnmatch.fnmatch(file_path, pattern) or fnmatch.fnmatch(
            Path(file_path).name,
            pattern,
        ):
            return True
    return False


def _scan_files(
    root_dir: str = ".",
    pattern: str = "{scan_pattern}",
    exclude: list[str] | None = None,
) -> list[Path]:
    """Scan directory for files matching pattern.

    Args:
        root_dir: Root directory to scan
        pattern: Glob pattern for files
        exclude: Exclusion patterns

    Returns:
        List of matching file paths

    """
    exclude = exclude or []
    root = Path(root_dir)
    files = []

    for file_path in root.rglob(pattern):
        if file_path.is_file() and not _should_exclude_file(str(file_path), exclude):
            files.append(file_path)

    return files''',
                priority=1,
            ),
        ]
