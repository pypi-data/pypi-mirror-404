"""Base Workflow Class for Multi-Model Pipelines

Provides a framework for creating cost-optimized workflows that
route tasks to the appropriate model tier.

Integration with empathy_os.models:
- Uses unified ModelTier/ModelProvider from empathy_os.models
- Supports LLMExecutor for abstracted LLM calls
- Supports TelemetryBackend for telemetry storage
- WorkflowStepConfig for declarative step definitions

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

from __future__ import annotations

import json
import logging
import sys
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .routing import TierRoutingStrategy
    from .tier_tracking import WorkflowTierTracker

# Load .env file for API keys if python-dotenv is available
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, rely on environment variables

# Import caching infrastructure
from empathy_os.cache import BaseCache
from empathy_os.config import _validate_file_path
from empathy_os.cost_tracker import MODEL_PRICING, CostTracker

# Import unified types from empathy_os.models
from empathy_os.models import (
    ExecutionContext,
    LLMExecutor,
    TaskRoutingRecord,
    TelemetryBackend,
)
from empathy_os.models import ModelProvider as UnifiedModelProvider
from empathy_os.models import ModelTier as UnifiedModelTier

# Import mixins (extracted for maintainability)
from .caching import CachedResponse, CachingMixin

# Import progress tracking
from .progress import (
    RICH_AVAILABLE,
    ProgressCallback,
    ProgressTracker,
    RichProgressReporter,
)
from .telemetry_mixin import TelemetryMixin

# Import telemetry tracking
try:
    from empathy_os.telemetry import UsageTracker

    TELEMETRY_AVAILABLE = True
except ImportError:
    TELEMETRY_AVAILABLE = False
    UsageTracker = None  # type: ignore

if TYPE_CHECKING:
    from .config import WorkflowConfig
    from .step_config import WorkflowStepConfig

logger = logging.getLogger(__name__)

# Default path for workflow run history
WORKFLOW_HISTORY_FILE = ".empathy/workflow_runs.json"


# Local enums for backward compatibility - DEPRECATED
# New code should use empathy_os.models.ModelTier/ModelProvider
class ModelTier(Enum):
    """DEPRECATED: Model tier for cost optimization.

    This enum is deprecated and will be removed in v5.0.
    Use empathy_os.models.ModelTier instead.

    Migration:
        # Old:
        from empathy_os.workflows.base import ModelTier

        # New:
        from empathy_os.models import ModelTier

    Why deprecated:
        - Creates confusion with dual definitions
        - empathy_os.models.ModelTier is the canonical location
        - Simplifies imports and reduces duplication
    """

    CHEAP = "cheap"  # Haiku/GPT-4o-mini - $0.25-1.25/M tokens
    CAPABLE = "capable"  # Sonnet/GPT-4o - $3-15/M tokens
    PREMIUM = "premium"  # Opus/o1 - $15-75/M tokens

    def __init__(self, value: str):
        """Initialize with deprecation warning."""
        # Only warn once per process, not per instance
        import warnings

        # Use self.__class__ instead of ModelTier (class not yet defined during creation)
        if not hasattr(self.__class__, "_deprecation_warned"):
            warnings.warn(
                "workflows.base.ModelTier is deprecated and will be removed in v5.0. "
                "Use empathy_os.models.ModelTier instead. "
                "Update imports: from empathy_os.models import ModelTier",
                DeprecationWarning,
                stacklevel=4,
            )
            self.__class__._deprecation_warned = True

    def to_unified(self) -> UnifiedModelTier:
        """Convert to unified ModelTier from empathy_os.models."""
        return UnifiedModelTier(self.value)


class ModelProvider(Enum):
    """Supported model providers."""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"  # Google Gemini models
    OLLAMA = "ollama"
    HYBRID = "hybrid"  # Mix of best models from different providers
    CUSTOM = "custom"  # User-defined custom models

    def to_unified(self) -> UnifiedModelProvider:
        """Convert to unified ModelProvider from empathy_os.models.

        As of v5.0.0, framework is Claude-native. All providers map to ANTHROPIC.
        """
        # v5.0.0: Framework is Claude-native, only ANTHROPIC supported
        return UnifiedModelProvider.ANTHROPIC


# Import unified MODEL_REGISTRY as single source of truth
# This import is placed here intentionally to avoid circular imports
from empathy_os.models import MODEL_REGISTRY  # noqa: E402


def _build_provider_models() -> dict[ModelProvider, dict[ModelTier, str]]:
    """Build PROVIDER_MODELS from MODEL_REGISTRY.

    This ensures PROVIDER_MODELS stays in sync with the single source of truth.
    """
    result: dict[ModelProvider, dict[ModelTier, str]] = {}

    # Map string provider names to ModelProvider enum
    provider_map = {
        "anthropic": ModelProvider.ANTHROPIC,
        "openai": ModelProvider.OPENAI,
        "google": ModelProvider.GOOGLE,
        "ollama": ModelProvider.OLLAMA,
        "hybrid": ModelProvider.HYBRID,
    }

    # Map string tier names to ModelTier enum
    tier_map = {
        "cheap": ModelTier.CHEAP,
        "capable": ModelTier.CAPABLE,
        "premium": ModelTier.PREMIUM,
    }

    for provider_str, tiers in MODEL_REGISTRY.items():
        if provider_str not in provider_map:
            continue  # Skip custom providers
        provider_enum = provider_map[provider_str]
        result[provider_enum] = {}
        for tier_str, model_info in tiers.items():
            if tier_str in tier_map:
                result[provider_enum][tier_map[tier_str]] = model_info.id

    return result


# Model mappings by provider and tier (derived from MODEL_REGISTRY)
PROVIDER_MODELS: dict[ModelProvider, dict[ModelTier, str]] = _build_provider_models()


@dataclass
class WorkflowStage:
    """Represents a single stage in a workflow."""

    name: str
    tier: ModelTier
    description: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0
    result: Any = None
    duration_ms: int = 0
    skipped: bool = False
    skip_reason: str | None = None


@dataclass
class CostReport:
    """Cost breakdown for a workflow execution."""

    total_cost: float
    baseline_cost: float  # If all stages used premium
    savings: float
    savings_percent: float
    by_stage: dict[str, float] = field(default_factory=dict)
    by_tier: dict[str, float] = field(default_factory=dict)
    # Cache metrics
    cache_hits: int = 0
    cache_misses: int = 0
    cache_hit_rate: float = 0.0
    estimated_cost_without_cache: float = 0.0
    savings_from_cache: float = 0.0


@dataclass
class StageQualityMetrics:
    """Quality metrics for stage output validation."""

    execution_succeeded: bool
    output_valid: bool
    quality_improved: bool  # Workflow-specific (e.g., health score improved)
    error_type: str | None
    validation_error: str | None


@dataclass
class WorkflowResult:
    """Result of a workflow execution."""

    success: bool
    stages: list[WorkflowStage]
    final_output: Any
    cost_report: CostReport
    started_at: datetime
    completed_at: datetime
    total_duration_ms: int
    provider: str = "unknown"
    error: str | None = None
    # Structured error taxonomy for reliability
    error_type: str | None = None  # "config" | "runtime" | "provider" | "timeout" | "validation"
    transient: bool = False  # True if retry is reasonable (e.g., provider timeout)


# Global singleton for workflow history store (lazy-initialized)
_history_store: Any = None  # WorkflowHistoryStore | None


def _get_history_store():
    """Get or create workflow history store singleton.

    Returns SQLite-based history store. Falls back to None if initialization fails.
    """
    global _history_store

    if _history_store is None:
        try:
            from .history import WorkflowHistoryStore

            _history_store = WorkflowHistoryStore()
            logger.debug("Workflow history store initialized (SQLite)")
        except (ImportError, OSError, PermissionError) as e:
            # File system errors or missing dependencies
            logger.warning(f"Failed to initialize SQLite history store: {e}")
            _history_store = False  # Mark as failed to avoid repeated attempts

    # Return store or None if initialization failed
    return _history_store if _history_store is not False else None


def _load_workflow_history(history_file: str = WORKFLOW_HISTORY_FILE) -> list[dict]:
    """Load workflow run history from disk (legacy JSON support).

    DEPRECATED: Use WorkflowHistoryStore for new code.
    This function is maintained for backward compatibility.

    Args:
        history_file: Path to JSON history file

    Returns:
        List of workflow run dictionaries
    """
    import warnings

    warnings.warn(
        "_load_workflow_history is deprecated. Use WorkflowHistoryStore instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    path = Path(history_file)
    if not path.exists():
        return []
    try:
        with open(path) as f:
            data = json.load(f)
            return list(data) if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _save_workflow_run(
    workflow_name: str,
    provider: str,
    result: WorkflowResult,
    history_file: str = WORKFLOW_HISTORY_FILE,
    max_history: int = 100,
) -> None:
    """Save a workflow run to history.

    Uses SQLite-based storage by default. Falls back to JSON if SQLite unavailable.

    Args:
        workflow_name: Name of the workflow
        provider: Provider used (anthropic, openai, google)
        result: WorkflowResult object
        history_file: Legacy JSON path (ignored if SQLite available)
        max_history: Legacy max history limit (ignored if SQLite available)
    """
    # Try SQLite first (new approach)
    store = _get_history_store()
    if store is not None:
        try:
            run_id = str(uuid.uuid4())
            store.record_run(run_id, workflow_name, provider, result)
            logger.debug(f"Workflow run saved to SQLite: {run_id}")
            return
        except (OSError, PermissionError, ValueError) as e:
            # SQLite failed, fall back to JSON
            logger.warning(f"Failed to save to SQLite, falling back to JSON: {e}")

    # Fallback: Legacy JSON storage
    logger.debug("Using legacy JSON storage for workflow history")
    path = Path(history_file)
    path.parent.mkdir(parents=True, exist_ok=True)

    history = []
    if path.exists():
        try:
            with open(path) as f:
                data = json.load(f)
                history = list(data) if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            pass

    # Create run record
    run: dict = {
        "workflow": workflow_name,
        "provider": provider,
        "success": result.success,
        "started_at": result.started_at.isoformat(),
        "completed_at": result.completed_at.isoformat(),
        "duration_ms": result.total_duration_ms,
        "cost": result.cost_report.total_cost,
        "baseline_cost": result.cost_report.baseline_cost,
        "savings": result.cost_report.savings,
        "savings_percent": result.cost_report.savings_percent,
        "stages": [
            {
                "name": s.name,
                "tier": s.tier.value,
                "skipped": s.skipped,
                "cost": s.cost,
                "duration_ms": s.duration_ms,
            }
            for s in result.stages
        ],
        "error": result.error,
    }

    # Extract XML-parsed fields from final_output if present
    if isinstance(result.final_output, dict):
        if result.final_output.get("xml_parsed"):
            run["xml_parsed"] = True
            run["summary"] = result.final_output.get("summary")
            run["findings"] = result.final_output.get("findings", [])
            run["checklist"] = result.final_output.get("checklist", [])

    # Add to history and trim
    history.append(run)
    history = history[-max_history:]

    validated_path = _validate_file_path(str(path))
    with open(validated_path, "w") as f:
        json.dump(history, f, indent=2)


def get_workflow_stats(history_file: str = WORKFLOW_HISTORY_FILE) -> dict:
    """Get workflow statistics for dashboard.

    Uses SQLite-based storage by default. Falls back to JSON if unavailable.

    Args:
        history_file: Legacy JSON path (used only if SQLite unavailable)

    Returns:
        Dictionary with workflow stats including:
        - total_runs: Total workflow runs
        - successful_runs: Number of successful runs
        - by_workflow: Per-workflow stats
        - by_provider: Per-provider stats
        - by_tier: Cost breakdown by tier
        - recent_runs: Last 10 runs
        - total_cost: Total cost across all runs
        - total_savings: Total cost savings
        - avg_savings_percent: Average savings percentage
    """
    # Try SQLite first (new approach)
    store = _get_history_store()
    if store is not None:
        try:
            return store.get_stats()
        except (OSError, PermissionError, ValueError) as e:
            # SQLite failed, fall back to JSON
            logger.warning(f"Failed to get stats from SQLite, falling back to JSON: {e}")

    # Fallback: Legacy JSON storage
    logger.debug("Using legacy JSON storage for workflow stats")
    history = []
    path = Path(history_file)
    if path.exists():
        try:
            with open(path) as f:
                data = json.load(f)
                history = list(data) if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            pass

    if not history:
        return {
            "total_runs": 0,
            "successful_runs": 0,
            "by_workflow": {},
            "by_provider": {},
            "by_tier": {"cheap": 0, "capable": 0, "premium": 0},
            "recent_runs": [],
            "total_cost": 0.0,
            "total_savings": 0.0,
            "avg_savings_percent": 0.0,
        }

    # Aggregate stats
    by_workflow: dict[str, dict] = {}
    by_provider: dict[str, dict] = {}
    by_tier: dict[str, float] = {"cheap": 0.0, "capable": 0.0, "premium": 0.0}
    total_cost = 0.0
    total_savings = 0.0
    successful_runs = 0

    for run in history:
        wf_name = run.get("workflow", "unknown")
        provider = run.get("provider", "unknown")
        cost = run.get("cost", 0.0)
        savings = run.get("savings", 0.0)

        # By workflow
        if wf_name not in by_workflow:
            by_workflow[wf_name] = {"runs": 0, "cost": 0.0, "savings": 0.0, "success": 0}
        by_workflow[wf_name]["runs"] += 1
        by_workflow[wf_name]["cost"] += cost
        by_workflow[wf_name]["savings"] += savings
        if run.get("success"):
            by_workflow[wf_name]["success"] += 1

        # By provider
        if provider not in by_provider:
            by_provider[provider] = {"runs": 0, "cost": 0.0}
        by_provider[provider]["runs"] += 1
        by_provider[provider]["cost"] += cost

        # By tier (from stages)
        for stage in run.get("stages", []):
            if not stage.get("skipped"):
                tier = stage.get("tier", "capable")
                by_tier[tier] = by_tier.get(tier, 0.0) + stage.get("cost", 0.0)

        total_cost += cost
        total_savings += savings
        if run.get("success"):
            successful_runs += 1

    # Calculate average savings percent
    avg_savings_percent = 0.0
    if history:
        savings_percents = [r.get("savings_percent", 0) for r in history if r.get("success")]
        if savings_percents:
            avg_savings_percent = sum(savings_percents) / len(savings_percents)

    return {
        "total_runs": len(history),
        "successful_runs": successful_runs,
        "by_workflow": by_workflow,
        "by_provider": by_provider,
        "by_tier": by_tier,
        "recent_runs": history[-10:][::-1],  # Last 10, most recent first
        "total_cost": total_cost,
        "total_savings": total_savings,
        "avg_savings_percent": avg_savings_percent,
    }


class BaseWorkflow(CachingMixin, TelemetryMixin, ABC):
    """Base class for multi-model workflows.

    Inherits from CachingMixin and TelemetryMixin (extracted for maintainability).

    Subclasses define stages and tier mappings:

        class MyWorkflow(BaseWorkflow):
            name = "my-workflow"
            description = "Does something useful"
            stages = ["stage1", "stage2", "stage3"]
            tier_map = {
                "stage1": ModelTier.CHEAP,
                "stage2": ModelTier.CAPABLE,
                "stage3": ModelTier.PREMIUM,
            }

            async def run_stage(self, stage_name, tier, input_data):
                # Implement stage logic
                return output_data
    """

    name: str = "base-workflow"
    description: str = "Base workflow template"
    stages: list[str] = []
    tier_map: dict[str, ModelTier] = {}

    def __init__(
        self,
        cost_tracker: CostTracker | None = None,
        provider: ModelProvider | str | None = None,
        config: WorkflowConfig | None = None,
        executor: LLMExecutor | None = None,
        telemetry_backend: TelemetryBackend | None = None,
        progress_callback: ProgressCallback | None = None,
        cache: BaseCache | None = None,
        enable_cache: bool = True,
        enable_tier_tracking: bool = True,
        enable_tier_fallback: bool = False,
        routing_strategy: TierRoutingStrategy | None = None,
        enable_rich_progress: bool = False,
        enable_adaptive_routing: bool = False,
        enable_heartbeat_tracking: bool = False,
        enable_coordination: bool = False,
        agent_id: str | None = None,
    ):
        """Initialize workflow with optional cost tracker, provider, and config.

        Args:
            cost_tracker: CostTracker instance for logging costs
            provider: Model provider (anthropic, openai, ollama) or ModelProvider enum.
                     If None, uses config or defaults to anthropic.
            config: WorkflowConfig for model customization. If None, loads from
                   .empathy/workflows.yaml or uses defaults.
            executor: LLMExecutor for abstracted LLM calls (optional).
                     If provided, enables unified execution with telemetry.
            telemetry_backend: TelemetryBackend for storing telemetry records.
                     Defaults to TelemetryStore (JSONL file backend).
            progress_callback: Callback for real-time progress updates.
                     If provided, enables live progress tracking during execution.
            cache: Optional cache instance. If None and enable_cache=True,
                   auto-creates cache with one-time setup prompt.
            enable_cache: Whether to enable caching (default True).
            enable_tier_tracking: Whether to enable automatic tier tracking (default True).
            enable_tier_fallback: Whether to enable intelligent tier fallback
                     (CHEAP → CAPABLE → PREMIUM). Opt-in feature (default False).
            routing_strategy: Optional TierRoutingStrategy for dynamic tier selection.
                     When provided, overrides static tier_map for stage tier decisions.
                     Strategies: CostOptimizedRouting, PerformanceOptimizedRouting,
                     BalancedRouting, HybridRouting.
            enable_rich_progress: Whether to enable Rich-based live progress display
                     (default False). When enabled and output is a TTY, shows live
                     progress bars with spinners. Default is False because most users
                     run workflows from IDEs (VSCode, etc.) where TTY is not available.
                     The console reporter works reliably in all environments.
            enable_adaptive_routing: Whether to enable adaptive model routing based
                     on telemetry history (default False). When enabled, uses historical
                     performance data to select the optimal Anthropic model for each stage,
                     automatically upgrading tiers when failure rates exceed 20%.
                     Opt-in feature for cost optimization and automatic quality improvement.
            enable_heartbeat_tracking: Whether to enable agent heartbeat tracking
                     (default False). When enabled, publishes TTL-based heartbeat updates
                     to Redis for agent liveness monitoring. Requires Redis backend.
                     Pattern 1 from Agent Coordination Architecture.
            enable_coordination: Whether to enable inter-agent coordination signals
                     (default False). When enabled, workflow can send and receive TTL-based
                     ephemeral signals for agent-to-agent communication. Requires Redis backend.
                     Pattern 2 from Agent Coordination Architecture.
            agent_id: Optional agent ID for heartbeat tracking and coordination.
                     If None, auto-generates ID from workflow name and run ID.
                     Used as identifier in Redis keys (heartbeat:{agent_id}, signal:{agent_id}:...).

        """
        from .config import WorkflowConfig

        self.cost_tracker = cost_tracker or CostTracker()
        self._stages_run: list[WorkflowStage] = []

        # Progress tracking
        self._progress_callback = progress_callback
        self._progress_tracker: ProgressTracker | None = None
        self._enable_rich_progress = enable_rich_progress
        self._rich_reporter: RichProgressReporter | None = None

        # New: LLMExecutor support
        self._executor = executor
        self._api_key: str | None = None  # For default executor creation

        # Cache support
        self._cache: BaseCache | None = cache
        self._enable_cache = enable_cache
        self._cache_setup_attempted = False

        # Tier tracking support
        self._enable_tier_tracking = enable_tier_tracking
        self._tier_tracker: WorkflowTierTracker | None = None

        # Tier fallback support
        self._enable_tier_fallback = enable_tier_fallback
        self._tier_progression: list[tuple[str, str, bool]] = []  # (stage, tier, success)

        # Routing strategy support
        self._routing_strategy: TierRoutingStrategy | None = routing_strategy

        # Adaptive routing support (Pattern 3 from AGENT_COORDINATION_ARCHITECTURE)
        self._enable_adaptive_routing = enable_adaptive_routing
        self._adaptive_router = None  # Lazy initialization on first use

        # Agent tracking and coordination (Pattern 1 & 2 from AGENT_COORDINATION_ARCHITECTURE)
        self._enable_heartbeat_tracking = enable_heartbeat_tracking
        self._enable_coordination = enable_coordination
        self._agent_id = agent_id  # Will be set during execute() if None
        self._heartbeat_coordinator = None  # Lazy initialization on first use
        self._coordination_signals = None  # Lazy initialization on first use

        # Telemetry tracking (uses TelemetryMixin)
        self._init_telemetry(telemetry_backend)

        # Load config if not provided
        self._config = config or WorkflowConfig.load()

        # Determine provider (priority: arg > config > default)
        if provider is None:
            provider = self._config.get_provider_for_workflow(self.name)

        # Handle string provider input
        if isinstance(provider, str):
            provider_str = provider.lower()
            try:
                provider = ModelProvider(provider_str)
                self._provider_str = provider_str
            except ValueError:
                # Custom provider, keep as string
                self._provider_str = provider_str
                provider = ModelProvider.CUSTOM
        else:
            self._provider_str = provider.value

        self.provider = provider

    def get_tier_for_stage(self, stage_name: str) -> ModelTier:
        """Get the model tier for a stage from static tier_map."""
        return self.tier_map.get(stage_name, ModelTier.CAPABLE)

    def _get_adaptive_router(self):
        """Get or create AdaptiveModelRouter instance (lazy initialization).

        Returns:
            AdaptiveModelRouter instance if telemetry is available, None otherwise
        """
        if not self._enable_adaptive_routing:
            return None

        if self._adaptive_router is None:
            # Lazy import to avoid circular dependencies
            try:
                from empathy_os.models import AdaptiveModelRouter

                if TELEMETRY_AVAILABLE and UsageTracker is not None:
                    self._adaptive_router = AdaptiveModelRouter(
                        telemetry=UsageTracker.get_instance()
                    )
                    logger.debug(
                        "adaptive_routing_initialized",
                        workflow=self.name,
                        message="Adaptive routing enabled for cost optimization"
                    )
                else:
                    logger.warning(
                        "adaptive_routing_unavailable",
                        workflow=self.name,
                        message="Telemetry not available, adaptive routing disabled"
                    )
                    self._enable_adaptive_routing = False
            except ImportError as e:
                logger.warning(
                    "adaptive_routing_import_error",
                    workflow=self.name,
                    error=str(e),
                    message="Failed to import AdaptiveModelRouter"
                )
                self._enable_adaptive_routing = False

        return self._adaptive_router

    def _get_heartbeat_coordinator(self):
        """Get or create HeartbeatCoordinator instance (lazy initialization).

        Returns:
            HeartbeatCoordinator instance if heartbeat tracking is enabled, None otherwise
        """
        if not self._enable_heartbeat_tracking:
            return None

        if self._heartbeat_coordinator is None:
            try:
                from empathy_os.telemetry import HeartbeatCoordinator

                self._heartbeat_coordinator = HeartbeatCoordinator()
                logger.debug(
                    "heartbeat_tracking_initialized",
                    workflow=self.name,
                    agent_id=self._agent_id,
                    message="Heartbeat tracking enabled for agent liveness monitoring"
                )
            except ImportError as e:
                logger.warning(
                    "heartbeat_tracking_import_error",
                    workflow=self.name,
                    error=str(e),
                    message="Failed to import HeartbeatCoordinator"
                )
                self._enable_heartbeat_tracking = False
            except Exception as e:
                logger.warning(
                    "heartbeat_tracking_init_error",
                    workflow=self.name,
                    error=str(e),
                    message="Failed to initialize HeartbeatCoordinator (Redis unavailable?)"
                )
                self._enable_heartbeat_tracking = False

        return self._heartbeat_coordinator

    def _get_coordination_signals(self):
        """Get or create CoordinationSignals instance (lazy initialization).

        Returns:
            CoordinationSignals instance if coordination is enabled, None otherwise
        """
        if not self._enable_coordination:
            return None

        if self._coordination_signals is None:
            try:
                from empathy_os.telemetry import CoordinationSignals

                self._coordination_signals = CoordinationSignals(agent_id=self._agent_id)
                logger.debug(
                    "coordination_initialized",
                    workflow=self.name,
                    agent_id=self._agent_id,
                    message="Coordination signals enabled for inter-agent communication"
                )
            except ImportError as e:
                logger.warning(
                    "coordination_import_error",
                    workflow=self.name,
                    error=str(e),
                    message="Failed to import CoordinationSignals"
                )
                self._enable_coordination = False
            except Exception as e:
                logger.warning(
                    "coordination_init_error",
                    workflow=self.name,
                    error=str(e),
                    message="Failed to initialize CoordinationSignals (Redis unavailable?)"
                )
                self._enable_coordination = False

        return self._coordination_signals

    def _check_adaptive_tier_upgrade(self, stage_name: str, current_tier: ModelTier) -> ModelTier:
        """Check if adaptive routing recommends a tier upgrade.

        Uses historical telemetry to detect if the current tier has a high
        failure rate (>20%) and automatically upgrades to the next tier.

        Args:
            stage_name: Name of the stage
            current_tier: Currently selected tier

        Returns:
            Upgraded tier if recommended, otherwise current_tier
        """
        router = self._get_adaptive_router()
        if router is None:
            return current_tier

        # Check if tier upgrade is recommended
        should_upgrade, reason = router.recommend_tier_upgrade(
            workflow=self.name,
            stage=stage_name
        )

        if should_upgrade:
            # Upgrade to next tier: CHEAP → CAPABLE → PREMIUM
            if current_tier == ModelTier.CHEAP:
                new_tier = ModelTier.CAPABLE
            elif current_tier == ModelTier.CAPABLE:
                new_tier = ModelTier.PREMIUM
            else:
                new_tier = current_tier  # Already at highest tier

            logger.warning(
                "adaptive_routing_tier_upgrade",
                workflow=self.name,
                stage=stage_name,
                old_tier=current_tier.value,
                new_tier=new_tier.value,
                reason=reason
            )

            return new_tier

        return current_tier

    def send_signal(
        self,
        signal_type: str,
        target_agent: str | None = None,
        payload: dict[str, Any] | None = None,
        ttl_seconds: int | None = None,
    ) -> str:
        """Send a coordination signal to another agent (Pattern 2).

        Args:
            signal_type: Type of signal (e.g., "task_complete", "checkpoint", "error")
            target_agent: Target agent ID (None for broadcast to all agents)
            payload: Optional signal payload data
            ttl_seconds: Optional TTL override (default 60 seconds)

        Returns:
            Signal ID if coordination is enabled, empty string otherwise

        Example:
            >>> # Signal completion to orchestrator
            >>> workflow.send_signal(
            ...     signal_type="task_complete",
            ...     target_agent="orchestrator",
            ...     payload={"result": "success", "data": {...}}
            ... )

            >>> # Broadcast abort to all agents
            >>> workflow.send_signal(
            ...     signal_type="abort",
            ...     target_agent=None,  # Broadcast
            ...     payload={"reason": "user_cancelled"}
            ... )
        """
        coordinator = self._get_coordination_signals()
        if coordinator is None:
            return ""

        try:
            return coordinator.signal(
                signal_type=signal_type,
                source_agent=self._agent_id,
                target_agent=target_agent,
                payload=payload or {},
                ttl_seconds=ttl_seconds,
            )
        except Exception as e:
            logger.warning(f"Failed to send coordination signal: {e}")
            return ""

    def wait_for_signal(
        self,
        signal_type: str,
        source_agent: str | None = None,
        timeout: float = 30.0,
        poll_interval: float = 0.5,
    ) -> Any:
        """Wait for a coordination signal from another agent (Pattern 2).

        Blocking call that polls for signals with timeout.

        Args:
            signal_type: Type of signal to wait for
            source_agent: Optional source agent filter
            timeout: Maximum wait time in seconds (default 30.0)
            poll_interval: Poll interval in seconds (default 0.5)

        Returns:
            CoordinationSignal if received, None if timeout or coordination disabled

        Example:
            >>> # Wait for orchestrator approval
            >>> signal = workflow.wait_for_signal(
            ...     signal_type="approval",
            ...     source_agent="orchestrator",
            ...     timeout=60.0
            ... )
            >>> if signal:
            ...     proceed_with_deployment(signal.payload)
        """
        coordinator = self._get_coordination_signals()
        if coordinator is None:
            return None

        try:
            return coordinator.wait_for_signal(
                signal_type=signal_type,
                source_agent=source_agent,
                timeout=timeout,
                poll_interval=poll_interval,
            )
        except Exception as e:
            logger.warning(f"Failed to wait for coordination signal: {e}")
            return None

    def check_signal(
        self,
        signal_type: str,
        source_agent: str | None = None,
        consume: bool = True,
    ) -> Any:
        """Check for a coordination signal without blocking (Pattern 2).

        Non-blocking check for pending signals.

        Args:
            signal_type: Type of signal to check for
            source_agent: Optional source agent filter
            consume: If True, remove signal after reading (default True)

        Returns:
            CoordinationSignal if available, None otherwise

        Example:
            >>> # Non-blocking check for abort signal
            >>> signal = workflow.check_signal(signal_type="abort")
            >>> if signal:
            ...     raise WorkflowAbortedException(signal.payload["reason"])
        """
        coordinator = self._get_coordination_signals()
        if coordinator is None:
            return None

        try:
            return coordinator.check_signal(
                signal_type=signal_type,
                source_agent=source_agent,
                consume=consume,
            )
        except Exception as e:
            logger.warning(f"Failed to check coordination signal: {e}")
            return None

    def _get_tier_with_routing(
        self,
        stage_name: str,
        input_data: dict[str, Any],
        budget_remaining: float = 100.0,
    ) -> ModelTier:
        """Get tier for a stage using routing strategy or adaptive routing if available.

        Priority order:
        1. If routing_strategy configured, uses that for tier selection
        2. Otherwise uses static tier_map
        3. If adaptive routing enabled, checks for tier upgrade recommendations

        Args:
            stage_name: Name of the stage
            input_data: Current workflow data (used to estimate input size)
            budget_remaining: Remaining budget in USD for this execution

        Returns:
            ModelTier to use for this stage (potentially upgraded by adaptive routing)
        """
        # Get base tier from routing strategy or static map
        if self._routing_strategy is not None:
            from .routing import RoutingContext

            # Estimate input size from data
            input_size = self._estimate_input_tokens(input_data)

            # Assess complexity
            complexity = self._assess_complexity(input_data)

            # Determine latency sensitivity based on stage position
            # First stages are more latency-sensitive (user waiting)
            stage_index = self.stages.index(stage_name) if stage_name in self.stages else 0
            if stage_index == 0:
                latency_sensitivity = "high"
            elif stage_index < len(self.stages) // 2:
                latency_sensitivity = "medium"
            else:
                latency_sensitivity = "low"

            # Create routing context
            context = RoutingContext(
                task_type=f"{self.name}:{stage_name}",
                input_size=input_size,
                complexity=complexity,
                budget_remaining=budget_remaining,
                latency_sensitivity=latency_sensitivity,
            )

            # Delegate to routing strategy
            base_tier = self._routing_strategy.route(context)
        else:
            # Use static tier_map
            base_tier = self.get_tier_for_stage(stage_name)

        # Check if adaptive routing recommends a tier upgrade
        # This uses telemetry history to detect high failure rates
        if self._enable_adaptive_routing:
            final_tier = self._check_adaptive_tier_upgrade(stage_name, base_tier)
            return final_tier

        return base_tier

    def _estimate_input_tokens(self, input_data: dict[str, Any]) -> int:
        """Estimate input token count from data.

        Simple heuristic: ~4 characters per token on average.

        Args:
            input_data: Workflow input data

        Returns:
            Estimated token count
        """
        import json

        try:
            # Serialize to estimate size
            data_str = json.dumps(input_data, default=str)
            return len(data_str) // 4
        except (TypeError, ValueError):
            return 1000  # Default estimate

    def get_model_for_tier(self, tier: ModelTier) -> str:
        """Get the model for a tier based on configured provider and config."""
        from .config import get_model

        provider_str = getattr(self, "_provider_str", self.provider.value)

        # Use config-aware model lookup
        model = get_model(provider_str, tier.value, self._config)
        return model

    # Note: _maybe_setup_cache is inherited from CachingMixin

    async def _call_llm(
        self,
        tier: ModelTier,
        system: str,
        user_message: str,
        max_tokens: int = 4096,
        stage_name: str | None = None,
    ) -> tuple[str, int, int]:
        """Provider-agnostic LLM call using the configured provider.

        This method uses run_step_with_executor internally to make LLM calls
        that respect the configured provider (anthropic, openai, google, etc.).

        Supports automatic caching to reduce API costs and latency.
        Tracks telemetry for usage analysis and cost savings measurement.

        Args:
            tier: Model tier to use (CHEAP, CAPABLE, PREMIUM)
            system: System prompt
            user_message: User message/prompt
            max_tokens: Maximum tokens in response
            stage_name: Optional stage name for cache key (defaults to tier)

        Returns:
            Tuple of (response_content, input_tokens, output_tokens)

        """
        from .step_config import WorkflowStepConfig

        # Start timing for telemetry
        start_time = time.time()

        # Determine stage name for cache key
        stage = stage_name or f"llm_call_{tier.value}"
        model = self.get_model_for_tier(tier)
        cache_type = None

        # Try cache lookup using CachingMixin
        cached = self._try_cache_lookup(stage, system, user_message, model)
        if cached is not None:
            # Track telemetry for cache hit
            duration_ms = int((time.time() - start_time) * 1000)
            cost = self._calculate_cost(tier, cached.input_tokens, cached.output_tokens)
            cache_type = self._get_cache_type()

            self._track_telemetry(
                stage=stage,
                tier=tier,
                model=model,
                cost=cost,
                tokens={"input": cached.input_tokens, "output": cached.output_tokens},
                cache_hit=True,
                cache_type=cache_type,
                duration_ms=duration_ms,
            )

            return (cached.content, cached.input_tokens, cached.output_tokens)

        # Create a step config for this call
        step = WorkflowStepConfig(
            name=stage,
            task_type="general",
            tier_hint=tier.value,
            description="LLM call",
            max_tokens=max_tokens,
        )

        try:
            content, in_tokens, out_tokens, cost = await self.run_step_with_executor(
                step=step,
                prompt=user_message,
                system=system,
            )

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Track telemetry for actual LLM call
            self._track_telemetry(
                stage=stage,
                tier=tier,
                model=model,
                cost=cost,
                tokens={"input": in_tokens, "output": out_tokens},
                cache_hit=False,
                cache_type=None,
                duration_ms=duration_ms,
            )

            # Store in cache using CachingMixin
            self._store_in_cache(
                stage,
                system,
                user_message,
                model,
                CachedResponse(content=content, input_tokens=in_tokens, output_tokens=out_tokens),
            )

            return content, in_tokens, out_tokens
        except (ValueError, TypeError, KeyError) as e:
            # Invalid input or configuration errors
            logger.warning(f"LLM call failed (invalid input): {e}")
            return f"Error calling LLM (invalid input): {e}", 0, 0
        except (TimeoutError, RuntimeError, ConnectionError) as e:
            # Timeout, API errors, or connection failures
            logger.warning(f"LLM call failed (timeout/API/connection error): {e}")
            return f"Error calling LLM (timeout/API error): {e}", 0, 0
        except (OSError, PermissionError) as e:
            # File system or permission errors
            logger.warning(f"LLM call failed (file system error): {e}")
            return f"Error calling LLM (file system error): {e}", 0, 0
        except Exception as e:
            # INTENTIONAL: Graceful degradation - return error message rather than crashing workflow
            logger.exception(f"Unexpected error calling LLM: {e}")
            return f"Error calling LLM: {type(e).__name__}", 0, 0

    # Note: _track_telemetry is inherited from TelemetryMixin

    def _calculate_cost(self, tier: ModelTier, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for a stage."""
        tier_name = tier.value
        pricing = MODEL_PRICING.get(tier_name, MODEL_PRICING["capable"])
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost

    def _calculate_baseline_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate what the cost would be using premium tier."""
        pricing = MODEL_PRICING["premium"]
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost

    def _generate_cost_report(self) -> CostReport:
        """Generate cost report from completed stages."""
        total_cost = 0.0
        baseline_cost = 0.0
        by_stage: dict[str, float] = {}
        by_tier: dict[str, float] = {}

        for stage in self._stages_run:
            if stage.skipped:
                continue

            total_cost += stage.cost
            by_stage[stage.name] = stage.cost

            tier_name = stage.tier.value
            by_tier[tier_name] = by_tier.get(tier_name, 0.0) + stage.cost

            # Calculate what this would cost at premium tier
            baseline_cost += self._calculate_baseline_cost(stage.input_tokens, stage.output_tokens)

        savings = baseline_cost - total_cost
        savings_percent = (savings / baseline_cost * 100) if baseline_cost > 0 else 0.0

        # Calculate cache metrics using CachingMixin
        cache_stats = self._get_cache_stats()
        cache_hits = cache_stats["hits"]
        cache_misses = cache_stats["misses"]
        cache_hit_rate = cache_stats["hit_rate"]
        estimated_cost_without_cache = total_cost
        savings_from_cache = 0.0

        # Estimate cost without cache (assumes cache hits would have incurred full cost)
        if cache_hits > 0:
            avg_cost_per_call = total_cost / cache_misses if cache_misses > 0 else 0.0
            estimated_additional_cost = cache_hits * avg_cost_per_call
            estimated_cost_without_cache = total_cost + estimated_additional_cost
            savings_from_cache = estimated_additional_cost

        return CostReport(
            total_cost=total_cost,
            baseline_cost=baseline_cost,
            savings=savings,
            savings_percent=savings_percent,
            by_stage=by_stage,
            by_tier=by_tier,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            cache_hit_rate=cache_hit_rate,
            estimated_cost_without_cache=estimated_cost_without_cache,
            savings_from_cache=savings_from_cache,
        )

    @abstractmethod
    async def run_stage(
        self,
        stage_name: str,
        tier: ModelTier,
        input_data: Any,
    ) -> tuple[Any, int, int]:
        """Execute a single workflow stage.

        Args:
            stage_name: Name of the stage to run
            tier: Model tier to use
            input_data: Input for this stage

        Returns:
            Tuple of (output_data, input_tokens, output_tokens)

        """

    def should_skip_stage(self, stage_name: str, input_data: Any) -> tuple[bool, str | None]:
        """Determine if a stage should be skipped.

        Override in subclasses for conditional stage execution.

        Args:
            stage_name: Name of the stage
            input_data: Current workflow data

        Returns:
            Tuple of (should_skip, reason)

        """
        return False, None

    def validate_output(self, stage_output: dict) -> tuple[bool, str | None]:
        """Validate stage output quality for tier fallback decisions.

        This is called after each stage execution when tier fallback is enabled.
        Override in subclasses to add workflow-specific validation logic.

        Default implementation checks:
        - No exceptions during execution (execution_succeeded)
        - Output is not empty (output_valid)
        - Required keys present if defined in stage config

        Args:
            stage_output: Output dict from run_stage()

        Returns:
            Tuple of (is_valid, failure_reason)
            - is_valid: True if output passes quality gates
            - failure_reason: Error code if validation failed (e.g., "output_empty",
              "health_score_low", "tests_failed")

        Example:
            >>> def validate_output(self, stage_output):
            ...     # Check health score for health-check workflow
            ...     health_score = stage_output.get("health_score", 0)
            ...     if health_score < 80:
            ...         return False, "health_score_low"
            ...     return True, None

        """
        # Default validation: check output is not empty
        if not stage_output:
            return False, "output_empty"

        # Check for error indicators in output
        if stage_output.get("error") is not None:
            return False, "execution_error"

        # Output is valid by default
        return True, None

    def _assess_complexity(self, input_data: dict[str, Any]) -> str:
        """Assess task complexity based on workflow stages and input.

        Args:
            input_data: Workflow input data

        Returns:
            Complexity level: "simple", "moderate", or "complex"

        """
        # Simple heuristic: based on number of stages and tier requirements
        num_stages = len(self.stages)
        premium_stages = sum(
            1 for s in self.stages if self.get_tier_for_stage(s) == ModelTier.PREMIUM
        )

        if num_stages <= 2 and premium_stages == 0:
            return "simple"
        elif num_stages <= 4 and premium_stages <= 1:
            return "moderate"
        else:
            return "complex"

    async def execute(self, **kwargs: Any) -> WorkflowResult:
        """Execute the full workflow.

        Args:
            **kwargs: Initial input data for the workflow

        Returns:
            WorkflowResult with stages, output, and cost report

        """
        # Set up cache (one-time setup with user prompt if needed)
        self._maybe_setup_cache()

        # Set run ID for telemetry correlation
        self._run_id = str(uuid.uuid4())

        # Log task routing (Tier 1 automation monitoring)
        routing_id = f"routing-{self._run_id}"
        routing_record = TaskRoutingRecord(
            routing_id=routing_id,
            timestamp=datetime.utcnow().isoformat() + "Z",
            task_description=f"{self.name}: {self.description}",
            task_type=self.name,
            task_complexity=self._assess_complexity(kwargs),
            assigned_agent=self.name,
            assigned_tier=getattr(self, "_provider_str", "unknown"),
            routing_strategy="rule_based",
            confidence_score=1.0,
            status="running",
            started_at=datetime.utcnow().isoformat() + "Z",
        )

        # Log routing start
        try:
            if self._telemetry_backend is not None:
                self._telemetry_backend.log_task_routing(routing_record)
        except Exception as e:
            logger.debug(f"Failed to log task routing: {e}")

        # Auto tier recommendation
        if self._enable_tier_tracking:
            try:
                from .tier_tracking import WorkflowTierTracker

                self._tier_tracker = WorkflowTierTracker(self.name, self.description)
                files_affected = kwargs.get("files_affected") or kwargs.get("path")
                if files_affected and not isinstance(files_affected, list):
                    files_affected = [str(files_affected)]
                self._tier_tracker.show_recommendation(files_affected)
            except Exception as e:
                logger.debug(f"Tier tracking disabled: {e}")
                self._enable_tier_tracking = False

        # Initialize agent ID for heartbeat/coordination (Pattern 1 & 2)
        if self._agent_id is None:
            # Auto-generate agent ID from workflow name and run ID
            self._agent_id = f"{self.name}-{self._run_id[:8]}"

        # Start heartbeat tracking (Pattern 1)
        heartbeat_coordinator = self._get_heartbeat_coordinator()
        if heartbeat_coordinator:
            try:
                heartbeat_coordinator.start_heartbeat(
                    agent_id=self._agent_id,
                    metadata={
                        "workflow": self.name,
                        "run_id": self._run_id,
                        "provider": getattr(self, "_provider_str", "unknown"),
                        "stages": len(self.stages),
                    }
                )
                logger.debug(
                    "heartbeat_started",
                    workflow=self.name,
                    agent_id=self._agent_id,
                    message="Agent heartbeat tracking started"
                )
            except Exception as e:
                logger.warning(f"Failed to start heartbeat tracking: {e}")
                self._enable_heartbeat_tracking = False

        started_at = datetime.now()
        self._stages_run = []
        current_data = kwargs
        error = None

        # Initialize progress tracker
        # Always show progress by default (IDE-friendly console output)
        # Rich live display only when explicitly enabled AND in TTY
        from .progress import ConsoleProgressReporter

        self._progress_tracker = ProgressTracker(
            workflow_name=self.name,
            workflow_id=self._run_id,
            stage_names=self.stages,
        )

        # Add user's callback if provided
        if self._progress_callback:
            self._progress_tracker.add_callback(self._progress_callback)

        # Rich progress: only when explicitly enabled AND in a TTY
        if self._enable_rich_progress and RICH_AVAILABLE and sys.stdout.isatty():
            try:
                self._rich_reporter = RichProgressReporter(self.name, self.stages)
                self._progress_tracker.add_callback(self._rich_reporter.report)
                self._rich_reporter.start()
            except Exception as e:
                # Fall back to console reporter
                logger.debug(f"Rich progress unavailable: {e}")
                self._rich_reporter = None
                console_reporter = ConsoleProgressReporter(verbose=False)
                self._progress_tracker.add_callback(console_reporter.report)
        else:
            # Default: use console reporter (works in IDEs, terminals, everywhere)
            console_reporter = ConsoleProgressReporter(verbose=False)
            self._progress_tracker.add_callback(console_reporter.report)

        self._progress_tracker.start_workflow()

        try:
            # Tier fallback mode: try CHEAP → CAPABLE → PREMIUM with validation
            if self._enable_tier_fallback:
                tier_chain = [ModelTier.CHEAP, ModelTier.CAPABLE, ModelTier.PREMIUM]

                for stage_name in self.stages:
                    # Check if stage should be skipped
                    should_skip, skip_reason = self.should_skip_stage(stage_name, current_data)

                    if should_skip:
                        tier = self.get_tier_for_stage(stage_name)
                        stage = WorkflowStage(
                            name=stage_name,
                            tier=tier,
                            description=f"Stage: {stage_name}",
                            skipped=True,
                            skip_reason=skip_reason,
                        )
                        self._stages_run.append(stage)

                        # Report skip to progress tracker
                        if self._progress_tracker:
                            self._progress_tracker.skip_stage(stage_name, skip_reason or "")

                        continue

                    # Try each tier in fallback chain
                    stage_succeeded = False
                    tier_index = 0

                    for tier in tier_chain:
                        stage_start = datetime.now()

                        # Report stage start to progress tracker with current tier
                        model_id = self.get_model_for_tier(tier)
                        if self._progress_tracker:
                            # On first attempt, start stage. On retry, update tier.
                            if tier_index == 0:
                                self._progress_tracker.start_stage(stage_name, tier.value, model_id)
                            else:
                                # Show tier upgrade (e.g., CHEAP → CAPABLE)
                                prev_tier = tier_chain[tier_index - 1].value
                                self._progress_tracker.update_tier(
                                    stage_name, tier.value, f"{prev_tier}_failed"
                                )

                        # Update heartbeat at stage start (Pattern 1)
                        if heartbeat_coordinator:
                            try:
                                stage_index = self.stages.index(stage_name)
                                progress = stage_index / len(self.stages)
                                heartbeat_coordinator.beat(
                                    status="running",
                                    progress=progress,
                                    current_task=f"Running stage: {stage_name} ({tier.value})"
                                )
                            except Exception as e:
                                logger.debug(f"Heartbeat update failed: {e}")

                        try:
                            # Run the stage at current tier
                            output, input_tokens, output_tokens = await self.run_stage(
                                stage_name,
                                tier,
                                current_data,
                            )

                            stage_end = datetime.now()
                            duration_ms = int((stage_end - stage_start).total_seconds() * 1000)
                            cost = self._calculate_cost(tier, input_tokens, output_tokens)

                            # Create stage output dict for validation
                            stage_output = (
                                output if isinstance(output, dict) else {"result": output}
                            )

                            # Validate output quality
                            is_valid, failure_reason = self.validate_output(stage_output)

                            if is_valid:
                                # Success - record stage and move to next
                                stage = WorkflowStage(
                                    name=stage_name,
                                    tier=tier,
                                    description=f"Stage: {stage_name}",
                                    input_tokens=input_tokens,
                                    output_tokens=output_tokens,
                                    cost=cost,
                                    result=output,
                                    duration_ms=duration_ms,
                                )
                                self._stages_run.append(stage)

                                # Report stage completion to progress tracker
                                if self._progress_tracker:
                                    self._progress_tracker.complete_stage(
                                        stage_name,
                                        cost=cost,
                                        tokens_in=input_tokens,
                                        tokens_out=output_tokens,
                                    )

                                # Update heartbeat after stage completion (Pattern 1)
                                if heartbeat_coordinator:
                                    try:
                                        stage_index = self.stages.index(stage_name) + 1
                                        progress = stage_index / len(self.stages)
                                        heartbeat_coordinator.beat(
                                            status="running",
                                            progress=progress,
                                            current_task=f"Completed stage: {stage_name}"
                                        )
                                    except Exception as e:
                                        logger.debug(f"Heartbeat update failed: {e}")

                                # Log to cost tracker
                                self.cost_tracker.log_request(
                                    model=model_id,
                                    input_tokens=input_tokens,
                                    output_tokens=output_tokens,
                                    task_type=f"workflow:{self.name}:{stage_name}",
                                )

                                # Track telemetry for this stage
                                self._track_telemetry(
                                    stage=stage_name,
                                    tier=tier,
                                    model=model_id,
                                    cost=cost,
                                    tokens={"input": input_tokens, "output": output_tokens},
                                    cache_hit=False,
                                    cache_type=None,
                                    duration_ms=duration_ms,
                                )

                                # Record successful tier usage
                                self._tier_progression.append((stage_name, tier.value, True))
                                stage_succeeded = True

                                # Pass output to next stage
                                current_data = stage_output
                                break  # Success - move to next stage

                            else:
                                # Quality gate failed - try next tier
                                self._tier_progression.append((stage_name, tier.value, False))
                                logger.info(
                                    f"Stage {stage_name} failed quality validation with {tier.value}: "
                                    f"{failure_reason}"
                                )

                                # Check if more tiers available
                                if tier_index < len(tier_chain) - 1:
                                    logger.info("Retrying with higher tier...")
                                else:
                                    logger.error(f"All tiers exhausted for {stage_name}")

                        except Exception as e:
                            # Exception during stage execution - try next tier
                            self._tier_progression.append((stage_name, tier.value, False))
                            logger.warning(
                                f"Stage {stage_name} error with {tier.value}: {type(e).__name__}: {e}"
                            )

                            # Check if more tiers available
                            if tier_index < len(tier_chain) - 1:
                                logger.info("Retrying with higher tier...")
                            else:
                                logger.error(f"All tiers exhausted for {stage_name}")

                        tier_index += 1

                    # Check if stage succeeded with any tier
                    if not stage_succeeded:
                        error_msg = (
                            f"Stage {stage_name} failed with all tiers: CHEAP, CAPABLE, PREMIUM"
                        )
                        if self._progress_tracker:
                            self._progress_tracker.fail_stage(stage_name, error_msg)
                        raise ValueError(error_msg)

            # Standard mode: use routing strategy or tier_map (backward compatible)
            else:
                # Track budget for routing decisions
                total_budget = 100.0  # Default budget in USD
                budget_spent = 0.0

                for stage_name in self.stages:
                    # Use routing strategy if available, otherwise fall back to tier_map
                    budget_remaining = total_budget - budget_spent
                    tier = self._get_tier_with_routing(
                        stage_name,
                        current_data if isinstance(current_data, dict) else {},
                        budget_remaining,
                    )
                    stage_start = datetime.now()

                    # Check if stage should be skipped
                    should_skip, skip_reason = self.should_skip_stage(stage_name, current_data)

                    if should_skip:
                        stage = WorkflowStage(
                            name=stage_name,
                            tier=tier,
                            description=f"Stage: {stage_name}",
                            skipped=True,
                            skip_reason=skip_reason,
                        )
                        self._stages_run.append(stage)

                        # Report skip to progress tracker
                        if self._progress_tracker:
                            self._progress_tracker.skip_stage(stage_name, skip_reason or "")

                        continue

                    # Report stage start to progress tracker
                    model_id = self.get_model_for_tier(tier)
                    if self._progress_tracker:
                        self._progress_tracker.start_stage(stage_name, tier.value, model_id)

                    # Run the stage
                    output, input_tokens, output_tokens = await self.run_stage(
                        stage_name,
                        tier,
                        current_data,
                    )

                    stage_end = datetime.now()
                    duration_ms = int((stage_end - stage_start).total_seconds() * 1000)
                    cost = self._calculate_cost(tier, input_tokens, output_tokens)

                    # Update budget spent for routing decisions
                    budget_spent += cost

                    stage = WorkflowStage(
                        name=stage_name,
                        tier=tier,
                        description=f"Stage: {stage_name}",
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        cost=cost,
                        result=output,
                        duration_ms=duration_ms,
                    )
                    self._stages_run.append(stage)

                    # Report stage completion to progress tracker
                    if self._progress_tracker:
                        self._progress_tracker.complete_stage(
                            stage_name,
                            cost=cost,
                            tokens_in=input_tokens,
                            tokens_out=output_tokens,
                        )

                    # Log to cost tracker
                    self.cost_tracker.log_request(
                        model=model_id,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        task_type=f"workflow:{self.name}:{stage_name}",
                    )

                    # Track telemetry for this stage
                    self._track_telemetry(
                        stage=stage_name,
                        tier=tier,
                        model=model_id,
                        cost=cost,
                        tokens={"input": input_tokens, "output": output_tokens},
                        cache_hit=False,
                        cache_type=None,
                        duration_ms=duration_ms,
                    )

                    # Pass output to next stage
                    current_data = output if isinstance(output, dict) else {"result": output}

        except (ValueError, TypeError, KeyError) as e:
            # Data validation or configuration errors
            error = f"Workflow execution error (data/config): {e}"
            logger.error(error)
            if self._progress_tracker:
                self._progress_tracker.fail_workflow(error)
        except (TimeoutError, RuntimeError, ConnectionError) as e:
            # Timeout, API errors, or connection failures
            error = f"Workflow execution error (timeout/API/connection): {e}"
            logger.error(error)
            if self._progress_tracker:
                self._progress_tracker.fail_workflow(error)
        except (OSError, PermissionError) as e:
            # File system or permission errors
            error = f"Workflow execution error (file system): {e}"
            logger.error(error)
            if self._progress_tracker:
                self._progress_tracker.fail_workflow(error)
        except Exception as e:
            # INTENTIONAL: Workflow orchestration - catch all errors to report failure gracefully
            logger.exception(f"Unexpected error in workflow execution: {type(e).__name__}")
            error = f"Workflow execution failed: {type(e).__name__}"
            if self._progress_tracker:
                self._progress_tracker.fail_workflow(error)

        completed_at = datetime.now()
        total_duration_ms = int((completed_at - started_at).total_seconds() * 1000)

        # Get final output from last non-skipped stage
        final_output = None
        for stage in reversed(self._stages_run):
            if not stage.skipped and stage.result is not None:
                final_output = stage.result
                break

        # Classify error type and transient status
        error_type = None
        transient = False
        if error:
            error_lower = error.lower()
            if "timeout" in error_lower or "timed out" in error_lower:
                error_type = "timeout"
                transient = True
            elif "config" in error_lower or "configuration" in error_lower:
                error_type = "config"
                transient = False
            elif "api" in error_lower or "rate limit" in error_lower or "quota" in error_lower:
                error_type = "provider"
                transient = True
            elif "validation" in error_lower or "invalid" in error_lower:
                error_type = "validation"
                transient = False
            else:
                error_type = "runtime"
                transient = False

        provider_str = getattr(self, "_provider_str", "unknown")
        result = WorkflowResult(
            success=error is None,
            stages=self._stages_run,
            final_output=final_output,
            cost_report=self._generate_cost_report(),
            started_at=started_at,
            completed_at=completed_at,
            total_duration_ms=total_duration_ms,
            provider=provider_str,
            error=error,
            error_type=error_type,
            transient=transient,
        )

        # Report workflow completion to progress tracker
        if self._progress_tracker and error is None:
            self._progress_tracker.complete_workflow()

        # Stop Rich progress display if active
        if self._rich_reporter:
            try:
                self._rich_reporter.stop()
            except Exception:
                pass  # Best effort cleanup
            self._rich_reporter = None

        # Save to workflow history for dashboard
        try:
            _save_workflow_run(self.name, provider_str, result)
        except (OSError, PermissionError):
            # File system errors saving history - log but don't crash workflow
            logger.warning("Failed to save workflow history (file system error)")
        except (ValueError, TypeError, KeyError):
            # Data serialization errors - log but don't crash workflow
            logger.warning("Failed to save workflow history (serialization error)")
        except Exception:
            # INTENTIONAL: History save is optional diagnostics - never crash workflow
            logger.exception("Unexpected error saving workflow history")

        # Emit workflow telemetry to backend
        self._emit_workflow_telemetry(result)

        # Stop heartbeat tracking (Pattern 1)
        if heartbeat_coordinator:
            try:
                final_status = "completed" if result.success else "failed"
                heartbeat_coordinator.stop_heartbeat(final_status=final_status)
                logger.debug(
                    "heartbeat_stopped",
                    workflow=self.name,
                    agent_id=self._agent_id,
                    status=final_status,
                    message="Agent heartbeat tracking stopped"
                )
            except Exception as e:
                logger.warning(f"Failed to stop heartbeat tracking: {e}")

        # Auto-save tier progression
        if self._enable_tier_tracking and self._tier_tracker:
            try:
                files_affected = kwargs.get("files_affected") or kwargs.get("path")
                if files_affected and not isinstance(files_affected, list):
                    files_affected = [str(files_affected)]

                # Determine bug type from workflow name
                bug_type_map = {
                    "code-review": "code_quality",
                    "bug-predict": "bug_prediction",
                    "security-audit": "security_issue",
                    "test-gen": "test_coverage",
                    "refactor-plan": "refactoring",
                    "health-check": "health_check",
                }
                bug_type = bug_type_map.get(self.name, "workflow_run")

                # Pass tier_progression data if tier fallback was enabled
                tier_progression_data = (
                    self._tier_progression if self._enable_tier_fallback else None
                )

                self._tier_tracker.save_progression(
                    workflow_result=result,
                    files_affected=files_affected,
                    bug_type=bug_type,
                    tier_progression=tier_progression_data,
                )
            except Exception as e:
                logger.debug(f"Failed to save tier progression: {e}")

        # Update routing record with completion status (Tier 1 automation monitoring)
        routing_record.status = "completed" if result.success else "failed"
        routing_record.completed_at = datetime.utcnow().isoformat() + "Z"
        routing_record.success = result.success
        routing_record.actual_cost = sum(s.cost for s in result.stages)

        if not result.success and result.error:
            routing_record.error_type = result.error_type or "unknown"
            routing_record.error_message = result.error

        # Log routing completion
        try:
            if self._telemetry_backend is not None:
                self._telemetry_backend.log_task_routing(routing_record)
        except Exception as e:
            logger.debug(f"Failed to log task routing completion: {e}")

        return result

    def describe(self) -> str:
        """Get a human-readable description of the workflow."""
        lines = [
            f"Workflow: {self.name}",
            f"Description: {self.description}",
            "",
            "Stages:",
        ]

        for stage_name in self.stages:
            tier = self.get_tier_for_stage(stage_name)
            model = self.get_model_for_tier(tier)
            lines.append(f"  {stage_name}: {tier.value} ({model})")

        return "\n".join(lines)

    def _build_cached_system_prompt(
        self,
        role: str,
        guidelines: list[str] | None = None,
        documentation: str | None = None,
        examples: list[dict[str, str]] | None = None,
    ) -> str:
        """Build system prompt optimized for Anthropic prompt caching.

        Prompt caching works best with:
        - Static content (guidelines, docs, coding standards)
        - Frequent reuse (>3 requests within 5 min)
        - Large context (>1024 tokens)

        Structure: Static content goes first (cacheable), dynamic content
        goes in user messages (not cached).

        Args:
            role: The role for the AI (e.g., "expert code reviewer")
            guidelines: List of static guidelines/rules
            documentation: Static documentation or reference material
            examples: Static examples for few-shot learning

        Returns:
            System prompt with static content first for optimal caching

        Example:
            >>> prompt = workflow._build_cached_system_prompt(
            ...     role="code reviewer",
            ...     guidelines=[
            ...         "Follow PEP 8 style guide",
            ...         "Check for security vulnerabilities",
            ...     ],
            ...     documentation="Coding standards:\\n- Use type hints\\n- Add docstrings",
            ... )
            >>> # This prompt will be cached by Anthropic for 5 minutes
            >>> # Subsequent calls with same prompt read from cache (90% cost reduction)
        """
        parts = []

        # 1. Role definition (static)
        parts.append(f"You are a {role}.")

        # 2. Guidelines (static - most important for caching)
        if guidelines:
            parts.append("\n# Guidelines\n")
            for i, guideline in enumerate(guidelines, 1):
                parts.append(f"{i}. {guideline}")

        # 3. Documentation (static - good caching candidate)
        if documentation:
            parts.append("\n# Reference Documentation\n")
            parts.append(documentation)

        # 4. Examples (static - excellent for few-shot learning)
        if examples:
            parts.append("\n# Examples\n")
            for i, example in enumerate(examples, 1):
                input_text = example.get("input", "")
                output_text = example.get("output", "")
                parts.append(f"\nExample {i}:")
                parts.append(f"Input: {input_text}")
                parts.append(f"Output: {output_text}")

        # Dynamic content (user-specific context, current task) should go
        # in the user message, NOT in system prompt
        parts.append(
            "\n# Instructions\n"
            "The user will provide the specific task context in their message. "
            "Apply the above guidelines and reference documentation to their request."
        )

        return "\n".join(parts)

    # =========================================================================
    # New infrastructure methods (Phase 4)
    # =========================================================================

    def _create_execution_context(
        self,
        step_name: str,
        task_type: str,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> ExecutionContext:
        """Create an ExecutionContext for a step execution.

        Args:
            step_name: Name of the workflow step
            task_type: Task type for routing
            user_id: Optional user ID
            session_id: Optional session ID

        Returns:
            ExecutionContext populated with workflow info

        """
        return ExecutionContext(
            workflow_name=self.name,
            step_name=step_name,
            user_id=user_id,
            session_id=session_id,
            metadata={
                "task_type": task_type,
                "run_id": self._run_id,
                "provider": self._provider_str,
            },
        )

    def _create_default_executor(self) -> LLMExecutor:
        """Create a default EmpathyLLMExecutor with optional resilience wrapper.

        This method is called lazily when run_step_with_executor is used
        without a pre-configured executor.

        When tier fallback is enabled (enable_tier_fallback=True), the base
        executor is returned without the ResilientExecutor wrapper to avoid
        double fallback (tier-level + LLM-level).

        When tier fallback is disabled (default), the executor is wrapped with
        resilience features (retry, fallback, circuit breaker).

        Returns:
            LLMExecutor instance (optionally wrapped with ResilientExecutor)

        """
        from empathy_os.models.empathy_executor import EmpathyLLMExecutor
        from empathy_os.models.fallback import ResilientExecutor

        # Create the base executor
        base_executor = EmpathyLLMExecutor(
            provider=self._provider_str,
            api_key=self._api_key,
            telemetry_store=self._telemetry_backend,
        )

        # When tier fallback is enabled, skip LLM-level fallback
        # to avoid double fallback (tier-level + LLM-level)
        if self._enable_tier_fallback:
            return base_executor

        # Standard mode: wrap with resilience layer (retry, fallback, circuit breaker)
        return ResilientExecutor(executor=base_executor)

    def _get_executor(self) -> LLMExecutor:
        """Get or create the LLM executor.

        Returns the configured executor or creates a default one.

        Returns:
            LLMExecutor instance

        """
        if self._executor is None:
            self._executor = self._create_default_executor()
        return self._executor

    # Note: _emit_call_telemetry and _emit_workflow_telemetry are inherited from TelemetryMixin

    async def run_step_with_executor(
        self,
        step: WorkflowStepConfig,
        prompt: str,
        system: str | None = None,
        **kwargs: Any,
    ) -> tuple[str, int, int, float]:
        """Run a workflow step using the LLMExecutor.

        This method provides a unified interface for executing steps with
        automatic routing, telemetry, and cost tracking. If no executor
        was provided at construction, a default EmpathyLLMExecutor is created.

        Args:
            step: WorkflowStepConfig defining the step
            prompt: The prompt to send
            system: Optional system prompt
            **kwargs: Additional arguments passed to executor

        Returns:
            Tuple of (content, input_tokens, output_tokens, cost)

        """
        executor = self._get_executor()

        context = self._create_execution_context(
            step_name=step.name,
            task_type=step.task_type,
        )

        start_time = datetime.now()
        response = await executor.run(
            task_type=step.task_type,
            prompt=prompt,
            system=system,
            context=context,
            **kwargs,
        )
        end_time = datetime.now()
        latency_ms = int((end_time - start_time).total_seconds() * 1000)

        # Emit telemetry
        self._emit_call_telemetry(
            step_name=step.name,
            task_type=step.task_type,
            tier=response.tier,
            model_id=response.model_id,
            input_tokens=response.tokens_input,
            output_tokens=response.tokens_output,
            cost=response.cost_estimate,
            latency_ms=latency_ms,
            success=True,
        )

        return (
            response.content,
            response.tokens_input,
            response.tokens_output,
            response.cost_estimate,
        )

    # =========================================================================
    # XML Prompt Integration (Phase 4)
    # =========================================================================

    def _get_xml_config(self) -> dict[str, Any]:
        """Get XML prompt configuration for this workflow.

        Returns:
            Dictionary with XML configuration settings.

        """
        if self._config is None:
            return {}
        return self._config.get_xml_config_for_workflow(self.name)

    def _is_xml_enabled(self) -> bool:
        """Check if XML prompts are enabled for this workflow."""
        config = self._get_xml_config()
        return bool(config.get("enabled", False))

    def _render_xml_prompt(
        self,
        role: str,
        goal: str,
        instructions: list[str],
        constraints: list[str],
        input_type: str,
        input_payload: str,
        extra: dict[str, Any] | None = None,
    ) -> str:
        """Render a prompt using XML template if enabled.

        Args:
            role: The role for the AI (e.g., "security analyst").
            goal: The primary objective.
            instructions: Step-by-step instructions.
            constraints: Rules and guidelines.
            input_type: Type of input ("code", "diff", "document").
            input_payload: The content to process.
            extra: Additional context data.

        Returns:
            Rendered prompt string (XML if enabled, plain text otherwise).

        """
        from empathy_os.prompts import PromptContext, XmlPromptTemplate, get_template

        config = self._get_xml_config()

        if not config.get("enabled", False):
            # Fall back to plain text
            return self._render_plain_prompt(
                role,
                goal,
                instructions,
                constraints,
                input_type,
                input_payload,
            )

        # Create context
        context = PromptContext(
            role=role,
            goal=goal,
            instructions=instructions,
            constraints=constraints,
            input_type=input_type,
            input_payload=input_payload,
            extra=extra or {},
        )

        # Get template
        template_name = config.get("template_name", self.name)
        template = get_template(template_name)

        if template is None:
            # Create a basic XML template if no built-in found
            template = XmlPromptTemplate(
                name=self.name,
                schema_version=config.get("schema_version", "1.0"),
            )

        return template.render(context)

    def _render_plain_prompt(
        self,
        role: str,
        goal: str,
        instructions: list[str],
        constraints: list[str],
        input_type: str,
        input_payload: str,
    ) -> str:
        """Render a plain text prompt (fallback when XML is disabled)."""
        parts = [f"You are a {role}.", "", f"Goal: {goal}", ""]

        if instructions:
            parts.append("Instructions:")
            for i, inst in enumerate(instructions, 1):
                parts.append(f"{i}. {inst}")
            parts.append("")

        if constraints:
            parts.append("Guidelines:")
            for constraint in constraints:
                parts.append(f"- {constraint}")
            parts.append("")

        if input_payload:
            parts.append(f"Input ({input_type}):")
            parts.append(input_payload)

        return "\n".join(parts)

    def _parse_xml_response(self, response: str) -> dict[str, Any]:
        """Parse an XML response if XML enforcement is enabled.

        Args:
            response: The LLM response text.

        Returns:
            Dictionary with parsed fields or raw response data.

        """
        from empathy_os.prompts import XmlResponseParser

        config = self._get_xml_config()

        if not config.get("enforce_response_xml", False):
            # No parsing needed, return as-is
            return {
                "_parsed_response": None,
                "_raw": response,
            }

        fallback = config.get("fallback_on_parse_error", True)
        parser = XmlResponseParser(fallback_on_error=fallback)
        parsed = parser.parse(response)

        return {
            "_parsed_response": parsed,
            "_raw": response,
            "summary": parsed.summary,
            "findings": [f.to_dict() for f in parsed.findings],
            "checklist": parsed.checklist,
            "xml_parsed": parsed.success,
            "parse_errors": parsed.errors,
        }

    def _extract_findings_from_response(
        self,
        response: str,
        files_changed: list[str],
        code_context: str = "",
    ) -> list[dict[str, Any]]:
        """Extract structured findings from LLM response.

        Tries multiple strategies in order:
        1. XML parsing (if XML tags present)
        2. Regex-based extraction for file:line patterns
        3. Returns empty list if no findings extractable

        Args:
            response: Raw LLM response text
            files_changed: List of files being analyzed (for context)
            code_context: Original code being reviewed (optional)

        Returns:
            List of findings matching WorkflowFinding schema:
            [
                {
                    "id": "unique-id",
                    "file": "relative/path.py",
                    "line": 42,
                    "column": 10,
                    "severity": "high",
                    "category": "security",
                    "message": "Brief message",
                    "details": "Extended explanation",
                    "recommendation": "Fix suggestion"
                }
            ]

        """
        import re
        import uuid

        findings: list[dict[str, Any]] = []

        # Strategy 1: Try XML parsing first
        response_lower = response.lower()
        if (
            "<finding>" in response_lower
            or "<issue>" in response_lower
            or "<findings>" in response_lower
        ):
            # Parse XML directly (bypass config checks)
            from empathy_os.prompts import XmlResponseParser

            parser = XmlResponseParser(fallback_on_error=True)
            parsed = parser.parse(response)

            if parsed.success and parsed.findings:
                for raw_finding in parsed.findings:
                    enriched = self._enrich_finding_with_location(
                        raw_finding.to_dict(),
                        files_changed,
                    )
                    findings.append(enriched)
                return findings

        # Strategy 2: Regex-based extraction for common patterns
        # Match patterns like:
        # - "src/auth.py:42: SQL injection found"
        # - "In file src/auth.py line 42"
        # - "auth.py (line 42, column 10)"
        patterns = [
            # Pattern 1: file.py:line:column: message
            r"([^\s:]+\.(?:py|ts|tsx|js|jsx|java|go|rb|php)):(\d+):(\d+):\s*(.+)",
            # Pattern 2: file.py:line: message
            r"([^\s:]+\.(?:py|ts|tsx|js|jsx|java|go|rb|php)):(\d+):\s*(.+)",
            # Pattern 3: in file X line Y
            r"(?:in file|file)\s+([^\s]+\.(?:py|ts|tsx|js|jsx|java|go|rb|php))\s+line\s+(\d+)",
            # Pattern 4: file.py (line X)
            r"([^\s]+\.(?:py|ts|tsx|js|jsx|java|go|rb|php))\s*\(line\s+(\d+)(?:,\s*col(?:umn)?\s+(\d+))?\)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            for match in matches:
                if len(match) >= 2:
                    file_path = match[0]
                    line = int(match[1])

                    # Handle different pattern formats
                    if len(match) == 4 and match[2].isdigit():
                        # Pattern 1: file:line:col:message
                        column = int(match[2])
                        message = match[3]
                    elif len(match) == 3 and match[2] and not match[2].isdigit():
                        # Pattern 2: file:line:message
                        column = 1
                        message = match[2]
                    elif len(match) == 3 and match[2].isdigit():
                        # Pattern 4: file (line col)
                        column = int(match[2])
                        message = ""
                    else:
                        # Pattern 3: in file X line Y (no message)
                        column = 1
                        message = ""

                    # Determine severity from keywords in message
                    severity = self._infer_severity(message)
                    category = self._infer_category(message)

                    findings.append(
                        {
                            "id": str(uuid.uuid4())[:8],
                            "file": file_path,
                            "line": line,
                            "column": column,
                            "severity": severity,
                            "category": category,
                            "message": message.strip() if message else "",
                            "details": "",
                            "recommendation": "",
                        },
                    )

        # Deduplicate by file:line
        seen = set()
        unique_findings = []
        for finding in findings:
            key = (finding["file"], finding["line"])
            if key not in seen:
                seen.add(key)
                unique_findings.append(finding)

        return unique_findings

    def _enrich_finding_with_location(
        self,
        raw_finding: dict[str, Any],
        files_changed: list[str],
    ) -> dict[str, Any]:
        """Enrich a finding from XML parser with file/line/column fields.

        Args:
            raw_finding: Finding dict from XML parser (has 'location' string field)
            files_changed: List of files being analyzed

        Returns:
            Enriched finding dict with file, line, column fields

        """
        import uuid

        location_str = raw_finding.get("location", "")
        file_path, line, column = self._parse_location_string(location_str, files_changed)

        # Map category from severity or title keywords
        category = self._infer_category(
            raw_finding.get("title", "") + " " + raw_finding.get("details", ""),
        )

        return {
            "id": str(uuid.uuid4())[:8],
            "file": file_path,
            "line": line,
            "column": column,
            "severity": raw_finding.get("severity", "medium"),
            "category": category,
            "message": raw_finding.get("title", ""),
            "details": raw_finding.get("details", ""),
            "recommendation": raw_finding.get("fix", ""),
        }

    def _parse_location_string(
        self,
        location: str,
        files_changed: list[str],
    ) -> tuple[str, int, int]:
        """Parse a location string to extract file, line, column.

        Handles formats like:
        - "src/auth.py:42:10"
        - "src/auth.py:42"
        - "auth.py line 42"
        - "line 42 in auth.py"

        Args:
            location: Location string from finding
            files_changed: List of files being analyzed (for fallback)

        Returns:
            Tuple of (file_path, line_number, column_number)
            Defaults: ("", 1, 1) if parsing fails

        """
        import re

        if not location:
            # Fallback: use first file if available
            return (files_changed[0] if files_changed else "", 1, 1)

        # Try colon-separated format: file.py:line:col
        match = re.search(
            r"([^\s:]+\.(?:py|ts|tsx|js|jsx|java|go|rb|php)):(\d+)(?::(\d+))?",
            location,
        )
        if match:
            file_path = match.group(1)
            line = int(match.group(2))
            column = int(match.group(3)) if match.group(3) else 1
            return (file_path, line, column)

        # Try "line X in file.py" format
        match = re.search(
            r"line\s+(\d+)\s+(?:in|of)\s+([^\s]+\.(?:py|ts|tsx|js|jsx|java|go|rb|php))",
            location,
            re.IGNORECASE,
        )
        if match:
            line = int(match.group(1))
            file_path = match.group(2)
            return (file_path, line, 1)

        # Try "file.py line X" format
        match = re.search(
            r"([^\s]+\.(?:py|ts|tsx|js|jsx|java|go|rb|php))\s+line\s+(\d+)",
            location,
            re.IGNORECASE,
        )
        if match:
            file_path = match.group(1)
            line = int(match.group(2))
            return (file_path, line, 1)

        # Extract just line number if present
        match = re.search(r"line\s+(\d+)", location, re.IGNORECASE)
        if match:
            line = int(match.group(1))
            # Use first file from files_changed as fallback
            file_path = files_changed[0] if files_changed else ""
            return (file_path, line, 1)

        # Couldn't parse - return defaults
        return (files_changed[0] if files_changed else "", 1, 1)

    def _infer_severity(self, text: str) -> str:
        """Infer severity from keywords in text.

        Args:
            text: Message or title text

        Returns:
            Severity level: critical, high, medium, low, or info

        """
        text_lower = text.lower()

        if any(
            word in text_lower
            for word in [
                "critical",
                "severe",
                "exploit",
                "vulnerability",
                "injection",
                "remote code execution",
                "rce",
            ]
        ):
            return "critical"

        if any(
            word in text_lower
            for word in [
                "high",
                "security",
                "unsafe",
                "dangerous",
                "xss",
                "csrf",
                "auth",
                "password",
                "secret",
            ]
        ):
            return "high"

        if any(
            word in text_lower
            for word in [
                "warning",
                "issue",
                "problem",
                "bug",
                "error",
                "deprecated",
                "leak",
            ]
        ):
            return "medium"

        if any(word in text_lower for word in ["low", "minor", "style", "format", "typo"]):
            return "low"

        return "info"

    def _infer_category(self, text: str) -> str:
        """Infer finding category from keywords.

        Args:
            text: Message or title text

        Returns:
            Category: security, performance, maintainability, style, or correctness

        """
        text_lower = text.lower()

        if any(
            word in text_lower
            for word in [
                "security",
                "vulnerability",
                "injection",
                "xss",
                "csrf",
                "auth",
                "encrypt",
                "password",
                "secret",
                "unsafe",
            ]
        ):
            return "security"

        if any(
            word in text_lower
            for word in [
                "performance",
                "slow",
                "memory",
                "leak",
                "inefficient",
                "optimization",
                "cache",
            ]
        ):
            return "performance"

        if any(
            word in text_lower
            for word in [
                "complex",
                "refactor",
                "duplicate",
                "maintainability",
                "readability",
                "documentation",
            ]
        ):
            return "maintainability"

        if any(
            word in text_lower for word in ["style", "format", "lint", "convention", "whitespace"]
        ):
            return "style"

        return "correctness"
