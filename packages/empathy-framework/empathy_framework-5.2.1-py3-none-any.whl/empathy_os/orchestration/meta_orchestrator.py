"""Meta-orchestrator for intelligent agent composition.

This module implements the core orchestration logic that analyzes tasks,
selects appropriate agents, and chooses composition patterns.

Security:
    - All inputs validated before processing
    - No eval() or exec() usage
    - Agent selection based on whitelisted templates

Example:
    >>> orchestrator = MetaOrchestrator()
    >>> plan = orchestrator.analyze_and_compose(
    ...     task="Boost test coverage to 90%",
    ...     context={"current_coverage": 75}
    ... )
    >>> print(plan.strategy)
    sequential
    >>> print([a.role for a in plan.agents])
    ['Test Coverage Expert', 'Test Generation Specialist', 'Quality Assurance Validator']
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .agent_templates import AgentTemplate, get_template, get_templates_by_capability

logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    """Task complexity classification."""

    SIMPLE = "simple"  # Single agent, straightforward
    MODERATE = "moderate"  # 2-3 agents, some coordination
    COMPLEX = "complex"  # 4+ agents, multi-phase execution


class TaskDomain(Enum):
    """Task domain classification."""

    TESTING = "testing"
    SECURITY = "security"
    CODE_QUALITY = "code_quality"
    DOCUMENTATION = "documentation"
    PERFORMANCE = "performance"
    ARCHITECTURE = "architecture"
    REFACTORING = "refactoring"
    GENERAL = "general"


class CompositionPattern(Enum):
    """Available composition patterns (grammar rules)."""

    # Original 7 patterns
    SEQUENTIAL = "sequential"  # A → B → C
    PARALLEL = "parallel"  # A || B || C
    DEBATE = "debate"  # A ⇄ B ⇄ C → Synthesis
    TEACHING = "teaching"  # Junior → Expert validation
    REFINEMENT = "refinement"  # Draft → Review → Polish
    ADAPTIVE = "adaptive"  # Classifier → Specialist
    CONDITIONAL = "conditional"  # If-then-else routing

    # Anthropic-inspired patterns (Patterns 8-10)
    TOOL_ENHANCED = "tool_enhanced"  # Single agent with tools
    PROMPT_CACHED_SEQUENTIAL = "prompt_cached_sequential"  # Shared cached context
    DELEGATION_CHAIN = "delegation_chain"  # Hierarchical delegation (≤3 levels)


@dataclass
class TaskRequirements:
    """Extracted requirements from task analysis.

    Attributes:
        complexity: Task complexity level
        domain: Primary task domain
        capabilities_needed: List of capabilities required
        parallelizable: Whether task can be parallelized
        quality_gates: Quality thresholds to enforce
        context: Additional context for customization
    """

    complexity: TaskComplexity
    domain: TaskDomain
    capabilities_needed: list[str]
    parallelizable: bool = False
    quality_gates: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionPlan:
    """Plan for agent execution.

    Attributes:
        agents: List of agents to execute
        strategy: Composition pattern to use
        quality_gates: Quality thresholds to enforce
        estimated_cost: Estimated execution cost
        estimated_duration: Estimated time in seconds
    """

    agents: list[AgentTemplate]
    strategy: CompositionPattern
    quality_gates: dict[str, Any] = field(default_factory=dict)
    estimated_cost: float = 0.0
    estimated_duration: int = 0


class MetaOrchestrator:
    """Intelligent task analyzer and agent composition engine.

    The meta-orchestrator analyzes tasks to determine requirements,
    selects appropriate agents, and chooses optimal composition patterns.

    Example:
        >>> orchestrator = MetaOrchestrator()
        >>> plan = orchestrator.analyze_and_compose(
        ...     task="Prepare for v3.12.0 release",
        ...     context={"version": "3.12.0"}
        ... )
    """

    # Keyword patterns for task analysis
    COMPLEXITY_KEYWORDS = {
        TaskComplexity.SIMPLE: [
            "format",
            "lint",
            "check",
            "validate",
            "document",
        ],
        TaskComplexity.MODERATE: [
            "improve",
            "refactor",
            "optimize",
            "test",
            "review",
        ],
        TaskComplexity.COMPLEX: [
            "release",
            "migrate",
            "redesign",
            "architecture",
            "prepare",
        ],
    }

    DOMAIN_KEYWORDS = {
        TaskDomain.TESTING: [
            "test",
            "coverage",
            "pytest",
            "unit test",
            "integration test",
        ],
        TaskDomain.SECURITY: [
            "security",
            "vulnerability",
            "audit",
            "penetration",
            "threat",
        ],
        TaskDomain.CODE_QUALITY: [
            "quality",
            "code review",
            "lint",
            "best practices",
            "maintainability",
        ],
        TaskDomain.DOCUMENTATION: [
            "docs",
            "documentation",
            "readme",
            "guide",
            "tutorial",
        ],
        TaskDomain.PERFORMANCE: [
            "performance",
            "optimize",
            "speed",
            "benchmark",
            "profile",
        ],
        TaskDomain.ARCHITECTURE: [
            "architecture",
            "design",
            "structure",
            "pattern",
            "dependency",
        ],
        TaskDomain.REFACTORING: [
            "refactor",
            "cleanup",
            "simplify",
            "restructure",
            "debt",
        ],
    }

    # Capability mapping by domain
    DOMAIN_CAPABILITIES = {
        TaskDomain.TESTING: [
            "analyze_gaps",
            "suggest_tests",
            "validate_coverage",
        ],
        TaskDomain.SECURITY: [
            "vulnerability_scan",
            "threat_modeling",
            "compliance_check",
        ],
        TaskDomain.CODE_QUALITY: [
            "code_review",
            "quality_assessment",
            "best_practices_check",
        ],
        TaskDomain.DOCUMENTATION: [
            "generate_docs",
            "check_completeness",
            "update_examples",
        ],
        TaskDomain.PERFORMANCE: [
            "profile_code",
            "identify_bottlenecks",
            "suggest_optimizations",
        ],
        TaskDomain.ARCHITECTURE: [
            "analyze_architecture",
            "identify_patterns",
            "suggest_improvements",
        ],
        TaskDomain.REFACTORING: [
            "identify_code_smells",
            "suggest_refactorings",
            "validate_changes",
        ],
    }

    def __init__(self):
        """Initialize meta-orchestrator."""
        logger.info("MetaOrchestrator initialized")

    def analyze_task(self, task: str, context: dict[str, Any] | None = None) -> TaskRequirements:
        """Analyze task to extract requirements (public wrapper for testing).

        Args:
            task: Task description (e.g., "Boost test coverage to 90%")
            context: Optional context dictionary

        Returns:
            TaskRequirements with extracted information

        Raises:
            ValueError: If task is invalid

        Example:
            >>> orchestrator = MetaOrchestrator()
            >>> requirements = orchestrator.analyze_task(
            ...     task="Improve test coverage",
            ...     context={"current_coverage": 75}
            ... )
            >>> print(requirements.domain)
            TaskDomain.TESTING
        """
        if not task or not isinstance(task, str):
            raise ValueError("task must be a non-empty string")

        context = context or {}
        return self._analyze_task(task, context)

    def create_execution_plan(
        self,
        requirements: TaskRequirements,
        agents: list[AgentTemplate],
        strategy: CompositionPattern,
    ) -> ExecutionPlan:
        """Create execution plan from components (extracted for testing).

        Args:
            requirements: Task requirements with quality gates
            agents: Selected agents for execution
            strategy: Composition pattern to use

        Returns:
            ExecutionPlan with all components configured

        Example:
            >>> orchestrator = MetaOrchestrator()
            >>> requirements = TaskRequirements(
            ...     complexity=TaskComplexity.MODERATE,
            ...     domain=TaskDomain.TESTING,
            ...     capabilities_needed=["analyze_gaps"],
            ...     quality_gates={"min_coverage": 80}
            ... )
            >>> agents = [get_template("test_coverage_analyzer")]
            >>> strategy = CompositionPattern.SEQUENTIAL
            >>> plan = orchestrator.create_execution_plan(requirements, agents, strategy)
            >>> print(plan.strategy)
            CompositionPattern.SEQUENTIAL
        """
        return ExecutionPlan(
            agents=agents,
            strategy=strategy,
            quality_gates=requirements.quality_gates,
            estimated_cost=self._estimate_cost(agents),
            estimated_duration=self._estimate_duration(agents, strategy),
        )

    def analyze_and_compose(
        self, task: str, context: dict[str, Any] | None = None, interactive: bool = False
    ) -> ExecutionPlan:
        """Analyze task and create execution plan.

        This is the main entry point for the meta-orchestrator.

        Args:
            task: Task description (e.g., "Boost test coverage to 90%")
            context: Optional context dictionary
            interactive: If True, prompts user for low-confidence cases (default: False)

        Returns:
            ExecutionPlan with agents and strategy

        Raises:
            ValueError: If task is invalid

        Example:
            >>> orchestrator = MetaOrchestrator()
            >>> plan = orchestrator.analyze_and_compose(
            ...     task="Improve test coverage",
            ...     context={"current_coverage": 75}
            ... )
        """
        if not task or not isinstance(task, str):
            raise ValueError("task must be a non-empty string")

        context = context or {}

        # Use interactive mode if requested
        if interactive:
            return self.analyze_and_compose_interactive(task, context)

        logger.info(f"Analyzing task: {task}")

        # Step 1: Analyze task requirements
        requirements = self._analyze_task(task, context)
        logger.info(
            f"Task analysis: complexity={requirements.complexity.value}, "
            f"domain={requirements.domain.value}, "
            f"capabilities={requirements.capabilities_needed}"
        )

        # Step 2: Select appropriate agents
        agents = self._select_agents(requirements)
        logger.info(f"Selected {len(agents)} agents: {[a.id for a in agents]}")

        # Step 3: Choose composition pattern
        strategy = self._choose_composition_pattern(requirements, agents)
        logger.info(f"Selected strategy: {strategy.value}")

        # Step 4: Create execution plan (using extracted public method)
        plan = self.create_execution_plan(requirements, agents, strategy)

        return plan

    def analyze_and_compose_interactive(
        self, task: str, context: dict[str, Any] | None = None
    ) -> ExecutionPlan:
        """Analyze task with user confirmation for ambiguous cases.

        This method uses confidence scoring to determine when to ask the user
        for input. High-confidence selections proceed automatically, while
        low-confidence cases prompt the user to choose.

        Args:
            task: Task description
            context: Optional context dictionary

        Returns:
            ExecutionPlan with agents and strategy

        Raises:
            ValueError: If task is invalid
            ImportError: If AskUserQuestion tool is not available

        Example:
            >>> orchestrator = MetaOrchestrator()
            >>> plan = orchestrator.analyze_and_compose_interactive(
            ...     task="Complex architectural redesign",
            ...     context={}
            ... )
            # User may be prompted to choose approach if confidence is low
        """
        if not task or not isinstance(task, str):
            raise ValueError("task must be a non-empty string")

        context = context or {}
        logger.info(f"Analyzing task interactively: {task}")

        # Step 1: Analyze task requirements
        requirements = self._analyze_task(task, context)
        logger.info(
            f"Task analysis: complexity={requirements.complexity.value}, "
            f"domain={requirements.domain.value}"
        )

        # Step 2: Select agents
        agents = self._select_agents(requirements)
        logger.info(f"Selected {len(agents)} agents: {[a.id for a in agents]}")

        # Step 3: Choose pattern
        recommended_pattern = self._choose_composition_pattern(requirements, agents)
        logger.info(f"Recommended strategy: {recommended_pattern.value}")

        # Step 4: Calculate confidence in recommendation
        confidence = self._calculate_confidence(requirements, agents, recommended_pattern)
        logger.info(f"Confidence score: {confidence:.2f}")

        # Step 5: Branch based on confidence
        if confidence >= 0.8:
            # High confidence → automatic execution
            logger.info("High confidence - proceeding automatically")
            return self.create_execution_plan(requirements, agents, recommended_pattern)

        else:
            # Low confidence → ask user
            logger.info("Low confidence - prompting user for choice")
            return self._prompt_user_for_approach(
                requirements, agents, recommended_pattern, confidence
            )

    def _calculate_confidence(
        self,
        requirements: TaskRequirements,
        agents: list[AgentTemplate],
        pattern: CompositionPattern,
    ) -> float:
        """Calculate confidence in automatic pattern selection.

        Confidence scoring considers:
        - Domain clarity (GENERAL domain reduces confidence)
        - Agent count (many agents = complex coordination)
        - Task complexity (complex tasks have multiple valid approaches)
        - Pattern specificity (Anthropic patterns have clear heuristics)

        Args:
            requirements: Task requirements
            agents: Selected agents
            pattern: Recommended composition pattern

        Returns:
            Confidence score between 0.0 and 1.0

        Example:
            >>> confidence = orchestrator._calculate_confidence(
            ...     requirements=TaskRequirements(
            ...         complexity=TaskComplexity.SIMPLE,
            ...         domain=TaskDomain.TESTING,
            ...         capabilities_needed=["analyze_gaps"]
            ...     ),
            ...     agents=[test_agent],
            ...     pattern=CompositionPattern.SEQUENTIAL
            ... )
            >>> confidence >= 0.8  # High confidence for simple, clear task
            True
        """
        confidence = 1.0

        # Reduce confidence for ambiguous cases
        if requirements.domain == TaskDomain.GENERAL:
            confidence *= 0.7  # Generic tasks are less clear

        if len(agents) > 5:
            confidence *= 0.8  # Many agents → complex coordination

        if requirements.complexity == TaskComplexity.COMPLEX:
            confidence *= 0.85  # Complex → multiple valid approaches

        # Increase confidence for clear patterns
        if pattern in [
            CompositionPattern.TOOL_ENHANCED,
            CompositionPattern.DELEGATION_CHAIN,
            CompositionPattern.PROMPT_CACHED_SEQUENTIAL,
        ]:
            confidence *= 1.1  # New Anthropic patterns have clear heuristics

        # Specific domain patterns also get confidence boost
        if pattern in [
            CompositionPattern.TEACHING,
            CompositionPattern.REFINEMENT,
        ] and requirements.domain in [TaskDomain.DOCUMENTATION, TaskDomain.REFACTORING]:
            confidence *= 1.05  # Domain-specific pattern match

        return min(confidence, 1.0)

    def _prompt_user_for_approach(
        self,
        requirements: TaskRequirements,
        agents: list[AgentTemplate],
        recommended_pattern: CompositionPattern,
        confidence: float,
    ) -> ExecutionPlan:
        """Prompt user to choose approach when confidence is low.

        Presents three options:
        1. Use recommended pattern (with confidence score)
        2. Customize team composition
        3. Show all patterns and choose

        Args:
            requirements: Task requirements
            agents: Selected agents
            recommended_pattern: Recommended pattern
            confidence: Confidence score (0.0-1.0)

        Returns:
            ExecutionPlan based on user choice

        Raises:
            ImportError: If AskUserQuestion tool not available
        """
        try:
            # Import here to avoid circular dependency and allow graceful degradation
            from empathy_os.tools import AskUserQuestion
        except ImportError as e:
            logger.warning(f"AskUserQuestion not available: {e}")
            logger.info("Falling back to automatic selection")
            return self.create_execution_plan(requirements, agents, recommended_pattern)

        # Format agent list for display
        agent_summary = ", ".join([a.role for a in agents])

        # Ask user for approach
        response = AskUserQuestion(
            questions=[
                {
                    "header": "Approach",
                    "question": "How would you like to create the agent team?",
                    "multiSelect": False,
                    "options": [
                        {
                            "label": f"Use recommended: {recommended_pattern.value} (Recommended)",
                            "description": f"Auto-selected based on task analysis. "
                            f"{len(agents)} agents: {agent_summary}. "
                            f"Confidence: {confidence:.0%}",
                        },
                        {
                            "label": "Customize team composition",
                            "description": "Choose specific agents and pattern manually",
                        },
                        {
                            "label": "Show all 10 patterns",
                            "description": "Learn about patterns and select one",
                        },
                    ],
                }
            ]
        )

        # Handle user response
        user_choice = response.get("Approach", "")

        if "Use recommended" in user_choice:
            logger.info("User accepted recommended approach")
            return self.create_execution_plan(requirements, agents, recommended_pattern)

        elif "Customize" in user_choice:
            logger.info("User chose to customize team")
            return self._interactive_team_builder(requirements, agents, recommended_pattern)

        else:  # Show patterns
            logger.info("User chose to explore patterns")
            return self._pattern_chooser_wizard(requirements, agents)

    def _interactive_team_builder(
        self,
        requirements: TaskRequirements,
        suggested_agents: list[AgentTemplate],
        suggested_pattern: CompositionPattern,
    ) -> ExecutionPlan:
        """Interactive team builder for manual customization.

        Allows user to:
        1. Review suggested agents and modify selection
        2. Choose composition pattern
        3. Configure quality gates

        Args:
            requirements: Task requirements
            suggested_agents: Auto-selected agents
            suggested_pattern: Auto-selected pattern

        Returns:
            ExecutionPlan with user-customized configuration
        """
        try:
            from empathy_os.tools import AskUserQuestion
        except ImportError:
            logger.warning("AskUserQuestion not available, using defaults")
            return self.create_execution_plan(requirements, suggested_agents, suggested_pattern)

        # Step 1: Agent selection
        agent_response = AskUserQuestion(
            questions=[
                {
                    "header": "Agents",
                    "question": "Which agents should be included in the team?",
                    "multiSelect": True,
                    "options": [
                        {
                            "label": agent.role,
                            "description": f"{agent.id} - {', '.join(agent.capabilities[:3])}",
                        }
                        for agent in suggested_agents
                    ],
                }
            ]
        )

        # Filter agents based on user selection
        selected_agent_roles = agent_response.get("Agents", [])
        if not isinstance(selected_agent_roles, list):
            selected_agent_roles = [selected_agent_roles]

        selected_agents = [a for a in suggested_agents if a.role in selected_agent_roles]
        if not selected_agents:
            # User deselected all - use defaults
            selected_agents = suggested_agents

        # Step 2: Pattern selection
        pattern_response = AskUserQuestion(
            questions=[
                {
                    "header": "Pattern",
                    "question": "Which composition pattern should be used?",
                    "multiSelect": False,
                    "options": [
                        {
                            "label": f"{suggested_pattern.value} (Recommended)",
                            "description": self._get_pattern_description(suggested_pattern),
                        },
                        {
                            "label": "sequential",
                            "description": "Execute agents one after another (A → B → C)",
                        },
                        {
                            "label": "parallel",
                            "description": "Execute agents simultaneously (A || B || C)",
                        },
                        {
                            "label": "tool_enhanced",
                            "description": "Single agent with comprehensive tool access",
                        },
                    ],
                }
            ]
        )

        # Parse pattern choice
        pattern_choice = pattern_response.get("Pattern", suggested_pattern.value)
        if "(Recommended)" in pattern_choice:
            selected_pattern = suggested_pattern
        else:
            # Extract pattern name
            pattern_name = pattern_choice.split()[0]
            try:
                selected_pattern = CompositionPattern(pattern_name)
            except ValueError:
                logger.warning(f"Invalid pattern: {pattern_name}, using suggested")
                selected_pattern = suggested_pattern

        # Create execution plan with user selections
        return self.create_execution_plan(requirements, selected_agents, selected_pattern)

    def _pattern_chooser_wizard(
        self,
        requirements: TaskRequirements,
        suggested_agents: list[AgentTemplate],
    ) -> ExecutionPlan:
        """Interactive pattern chooser with educational previews.

        Shows all 10 composition patterns with:
        - Description and when to use
        - Visual preview of agent flow
        - Estimated cost and duration
        - Examples of similar tasks

        Args:
            requirements: Task requirements
            suggested_agents: Auto-selected agents

        Returns:
            ExecutionPlan with user-selected pattern
        """
        try:
            from empathy_os.tools import AskUserQuestion
        except ImportError:
            logger.warning("AskUserQuestion not available, using defaults")
            suggested_pattern = self._choose_composition_pattern(requirements, suggested_agents)
            return self.create_execution_plan(
                requirements, suggested_agents, suggested_pattern
            )

        # Present all patterns with descriptions
        pattern_response = AskUserQuestion(
            questions=[
                {
                    "header": "Pattern",
                    "question": "Choose a composition pattern (with preview):",
                    "multiSelect": False,
                    "options": [
                        {
                            "label": "sequential",
                            "description": "A → B → C | Step-by-step pipeline | "
                            "Example: Parse → Analyze → Report",
                        },
                        {
                            "label": "parallel",
                            "description": "A || B || C | Independent tasks | "
                            "Example: Security + Quality + Performance audits",
                        },
                        {
                            "label": "debate",
                            "description": "A ⇄ B ⇄ C → Synthesis | Multiple perspectives | "
                            "Example: 3 reviewers discuss approach",
                        },
                        {
                            "label": "teaching",
                            "description": "Junior → Expert validation | Draft + review | "
                            "Example: Cheap model drafts, expert validates",
                        },
                        {
                            "label": "refinement",
                            "description": "Draft → Review → Polish | Iterative improvement | "
                            "Example: Code → Review → Refine",
                        },
                        {
                            "label": "adaptive",
                            "description": "Classifier → Specialist | Dynamic routing | "
                            "Example: Analyze task type → Route to expert",
                        },
                        {
                            "label": "tool_enhanced (NEW)",
                            "description": "Single agent + tools | Most efficient | "
                            "Example: File reader with analysis tools",
                        },
                        {
                            "label": "prompt_cached_sequential (NEW)",
                            "description": "Shared large context | Cost-optimized | "
                            "Example: 3 agents using same codebase docs",
                        },
                        {
                            "label": "delegation_chain (NEW)",
                            "description": "Coordinator → Specialists | Hierarchical | "
                            "Example: Task planner delegates to architects",
                        },
                    ],
                }
            ]
        )

        # Parse pattern choice
        pattern_choice = pattern_response.get("Pattern", "sequential")
        pattern_name = pattern_choice.split()[0]  # Extract name before any annotations

        try:
            selected_pattern = CompositionPattern(pattern_name)
        except ValueError:
            logger.warning(f"Invalid pattern: {pattern_name}, using sequential")
            selected_pattern = CompositionPattern.SEQUENTIAL

        logger.info(f"User selected pattern: {selected_pattern.value}")

        # Create execution plan with user-selected pattern
        return self.create_execution_plan(requirements, suggested_agents, selected_pattern)

    def _get_pattern_description(self, pattern: CompositionPattern) -> str:
        """Get human-readable description of a pattern.

        Args:
            pattern: Composition pattern

        Returns:
            Description string
        """
        descriptions = {
            CompositionPattern.SEQUENTIAL: "Execute agents one after another (A → B → C)",
            CompositionPattern.PARALLEL: "Execute agents simultaneously (A || B || C)",
            CompositionPattern.DEBATE: "Multiple agents discuss and synthesize (A ⇄ B → Result)",
            CompositionPattern.TEACHING: "Junior agent with expert validation (Draft → Review)",
            CompositionPattern.REFINEMENT: "Iterative improvement (Draft → Review → Polish)",
            CompositionPattern.ADAPTIVE: "Dynamic routing based on classification",
            CompositionPattern.CONDITIONAL: "If-then-else branching logic",
            CompositionPattern.TOOL_ENHANCED: "Single agent with comprehensive tool access",
            CompositionPattern.PROMPT_CACHED_SEQUENTIAL: "Sequential with shared cached context",
            CompositionPattern.DELEGATION_CHAIN: "Hierarchical coordinator → specialists",
        }
        return descriptions.get(pattern, "Custom composition pattern")

    def _analyze_task(self, task: str, context: dict[str, Any]) -> TaskRequirements:
        """Analyze task to extract requirements.

        Args:
            task: Task description
            context: Context dictionary

        Returns:
            TaskRequirements with extracted information
        """
        task_lower = task.lower()

        # Determine complexity
        complexity = self._classify_complexity(task_lower)

        # Determine domain
        domain = self._classify_domain(task_lower)

        # Extract needed capabilities
        capabilities = self._extract_capabilities(domain, context)

        # Determine if parallelizable
        parallelizable = self._is_parallelizable(task_lower, complexity)

        # Extract quality gates from context
        quality_gates = context.get("quality_gates", {})

        return TaskRequirements(
            complexity=complexity,
            domain=domain,
            capabilities_needed=capabilities,
            parallelizable=parallelizable,
            quality_gates=quality_gates,
            context=context,
        )

    def _classify_complexity(self, task_lower: str) -> TaskComplexity:
        """Classify task complexity based on keywords.

        Args:
            task_lower: Lowercase task description

        Returns:
            TaskComplexity classification
        """
        # Check for complex keywords first (most specific)
        for keyword in self.COMPLEXITY_KEYWORDS[TaskComplexity.COMPLEX]:
            if keyword in task_lower:
                return TaskComplexity.COMPLEX

        # Check for moderate keywords
        for keyword in self.COMPLEXITY_KEYWORDS[TaskComplexity.MODERATE]:
            if keyword in task_lower:
                return TaskComplexity.MODERATE

        # Check for simple keywords
        for keyword in self.COMPLEXITY_KEYWORDS[TaskComplexity.SIMPLE]:
            if keyword in task_lower:
                return TaskComplexity.SIMPLE

        # Default to moderate if no keywords match
        return TaskComplexity.MODERATE

    def _classify_domain(self, task_lower: str) -> TaskDomain:
        """Classify task domain based on keywords.

        Args:
            task_lower: Lowercase task description

        Returns:
            TaskDomain classification
        """
        # Score each domain based on keyword matches
        domain_scores: dict[TaskDomain, int] = dict.fromkeys(TaskDomain, 0)

        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            for keyword in keywords:
                if keyword in task_lower:
                    domain_scores[domain] += 1

        # Return domain with highest score
        max_score = max(domain_scores.values())
        if max_score > 0:
            for domain, score in domain_scores.items():
                if score == max_score:
                    return domain

        # Default to general if no keywords match
        return TaskDomain.GENERAL

    def _extract_capabilities(self, domain: TaskDomain, context: dict[str, Any]) -> list[str]:
        """Extract needed capabilities based on domain.

        Args:
            domain: Task domain
            context: Context dictionary

        Returns:
            List of capability names
        """
        # Get default capabilities for domain
        capabilities = self.DOMAIN_CAPABILITIES.get(domain, []).copy()

        # Add capabilities from context if provided
        if "capabilities" in context:
            additional = context["capabilities"]
            if isinstance(additional, list):
                capabilities.extend(additional)

        return capabilities

    def _is_parallelizable(self, task_lower: str, complexity: TaskComplexity) -> bool:
        """Determine if task can be parallelized.

        Args:
            task_lower: Lowercase task description
            complexity: Task complexity

        Returns:
            True if task can be parallelized
        """
        # Keywords indicating parallel execution
        parallel_keywords = [
            "release",
            "audit",
            "check",
            "validate",
            "review",
        ]

        # Keywords indicating sequential execution
        sequential_keywords = [
            "migrate",
            "refactor",
            "generate",
            "create",
        ]

        # Check for sequential keywords first (higher precedence)
        for keyword in sequential_keywords:
            if keyword in task_lower:
                return False

        # Check for parallel keywords
        for keyword in parallel_keywords:
            if keyword in task_lower:
                return True

        # Complex tasks often benefit from parallel execution
        return complexity == TaskComplexity.COMPLEX

    def _select_agents(self, requirements: TaskRequirements) -> list[AgentTemplate]:
        """Select appropriate agents based on requirements.

        Args:
            requirements: Task requirements

        Returns:
            List of agent templates

        Raises:
            ValueError: If no agents match requirements
        """
        agents: list[AgentTemplate] = []

        # Select agents based on needed capabilities
        for capability in requirements.capabilities_needed:
            templates = get_templates_by_capability(capability)
            if templates:
                # Pick the first template with this capability
                # In future: could rank by success rate, cost, etc.
                agent = templates[0]
                if agent not in agents:
                    agents.append(agent)

        # If no agents found, use domain-appropriate default
        if not agents:
            agents = self._get_default_agents(requirements.domain)

        if not agents:
            raise ValueError(f"No agents available for domain: {requirements.domain.value}")

        return agents

    def _get_default_agents(self, domain: TaskDomain) -> list[AgentTemplate]:
        """Get default agents for a domain.

        Args:
            domain: Task domain

        Returns:
            List of default agent templates
        """
        defaults = {
            TaskDomain.TESTING: ["test_coverage_analyzer"],
            TaskDomain.SECURITY: ["security_auditor"],
            TaskDomain.CODE_QUALITY: ["code_reviewer"],
            TaskDomain.DOCUMENTATION: ["documentation_writer"],
            TaskDomain.PERFORMANCE: ["performance_optimizer"],
            TaskDomain.ARCHITECTURE: ["architecture_analyst"],
            TaskDomain.REFACTORING: ["refactoring_specialist"],
        }

        template_ids = defaults.get(domain, ["code_reviewer"])
        agents = []
        for template_id in template_ids:
            template = get_template(template_id)
            if template:
                agents.append(template)

        return agents

    def _choose_composition_pattern(
        self, requirements: TaskRequirements, agents: list[AgentTemplate]
    ) -> CompositionPattern:
        """Choose optimal composition pattern.

        Args:
            requirements: Task requirements
            agents: Selected agents

        Returns:
            CompositionPattern to use
        """
        num_agents = len(agents)
        context = requirements.context

        # Anthropic Pattern 8: Tool-Enhanced (single agent + tools preferred)
        if num_agents == 1 and context.get("tools"):
            return CompositionPattern.TOOL_ENHANCED

        # Anthropic Pattern 10: Delegation Chain (hierarchical coordination)
        # Use when: Complex task + coordinator pattern + 2+ specialists
        has_coordinator = any("coordinator" in agent.role.lower() for agent in agents)
        if (
            requirements.complexity == TaskComplexity.COMPLEX
            and has_coordinator
            and num_agents >= 2
        ):
            return CompositionPattern.DELEGATION_CHAIN

        # Anthropic Pattern 9: Prompt-Cached Sequential (large shared context)
        # Use when: 3+ agents need same large context (>2000 tokens)
        large_context = context.get("cached_context") or context.get("shared_knowledge")
        if num_agents >= 3 and large_context and len(str(large_context)) > 2000:
            return CompositionPattern.PROMPT_CACHED_SEQUENTIAL

        # Parallelizable tasks: use parallel strategy (check before single agent)
        if requirements.parallelizable:
            return CompositionPattern.PARALLEL

        # Security/architecture: benefit from multiple perspectives (even with 1 agent)
        if requirements.domain in [TaskDomain.SECURITY, TaskDomain.ARCHITECTURE]:
            return CompositionPattern.PARALLEL

        # Documentation: teaching pattern (cheap → validate → expert if needed)
        if requirements.domain == TaskDomain.DOCUMENTATION:
            return CompositionPattern.TEACHING

        # Refactoring: refinement pattern (identify → refactor → validate)
        if requirements.domain == TaskDomain.REFACTORING:
            return CompositionPattern.REFINEMENT

        # Single agent: sequential (after domain-specific patterns)
        if num_agents == 1:
            return CompositionPattern.SEQUENTIAL

        # Multiple agents with same capability: debate/consensus
        capabilities = [cap for agent in agents for cap in agent.capabilities]
        if len(capabilities) != len(set(capabilities)):
            # Duplicate capabilities detected → debate
            return CompositionPattern.DEBATE

        # Testing domain: typically sequential (analyze → generate → validate)
        if requirements.domain == TaskDomain.TESTING:
            return CompositionPattern.SEQUENTIAL

        # Complex tasks: adaptive routing
        if requirements.complexity == TaskComplexity.COMPLEX:
            return CompositionPattern.ADAPTIVE

        # Default: sequential
        return CompositionPattern.SEQUENTIAL

    def _estimate_cost(self, agents: list[AgentTemplate]) -> float:
        """Estimate execution cost based on agent tiers.

        Args:
            agents: List of agents

        Returns:
            Estimated cost in arbitrary units
        """
        tier_costs = {
            "CHEAP": 1.0,
            "CAPABLE": 3.0,
            "PREMIUM": 10.0,
        }

        total_cost = 0.0
        for agent in agents:
            total_cost += tier_costs.get(agent.tier_preference, 3.0)

        return total_cost

    def _estimate_duration(self, agents: list[AgentTemplate], strategy: CompositionPattern) -> int:
        """Estimate execution duration in seconds.

        Args:
            agents: List of agents
            strategy: Composition pattern

        Returns:
            Estimated duration in seconds
        """
        # Get max timeout from agents
        max_timeout = max(
            (agent.resource_requirements.timeout_seconds for agent in agents),
            default=300,
        )

        # Sequential: sum of timeouts
        if strategy == CompositionPattern.SEQUENTIAL:
            return sum(agent.resource_requirements.timeout_seconds for agent in agents)

        # Parallel: max timeout
        if strategy == CompositionPattern.PARALLEL:
            return max_timeout

        # Debate: multiple rounds, estimate 2x max timeout
        if strategy == CompositionPattern.DEBATE:
            return max_timeout * 2

        # Teaching: initial attempt + possible expert review
        if strategy == CompositionPattern.TEACHING:
            return int(max_timeout * 1.5)

        # Refinement: 3 passes (draft → review → polish)
        if strategy == CompositionPattern.REFINEMENT:
            return max_timeout * 3

        # Adaptive: classification + specialist
        if strategy == CompositionPattern.ADAPTIVE:
            return int(max_timeout * 1.2)

        # Anthropic Pattern 8: Tool-Enhanced (single agent with tools, efficient)
        if strategy == CompositionPattern.TOOL_ENHANCED:
            return max_timeout  # Similar to sequential for single agent

        # Anthropic Pattern 9: Prompt-Cached Sequential (faster with cache hits)
        if strategy == CompositionPattern.PROMPT_CACHED_SEQUENTIAL:
            # Sequential but 20% faster due to cached context reducing token processing
            total = sum(agent.resource_requirements.timeout_seconds for agent in agents)
            return int(total * 0.8)

        # Anthropic Pattern 10: Delegation Chain (coordinator + specialists in sequence)
        if strategy == CompositionPattern.DELEGATION_CHAIN:
            # Coordinator analyzes, then specialists execute (sequential-like)
            return sum(agent.resource_requirements.timeout_seconds for agent in agents)

        # Conditional: branch evaluation + selected path
        if strategy == CompositionPattern.CONDITIONAL:
            return int(max_timeout * 1.1)

        # Default: max timeout
        return max_timeout
