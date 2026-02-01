"""Meta-orchestrator for progressive tier escalation decisions.

The MetaOrchestrator is responsible for:
1. Analyzing tier execution results
2. Making escalation decisions
3. Creating specialized agent teams
4. Building XML-enhanced prompts with failure context
5. Detecting stagnation patterns
"""

import logging
from typing import Any

from empathy_os.workflows.progressive.core import EscalationConfig, Tier, TierResult

logger = logging.getLogger(__name__)


class MetaOrchestrator:
    """Meta-agent that orchestrates progressive tier decisions.

    The MetaOrchestrator acts as a higher-level intelligence that:
    - Analyzes tier results objectively
    - Decides when to escalate vs retry
    - Detects stagnation patterns
    - Creates specialized agent teams per tier
    - Builds context-aware prompts

    This separates escalation logic from workflow logic, allowing
    workflows to focus on their domain-specific tasks.

    Example:
        >>> orchestrator = MetaOrchestrator()
        >>> should_esc, reason = orchestrator.should_escalate(
        ...     tier=Tier.CHEAP,
        ...     result=cheap_result,
        ...     attempt=2,
        ...     config=config
        ... )
        >>> if should_esc:
        ...     print(f"Escalating: {reason}")
    """

    def __init__(self) -> None:
        """Initialize meta-orchestrator."""
        self.tier_history: dict[Tier, list[float]] = {
            Tier.CHEAP: [],
            Tier.CAPABLE: [],
            Tier.PREMIUM: [],
        }

    def should_escalate(
        self, tier: Tier, result: TierResult, attempt: int, config: EscalationConfig
    ) -> tuple[bool, str]:
        """Determine if tier should escalate to next tier.

        Multi-criteria decision based on:
        - Quality score vs thresholds
        - Syntax errors
        - Failure rate
        - Attempt count
        - Stagnation detection (for CAPABLE tier)

        Args:
            tier: Current tier
            result: Execution result
            attempt: Attempt number at this tier
            config: Escalation configuration

        Returns:
            Tuple of (should_escalate, reason)

        Example:
            >>> should_esc, reason = orchestrator.should_escalate(
            ...     Tier.CHEAP, result, 2, config
            ... )
            >>> # (True, "Quality score 65 below threshold 70")
        """
        cqs = result.quality_score

        # Track CQS history for stagnation detection
        self.tier_history[tier].append(cqs)

        # Check if we've met minimum attempts
        min_attempts = config.get_min_attempts(tier)
        if attempt < min_attempts:
            return False, f"Only {attempt}/{min_attempts} attempts completed"

        # Tier-specific threshold checks
        if tier == Tier.CHEAP:
            return self._check_cheap_escalation(result, config)
        elif tier == Tier.CAPABLE:
            return self._check_capable_escalation(result, attempt, config)
        else:  # PREMIUM
            # Premium doesn't escalate (highest tier)
            return False, "Premium tier is final"

    def _check_cheap_escalation(
        self, result: TierResult, config: EscalationConfig
    ) -> tuple[bool, str]:
        """Check if cheap tier should escalate to capable.

        Args:
            result: Cheap tier result
            config: Escalation configuration

        Returns:
            Tuple of (should_escalate, reason)
        """
        cqs = result.quality_score
        failure_rate = 1.0 - result.success_rate
        syntax_error_count = len(result.failure_analysis.syntax_errors)

        # Check severity first (critical failures)
        if result.failure_analysis.failure_severity == "CRITICAL":
            return True, "Critical failures detected (consider skipping to Premium)"

        # Check syntax errors (prioritize over CQS)
        if syntax_error_count > config.cheap_to_capable_max_syntax_errors:
            return (
                True,
                f"{syntax_error_count} syntax errors exceeds limit {config.cheap_to_capable_max_syntax_errors}",
            )

        # Check failure rate
        if failure_rate > config.cheap_to_capable_failure_rate:
            return (
                True,
                f"Failure rate {failure_rate:.1%} exceeds threshold {config.cheap_to_capable_failure_rate:.1%}",
            )

        # Check CQS threshold
        if cqs < config.cheap_to_capable_min_cqs:
            return (
                True,
                f"Quality score {cqs:.1f} below threshold {config.cheap_to_capable_min_cqs}",
            )

        # All checks passed, no escalation needed
        return False, f"Quality acceptable (CQS={cqs:.1f})"

    def _check_capable_escalation(
        self, result: TierResult, attempt: int, config: EscalationConfig
    ) -> tuple[bool, str]:
        """Check if capable tier should escalate to premium.

        Includes stagnation detection: if improvement is <5% for 2 consecutive
        attempts, escalate even if quality is borderline acceptable.

        Args:
            result: Capable tier result
            attempt: Attempt number
            config: Escalation configuration

        Returns:
            Tuple of (should_escalate, reason)
        """
        cqs = result.quality_score
        failure_rate = 1.0 - result.success_rate
        syntax_error_count = len(result.failure_analysis.syntax_errors)

        # Check max attempts first
        if attempt >= config.capable_max_attempts:
            return (
                True,
                f"Max attempts ({config.capable_max_attempts}) reached without achieving target quality",
            )

        # Check syntax errors (strict for capable tier)
        if syntax_error_count > config.capable_to_premium_max_syntax_errors:
            return (
                True,
                f"{syntax_error_count} syntax errors exceeds limit {config.capable_to_premium_max_syntax_errors}",
            )

        # Check failure rate
        if failure_rate > config.capable_to_premium_failure_rate:
            return (
                True,
                f"Failure rate {failure_rate:.1%} exceeds threshold {config.capable_to_premium_failure_rate:.1%}",
            )

        # Check stagnation (consecutive runs with <5% improvement)
        # Only check if we have enough history
        if len(self.tier_history[Tier.CAPABLE]) >= config.consecutive_stagnation_limit + 1:
            is_stagnant, stagnation_reason = self._detect_stagnation(
                self.tier_history[Tier.CAPABLE],
                config.improvement_threshold,
                config.consecutive_stagnation_limit,
            )

            if is_stagnant:
                return True, f"Stagnation detected: {stagnation_reason}"

        # Check CQS threshold (after stagnation check)
        if cqs < config.capable_to_premium_min_cqs and attempt >= config.capable_min_attempts:
            return (
                True,
                f"Quality score {cqs:.1f} below threshold {config.capable_to_premium_min_cqs}",
            )

        # No escalation needed
        return False, f"Quality acceptable (CQS={cqs:.1f}), continuing improvement"

    def _detect_stagnation(
        self, cqs_history: list[float], improvement_threshold: float, consecutive_limit: int
    ) -> tuple[bool, str]:
        """Detect if improvement has stagnated.

        Stagnation is defined as N consecutive attempts with <X% improvement.

        Args:
            cqs_history: List of CQS scores (chronological)
            improvement_threshold: Min improvement % to avoid stagnation
            consecutive_limit: Number of consecutive stagnations before escalating

        Returns:
            Tuple of (is_stagnant, reason)

        Example:
            >>> history = [75, 76, 77, 77.5]
            >>> is_stagnant, reason = orchestrator._detect_stagnation(
            ...     history, improvement_threshold=5.0, consecutive_limit=2
            ... )
            >>> # (True, "2 consecutive runs with <5% improvement")
        """
        if len(cqs_history) < consecutive_limit + 1:
            return False, "Insufficient history for stagnation detection"

        # Check last N improvements
        consecutive_stagnations = 0

        for i in range(len(cqs_history) - 1, 0, -1):
            current = cqs_history[i]
            previous = cqs_history[i - 1]

            improvement = current - previous

            if improvement < improvement_threshold:
                consecutive_stagnations += 1

                if consecutive_stagnations >= consecutive_limit:
                    return True, (
                        f"{consecutive_stagnations} consecutive runs with "
                        f"<{improvement_threshold}% improvement"
                    )
            else:
                # Improvement above threshold, reset counter
                break

        return False, "No stagnation detected"

    def build_tier_prompt(
        self, tier: Tier, base_task: str, failure_context: dict[str, Any] | None = None
    ) -> str:
        """Build XML-enhanced prompt with failure context.

        Creates tier-appropriate prompts:
        - CHEAP: Simple, focused prompt
        - CAPABLE: Enhanced with failure analysis from cheap tier
        - PREMIUM: Comprehensive with full escalation context

        Args:
            tier: Which tier this prompt is for
            base_task: Base task description
            failure_context: Context from previous tier (if escalating)

        Returns:
            XML-enhanced prompt string

        Example:
            >>> prompt = orchestrator.build_tier_prompt(
            ...     Tier.CAPABLE,
            ...     "Generate tests for module.py",
            ...     failure_context={"previous_tier": Tier.CHEAP, ...}
            ... )
        """
        if tier == Tier.CHEAP:
            return self._build_cheap_prompt(base_task)
        elif tier == Tier.CAPABLE:
            return self._build_capable_prompt(base_task, failure_context)
        else:  # PREMIUM
            return self._build_premium_prompt(base_task, failure_context)

    def _build_cheap_prompt(self, base_task: str) -> str:
        """Build simple prompt for cheap tier.

        Args:
            base_task: Task description

        Returns:
            XML-enhanced prompt
        """
        return f"""<task>
  <objective>{base_task}</objective>

  <quality_requirements>
    <pass_rate>70%+</pass_rate>
    <coverage>60%+</coverage>
    <syntax>No syntax errors</syntax>
  </quality_requirements>

  <instructions>
    Generate high-quality output that meets the quality requirements.
    Focus on correctness and completeness.
  </instructions>
</task>"""

    def _build_capable_prompt(self, base_task: str, failure_context: dict[str, Any] | None) -> str:
        """Build enhanced prompt for capable tier with failure context.

        Args:
            base_task: Task description
            failure_context: Context from cheap tier

        Returns:
            XML-enhanced prompt with failure analysis
        """
        if not failure_context:
            # No context, use enhanced base prompt
            return f"""<task>
  <objective>{base_task}</objective>

  <quality_requirements>
    <pass_rate>80%+</pass_rate>
    <coverage>70%+</coverage>
    <quality_score>80+</quality_score>
  </quality_requirements>

  <instructions>
    Generate high-quality output with comprehensive coverage.
    Ensure all edge cases are handled correctly.
  </instructions>
</task>"""

        # Extract detailed failure context
        previous_cqs = failure_context.get("previous_cqs", 0)
        reason = failure_context.get("reason", "Quality below threshold")
        failures = failure_context.get("failures", [])
        examples = failure_context.get("examples", [])

        # Analyze failure patterns
        failure_patterns = self.analyze_failure_patterns(failures) if failures else {}

        # Build detailed prompt with failure analysis
        prompt_parts = [
            "<task>",
            f"  <objective>{base_task}</objective>",
            "",
            "  <context_from_previous_tier>",
            "    <tier>cheap</tier>",
            f"    <quality_score>{previous_cqs:.1f}</quality_score>",
            f"    <escalation_reason>{reason}</escalation_reason>",
            "",
        ]

        # Add failure pattern analysis
        if failure_patterns:
            prompt_parts.append("    <failure_analysis>")
            prompt_parts.append(
                f"      <total_failures>{failure_patterns.get('total_failures', 0)}</total_failures>"
            )
            prompt_parts.append("      <patterns>")

            error_types = failure_patterns.get("error_types", {})
            for error_type, count in sorted(error_types.items(), key=lambda x: -x[1]):
                prompt_parts.append(f'        <pattern type="{error_type}" count="{count}" />')

            prompt_parts.append("      </patterns>")

            primary_issue = failure_patterns.get("primary_issue", "unknown")
            prompt_parts.append(f"      <primary_issue>{primary_issue}</primary_issue>")
            prompt_parts.append("    </failure_analysis>")
            prompt_parts.append("")

        # Add concrete failure examples (max 3)
        if examples:
            prompt_parts.append("    <failed_attempts>")
            prompt_parts.append("      <!-- Examples of what the cheap tier produced -->")

            for i, example in enumerate(examples[:3], 1):
                error = example.get("error", "Unknown error")
                code_snippet = example.get("code", "")[:200]  # Limit snippet length

                prompt_parts.append(f'      <example number="{i}">')
                prompt_parts.append(f"        <error>{self._escape_xml(error)}</error>")
                if code_snippet:
                    prompt_parts.append(
                        f"        <code_snippet>{self._escape_xml(code_snippet)}</code_snippet>"
                    )
                prompt_parts.append("      </example>")

            prompt_parts.append("    </failed_attempts>")
            prompt_parts.append("")

        prompt_parts.extend(
            [
                "    <improvement_needed>",
                "      The cheap tier struggled with these items. Analyze the failure",
                "      patterns above and generate improved solutions that specifically",
                "      address these issues.",
                "    </improvement_needed>",
                "  </context_from_previous_tier>",
                "",
                "  <your_task>",
                "    Generate improved output that avoids the specific failure patterns identified above.",
                "",
                "    <quality_requirements>",
                "      <pass_rate>80%+</pass_rate>",
                "      <coverage>70%+</coverage>",
                "      <quality_score>80+</quality_score>",
                "    </quality_requirements>",
                "",
                "    <focus_areas>",
            ]
        )

        # Add targeted focus areas based on failure patterns
        if failure_patterns:
            error_types = failure_patterns.get("error_types", {})
            if "async_errors" in error_types:
                prompt_parts.append(
                    '      <focus area="async">Proper async/await patterns and error handling</focus>'
                )
            if "mocking_errors" in error_types:
                prompt_parts.append(
                    '      <focus area="mocking">Correct mock setup and teardown</focus>'
                )
            if "syntax_errors" in error_types:
                prompt_parts.append(
                    '      <focus area="syntax">Valid Python syntax and imports</focus>'
                )
            if "other_errors" in error_types:
                prompt_parts.append(
                    '      <focus area="general">Edge cases and error handling</focus>'
                )
        else:
            # Default focus areas
            prompt_parts.extend(
                [
                    '      <focus area="syntax">Correct syntax and structure</focus>',
                    '      <focus area="coverage">Comprehensive test coverage</focus>',
                    '      <focus area="errors">Proper error handling</focus>',
                    '      <focus area="edge_cases">Edge case coverage</focus>',
                ]
            )

        prompt_parts.extend(["    </focus_areas>", "  </your_task>", "</task>"])

        return "\n".join(prompt_parts)

    def _build_premium_prompt(self, base_task: str, failure_context: dict[str, Any] | None) -> str:
        """Build comprehensive prompt for premium tier.

        Args:
            base_task: Task description
            failure_context: Context from previous tiers

        Returns:
            XML-enhanced prompt with full escalation context
        """
        if not failure_context:
            return f"""<task>
  <objective>{base_task}</objective>

  <quality_requirements>
    <pass_rate>95%+</pass_rate>
    <coverage>85%+</coverage>
    <quality_score>95+</quality_score>
  </quality_requirements>

  <expert_instructions>
    Apply expert-level techniques to generate exceptional output.
    This is the highest tier - excellence is expected.
  </expert_instructions>
</task>"""

        # Extract comprehensive escalation context
        previous_tier = failure_context.get("previous_tier", Tier.CAPABLE)
        previous_cqs = failure_context.get("previous_cqs", 0)
        reason = failure_context.get("reason", "Previous tier unsuccessful")
        failures = failure_context.get("failures", [])
        examples = failure_context.get("examples", [])

        # Analyze persistent failure patterns
        failure_patterns = self.analyze_failure_patterns(failures) if failures else {}

        prompt_parts = [
            "<task>",
            f"  <objective>{base_task}</objective>",
            "",
            "  <escalation_context>",
            f"    <previous_tier>{previous_tier.value}</previous_tier>",
            f"    <quality_score>{previous_cqs:.1f}</quality_score>",
            f"    <escalation_reason>{self._escape_xml(reason)}</escalation_reason>",
            "",
            "    <progression_analysis>",
            "      This task has been escalated through multiple tiers:",
            "      1. CHEAP tier: Initial attempt with basic models",
            "      2. CAPABLE tier: Enhanced attempt with better models",
            "      3. PREMIUM tier (current): Final expert-level attempt",
            "",
            "      The fact that this reached premium tier indicates a complex",
            "      or difficult case requiring expert-level handling.",
            "    </progression_analysis>",
            "",
        ]

        # Add detailed failure analysis
        if failure_patterns:
            prompt_parts.append("    <persistent_issues>")
            prompt_parts.append(
                f"      <total_failures>{failure_patterns.get('total_failures', 0)}</total_failures>"
            )
            prompt_parts.append("      <failure_patterns>")

            error_types = failure_patterns.get("error_types", {})
            for error_type, count in sorted(error_types.items(), key=lambda x: -x[1]):
                prompt_parts.append(f'        <pattern type="{error_type}" count="{count}">')

                # Add specific guidance per error type
                if error_type == "async_errors":
                    prompt_parts.append(
                        "          <guidance>Use proper async/await patterns, handle timeouts correctly</guidance>"
                    )
                elif error_type == "mocking_errors":
                    prompt_parts.append(
                        "          <guidance>Ensure mocks are properly configured and reset</guidance>"
                    )
                elif error_type == "syntax_errors":
                    prompt_parts.append(
                        "          <guidance>Double-check syntax, imports, and type annotations</guidance>"
                    )

                prompt_parts.append("        </pattern>")

            prompt_parts.append("      </failure_patterns>")
            prompt_parts.append(
                f"      <primary_issue>{failure_patterns.get('primary_issue', 'unknown')}</primary_issue>"
            )
            prompt_parts.append("    </persistent_issues>")
            prompt_parts.append("")

        # Add concrete examples from capable tier
        if examples:
            prompt_parts.append("    <capable_tier_attempts>")
            prompt_parts.append("      <!-- Examples from the capable tier's attempts -->")

            for i, example in enumerate(examples[:3], 1):
                error = example.get("error", "Unknown error")
                code_snippet = example.get("code", "")[:300]  # More context for premium
                quality_score = example.get("quality_score", 0)

                prompt_parts.append(f'      <attempt number="{i}" quality_score="{quality_score}">')
                prompt_parts.append(f"        <error>{self._escape_xml(error)}</error>")
                if code_snippet:
                    prompt_parts.append(
                        f"        <code_snippet>{self._escape_xml(code_snippet)}</code_snippet>"
                    )
                prompt_parts.append("      </attempt>")

            prompt_parts.append("    </capable_tier_attempts>")
            prompt_parts.append("")

        prompt_parts.extend(
            [
                "  </escalation_context>",
                "",
                "  <expert_task>",
                "    <critical_notice>",
                "      You are the FINAL tier in the progressive escalation system.",
                "      Previous tiers (cheap and capable) have attempted this task",
                "      multiple times and could not achieve the required quality.",
                "",
                "      This is the last automated attempt before human review.",
                "      Excellence is not optional - it is required.",
                "    </critical_notice>",
                "",
                "    <expert_techniques>",
                "      Apply sophisticated approaches:",
                "      - Deep analysis of why previous attempts failed",
                "      - Production-grade error handling and edge cases",
                "      - Comprehensive documentation and clarity",
                "      - Defensive programming against subtle bugs",
            ]
        )

        # Add specific techniques based on failure patterns
        if failure_patterns:
            error_types = failure_patterns.get("error_types", {})
            if "async_errors" in error_types:
                prompt_parts.append(
                    "      - Advanced async patterns (asyncio.gather, proper timeouts)"
                )
            if "mocking_errors" in error_types:
                prompt_parts.append(
                    "      - Sophisticated mocking (pytest fixtures, proper lifecycle)"
                )
            if "syntax_errors" in error_types:
                prompt_parts.append("      - Rigorous syntax validation before submission")

        prompt_parts.extend(
            [
                "    </expert_techniques>",
                "",
                "    <quality_requirements>",
                "      <pass_rate>95%+</pass_rate>",
                "      <coverage>85%+</coverage>",
                "      <quality_score>95+</quality_score>",
                "      <zero_syntax_errors>MANDATORY</zero_syntax_errors>",
                "    </quality_requirements>",
                "",
                "    <success_criteria>",
                "      Your implementation must:",
                "      1. Address ALL failure patterns identified above",
                "      2. Achieve exceptional quality scores (95+)",
                "      3. Have zero syntax errors or runtime failures",
                "      4. Include comprehensive edge case coverage",
                "      5. Be production-ready with proper documentation",
                "    </success_criteria>",
                "  </expert_task>",
                "</task>",
            ]
        )

        return "\n".join(prompt_parts)

    def _escape_xml(self, text: str) -> str:
        """Escape special XML characters.

        Args:
            text: Text to escape

        Returns:
            XML-safe text

        Example:
            >>> orchestrator._escape_xml("Error: <missing>")
            'Error: &lt;missing&gt;'
        """
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )

    def create_agent_team(
        self, tier: Tier, failure_context: dict[str, Any] | None = None
    ) -> list[str]:
        """Create specialized agent team for tier.

        Different tiers get different agent compositions:
        - CHEAP: Single generator agent
        - CAPABLE: Generator + Analyzer
        - PREMIUM: Generator + Analyzer + Reviewer

        Args:
            tier: Which tier
            failure_context: Context from previous tier

        Returns:
            List of agent types to create

        Note:
            This returns agent type names. Actual agent creation
            will be implemented when we integrate with the agent system.

        Example:
            >>> agents = orchestrator.create_agent_team(
            ...     Tier.CAPABLE,
            ...     failure_context={...}
            ... )
            >>> # ["generator", "analyzer"]
        """
        if tier == Tier.CHEAP:
            return ["generator"]
        elif tier == Tier.CAPABLE:
            return ["generator", "analyzer"]
        else:  # PREMIUM
            return ["generator", "analyzer", "reviewer"]

    def analyze_failure_patterns(self, failures: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze failure patterns to inform next tier.

        Groups failures by type and identifies common issues.

        Args:
            failures: List of failed items with error details

        Returns:
            Failure pattern analysis

        Example:
            >>> patterns = orchestrator.analyze_failure_patterns(
            ...     [{"error": "SyntaxError: async"}, ...]
            ... )
            >>> # {"async_errors": 15, "mocking_errors": 10, ...}
        """
        # Group by error type
        error_types: dict[str, int] = {}

        for failure in failures:
            error = failure.get("error", "unknown")

            # Categorize error
            if "async" in error.lower() or "await" in error.lower():
                error_types["async_errors"] = error_types.get("async_errors", 0) + 1
            elif "mock" in error.lower():
                error_types["mocking_errors"] = error_types.get("mocking_errors", 0) + 1
            elif "syntax" in error.lower():
                error_types["syntax_errors"] = error_types.get("syntax_errors", 0) + 1
            else:
                error_types["other_errors"] = error_types.get("other_errors", 0) + 1

        return {
            "total_failures": len(failures),
            "error_types": error_types,
            "primary_issue": (
                max(error_types.items(), key=lambda x: x[1])[0] if error_types else "unknown"
            ),
        }
