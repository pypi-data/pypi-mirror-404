"""Progress Tracking System

Real-time progress tracking for workflow execution with WebSocket support.
Enables live UI updates during workflow runs.

Copyright 2025 Smart AI Memory, LLC
Licensed under Fair Source 0.9
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import uuid
from collections.abc import Callable, Coroutine, Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Protocol

logger = logging.getLogger(__name__)

# Rich imports with fallback
try:
    from rich.console import Console, Group
    from rich.live import Live
    from rich.panel import Panel
    from rich.progress import BarColumn, Progress, SpinnerColumn, TaskID, TextColumn
    from rich.table import Table
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None  # type: ignore
    Live = None  # type: ignore
    Panel = None  # type: ignore
    Progress = None  # type: ignore


class ProgressStatus(Enum):
    """Status of a workflow or stage."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    FALLBACK = "fallback"  # Using fallback model
    RETRYING = "retrying"  # Retrying after error


@dataclass
class StageProgress:
    """Progress information for a single stage."""

    name: str
    status: ProgressStatus
    tier: str = "capable"
    model: str = ""
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int = 0
    cost: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    error: str | None = None
    fallback_info: str | None = None
    retry_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "status": self.status.value,
            "tier": self.tier,
            "model": self.model,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "cost": self.cost,
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
            "error": self.error,
            "fallback_info": self.fallback_info,
            "retry_count": self.retry_count,
        }


@dataclass
class ProgressUpdate:
    """A progress update to be broadcast."""

    workflow: str
    workflow_id: str
    current_stage: str
    stage_index: int
    total_stages: int
    status: ProgressStatus
    message: str
    cost_so_far: float = 0.0
    tokens_so_far: int = 0
    percent_complete: float = 0.0
    estimated_remaining_ms: int | None = None
    stages: list[StageProgress] = field(default_factory=list)
    fallback_info: str | None = None
    error: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "workflow": self.workflow,
            "workflow_id": self.workflow_id,
            "current_stage": self.current_stage,
            "stage_index": self.stage_index,
            "total_stages": self.total_stages,
            "status": self.status.value,
            "message": self.message,
            "cost_so_far": self.cost_so_far,
            "tokens_so_far": self.tokens_so_far,
            "percent_complete": self.percent_complete,
            "estimated_remaining_ms": self.estimated_remaining_ms,
            "stages": [s.to_dict() for s in self.stages],
            "fallback_info": self.fallback_info,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


# Type for progress callbacks
ProgressCallback = Callable[[ProgressUpdate], None]
AsyncProgressCallback = Callable[[ProgressUpdate], Coroutine[Any, Any, None]]


class ProgressTracker:
    """Tracks and broadcasts workflow progress.

    Maintains state for all stages and emits updates to registered callbacks.
    Supports both sync and async callbacks for flexibility.
    """

    def __init__(
        self,
        workflow_name: str,
        workflow_id: str,
        stage_names: list[str],
    ):
        self.workflow = workflow_name
        self.workflow_id = workflow_id
        self.stage_names = stage_names
        # Optimization: Index map for O(1) stage lookup (vs O(n) .index() call)
        self._stage_index_map: dict[str, int] = {name: i for i, name in enumerate(stage_names)}
        self.current_index = 0
        self.cost_accumulated = 0.0
        self.tokens_accumulated = 0
        self._started_at = datetime.now()
        self._stage_start_times: dict[str, datetime] = {}
        self._stage_durations: list[int] = []

        # Initialize stages
        self.stages: list[StageProgress] = [
            StageProgress(name=name, status=ProgressStatus.PENDING) for name in stage_names
        ]

        # Callbacks
        self._callbacks: list[ProgressCallback] = []
        self._async_callbacks: list[AsyncProgressCallback] = []

    def add_callback(self, callback: ProgressCallback) -> None:
        """Add a synchronous progress callback."""
        self._callbacks.append(callback)

    def add_async_callback(self, callback: AsyncProgressCallback) -> None:
        """Add an asynchronous progress callback."""
        self._async_callbacks.append(callback)

    def remove_callback(self, callback: ProgressCallback) -> None:
        """Remove a synchronous callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def start_workflow(self) -> None:
        """Mark workflow as started."""
        self._started_at = datetime.now()
        self._emit(ProgressStatus.RUNNING, f"Starting {self.workflow}...")

    def start_stage(self, stage_name: str, tier: str = "capable", model: str = "") -> None:
        """Mark a stage as started."""
        stage = self._get_stage(stage_name)
        if stage:
            stage.status = ProgressStatus.RUNNING
            stage.started_at = datetime.now()
            stage.tier = tier
            stage.model = model
            self._stage_start_times[stage_name] = stage.started_at
            # Optimization: O(1) lookup instead of O(n) .index() call
            self.current_index = self._stage_index_map.get(stage_name, 0)

        self._emit(ProgressStatus.RUNNING, f"Running {stage_name}...")

    def complete_stage(
        self,
        stage_name: str,
        cost: float = 0.0,
        tokens_in: int = 0,
        tokens_out: int = 0,
    ) -> None:
        """Mark a stage as completed."""
        stage = self._get_stage(stage_name)
        if stage:
            stage.status = ProgressStatus.COMPLETED
            stage.completed_at = datetime.now()
            stage.cost = cost
            stage.tokens_in = tokens_in
            stage.tokens_out = tokens_out

            if stage.started_at:
                duration_ms = int((stage.completed_at - stage.started_at).total_seconds() * 1000)
                stage.duration_ms = duration_ms
                self._stage_durations.append(duration_ms)

        self.cost_accumulated += cost
        self.tokens_accumulated += tokens_in + tokens_out
        # Optimization: O(1) lookup instead of O(n) .index() call
        self.current_index = self._stage_index_map.get(stage_name, 0) + 1

        self._emit(ProgressStatus.COMPLETED, f"Completed {stage_name}")

    def fail_stage(self, stage_name: str, error: str) -> None:
        """Mark a stage as failed."""
        stage = self._get_stage(stage_name)
        if stage:
            stage.status = ProgressStatus.FAILED
            stage.completed_at = datetime.now()
            stage.error = error

            if stage.started_at:
                stage.duration_ms = int(
                    (stage.completed_at - stage.started_at).total_seconds() * 1000,
                )

        self._emit(ProgressStatus.FAILED, f"Failed: {stage_name}", error=error)

    def skip_stage(self, stage_name: str, reason: str = "") -> None:
        """Mark a stage as skipped."""
        stage = self._get_stage(stage_name)
        if stage:
            stage.status = ProgressStatus.SKIPPED

        message = f"Skipped {stage_name}"
        if reason:
            message += f": {reason}"
        self._emit(ProgressStatus.SKIPPED, message)

    def update_tier(self, stage_name: str, new_tier: str, reason: str = "") -> None:
        """Update the tier for a stage during tier fallback.

        Args:
            stage_name: Name of the stage
            new_tier: New tier being attempted (CHEAP, CAPABLE, PREMIUM)
            reason: Optional reason for tier change (e.g., "validation_failed")

        """
        stage = self._get_stage(stage_name)
        if stage:
            old_tier = stage.tier
            stage.tier = new_tier

            message = f"Tier upgrade: {stage_name} [{old_tier.upper()} → {new_tier.upper()}]"
            if reason:
                message += f" ({reason})"

            self._emit(ProgressStatus.RUNNING, message)

    def fallback_occurred(
        self,
        stage_name: str,
        original_model: str,
        fallback_model: str,
        reason: str,
    ) -> None:
        """Record that a fallback occurred."""
        stage = self._get_stage(stage_name)
        fallback_info = f"{original_model} → {fallback_model} ({reason})"

        if stage:
            stage.status = ProgressStatus.FALLBACK
            stage.fallback_info = fallback_info

        self._emit(
            ProgressStatus.FALLBACK,
            f"Falling back from {original_model} to {fallback_model}",
            fallback_info=fallback_info,
        )

    def retry_occurred(self, stage_name: str, attempt: int, max_attempts: int) -> None:
        """Record that a retry is occurring."""
        stage = self._get_stage(stage_name)
        if stage:
            stage.status = ProgressStatus.RETRYING
            stage.retry_count = attempt

        self._emit(
            ProgressStatus.RETRYING,
            f"Retrying {stage_name} (attempt {attempt}/{max_attempts})",
        )

    def complete_workflow(self) -> None:
        """Mark workflow as completed."""
        self._emit(
            ProgressStatus.COMPLETED,
            f"Workflow {self.workflow} completed",
        )

    def fail_workflow(self, error: str) -> None:
        """Mark workflow as failed."""
        self._emit(
            ProgressStatus.FAILED,
            f"Workflow {self.workflow} failed",
            error=error,
        )

    def _get_stage(self, stage_name: str) -> StageProgress | None:
        """Get stage by name."""
        for stage in self.stages:
            if stage.name == stage_name:
                return stage
        return None

    def _calculate_percent_complete(self) -> float:
        """Calculate completion percentage."""
        completed = sum(1 for s in self.stages if s.status == ProgressStatus.COMPLETED)
        return (completed / len(self.stages)) * 100 if self.stages else 0.0

    def _estimate_remaining_ms(self) -> int | None:
        """Estimate remaining time based on average stage duration."""
        if not self._stage_durations:
            return None

        avg_duration = sum(self._stage_durations) / len(self._stage_durations)
        remaining_stages = len(self.stages) - self.current_index
        return int(avg_duration * remaining_stages)

    def _emit(
        self,
        status: ProgressStatus,
        message: str,
        fallback_info: str | None = None,
        error: str | None = None,
    ) -> None:
        """Emit a progress update to all callbacks."""
        current_stage = (
            self.stage_names[min(self.current_index, len(self.stage_names) - 1)]
            if self.stage_names
            else ""
        )

        update = ProgressUpdate(
            workflow=self.workflow,
            workflow_id=self.workflow_id,
            current_stage=current_stage,
            stage_index=self.current_index,
            total_stages=len(self.stages),
            status=status,
            message=message,
            cost_so_far=self.cost_accumulated,
            tokens_so_far=self.tokens_accumulated,
            percent_complete=self._calculate_percent_complete(),
            estimated_remaining_ms=self._estimate_remaining_ms(),
            stages=list(self.stages),
            fallback_info=fallback_info,
            error=error,
        )

        # Call sync callbacks
        for callback in self._callbacks:
            try:
                callback(update)
            except Exception:  # noqa: BLE001
                # INTENTIONAL: Callbacks are optional - never fail workflow on callback error
                logger.warning("Progress callback error", exc_info=True)

        # Call async callbacks
        for async_callback in self._async_callbacks:
            try:
                asyncio.create_task(async_callback(update))
            except RuntimeError:
                # No event loop running, skip async callbacks
                pass


class ProgressReporter(Protocol):
    """Protocol for progress reporting implementations."""

    def report(self, update: ProgressUpdate) -> None:
        """Report a progress update."""
        ...

    async def report_async(self, update: ProgressUpdate) -> None:
        """Report a progress update asynchronously."""
        ...


class ConsoleProgressReporter:
    """Console-based progress reporter optimized for IDE environments.

    Provides clear, readable progress output that works reliably in:
    - VSCode integrated terminal
    - VSCode output panel
    - IDE debug consoles
    - Standard terminals

    Uses Unicode symbols that render correctly in most environments.
    """

    def __init__(self, verbose: bool = False, show_tokens: bool = False):
        """Initialize console progress reporter.

        Args:
            verbose: Show additional details (fallback info, errors)
            show_tokens: Include token counts in output
        """
        self.verbose = verbose
        self.show_tokens = show_tokens
        self._start_time: datetime | None = None
        self._stage_times: dict[str, int] = {}

    def report(self, update: ProgressUpdate) -> None:
        """Print progress to console.

        Args:
            update: Progress update from the tracker
        """
        # Track start time for elapsed calculation
        if self._start_time is None:
            self._start_time = datetime.now()

        percent = f"{update.percent_complete:3.0f}%"
        cost = f"${update.cost_so_far:.4f}"

        # Status icons that work in most environments
        status_icon = {
            ProgressStatus.PENDING: "○",
            ProgressStatus.RUNNING: "►",
            ProgressStatus.COMPLETED: "✓",
            ProgressStatus.FAILED: "✗",
            ProgressStatus.SKIPPED: "–",
            ProgressStatus.FALLBACK: "↻",
            ProgressStatus.RETRYING: "↻",
        }.get(update.status, "?")

        # Get current tier from running stage
        tier_info = ""
        model_info = ""
        if update.current_stage and update.stages:
            for stage in update.stages:
                if stage.name == update.current_stage:
                    if stage.status == ProgressStatus.RUNNING:
                        tier_info = f" [{stage.tier.upper()}]"
                        if stage.model:
                            model_info = f" ({stage.model})"
                    # Track stage duration
                    if stage.duration_ms > 0:
                        self._stage_times[stage.name] = stage.duration_ms
                    break

        # Build output line
        elapsed = ""
        if self._start_time:
            elapsed_sec = (datetime.now() - self._start_time).total_seconds()
            if elapsed_sec >= 1:
                elapsed = f" [{elapsed_sec:.1f}s]"

        tokens_str = ""
        if self.show_tokens and update.tokens_so_far > 0:
            tokens_str = f" | {update.tokens_so_far:,} tokens"

        # Format: [100%] ✓ Completed optimize [PREMIUM] ($0.0279) [12.3s]
        output = f"[{percent}] {status_icon} {update.message}{tier_info} ({cost}{tokens_str}){elapsed}"
        print(output)

        # Verbose output
        if self.verbose:
            if update.fallback_info:
                print(f"         ↳ Fallback: {update.fallback_info}")
            if update.error:
                print(f"         ↳ Error: {update.error}")

        # Print summary only on final workflow completion (not stage completion)
        if update.status == ProgressStatus.COMPLETED and "workflow" in update.message.lower():
            self._print_summary(update)

    def _print_summary(self, update: ProgressUpdate) -> None:
        """Print workflow completion summary."""
        if not self._stage_times:
            return

        print("")
        print("─" * 50)
        print("Stage Summary:")
        for stage in update.stages:
            if stage.status == ProgressStatus.COMPLETED:
                duration_ms = stage.duration_ms or self._stage_times.get(stage.name, 0)
                duration_str = f"{duration_ms}ms" if duration_ms < 1000 else f"{duration_ms/1000:.1f}s"
                cost_str = f"${stage.cost:.4f}" if stage.cost > 0 else "—"
                print(f"  {stage.name}: {duration_str} | {cost_str}")
            elif stage.status == ProgressStatus.SKIPPED:
                print(f"  {stage.name}: skipped")
        print("─" * 50)

    async def report_async(self, update: ProgressUpdate) -> None:
        """Async version just calls sync."""
        self.report(update)


class JsonLinesProgressReporter:
    """JSON Lines progress reporter for machine parsing."""

    def __init__(self, output_file: str | None = None):
        self.output_file = output_file

    def report(self, update: ProgressUpdate) -> None:
        """Output progress as JSON line."""
        json_line = update.to_json()

        if self.output_file:
            with open(self.output_file, "a") as f:
                f.write(json_line + "\n")
        else:
            print(json_line)

    async def report_async(self, update: ProgressUpdate) -> None:
        """Async version just calls sync."""
        self.report(update)


def create_progress_tracker(
    workflow_name: str,
    stage_names: list[str],
    reporter: ProgressReporter | None = None,
) -> ProgressTracker:
    """Factory function to create a progress tracker with optional reporter.

    Args:
        workflow_name: Name of the workflow
        stage_names: List of stage names in order
        reporter: Optional progress reporter

    Returns:
        Configured ProgressTracker instance

    """
    tracker = ProgressTracker(
        workflow_name=workflow_name,
        workflow_id=uuid.uuid4().hex[:12],
        stage_names=stage_names,
    )

    if reporter:
        tracker.add_callback(reporter.report)

    return tracker


class RichProgressReporter:
    """Rich-based live progress display with spinner, progress bar, and metrics.

    Provides real-time visual feedback during workflow execution:
    - Progress bar showing stage completion (1/3, 2/3, etc.)
    - Spinner during active LLM API calls
    - Real-time cost and token display
    - In-place updates (no terminal scrolling)

    Requires Rich library. Falls back gracefully if unavailable.
    """

    def __init__(self, workflow_name: str, stage_names: list[str]) -> None:
        """Initialize the Rich progress reporter.

        Args:
            workflow_name: Name of the workflow for display
            stage_names: List of stage names for progress tracking
        """
        if not RICH_AVAILABLE:
            raise RuntimeError("Rich library required for RichProgressReporter")

        self.workflow_name = workflow_name
        self.stage_names = stage_names
        self.console = Console()
        self._live: Live | None = None
        self._progress: Progress | None = None
        self._task_id: TaskID | None = None
        self._current_stage = ""
        self._cost = 0.0
        self._tokens = 0
        self._status = ProgressStatus.PENDING

    def start(self) -> None:
        """Start the live progress display."""
        if not RICH_AVAILABLE or Progress is None or Live is None:
            return

        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=30),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            console=self.console,
            transient=False,
        )

        self._task_id = self._progress.add_task(
            self.workflow_name,
            total=len(self.stage_names),
        )

        self._live = Live(
            self._create_display(),
            console=self.console,
            refresh_per_second=4,
            transient=False,
        )
        self._live.start()

    def stop(self) -> None:
        """Stop the live progress display."""
        if self._live:
            self._live.stop()
            self._live = None

    def report(self, update: ProgressUpdate) -> None:
        """Handle a progress update.

        Args:
            update: Progress update from the tracker
        """
        self._current_stage = update.current_stage
        self._cost = update.cost_so_far
        self._tokens = update.tokens_so_far
        self._status = update.status

        # Update progress bar
        if self._progress is not None and self._task_id is not None:
            completed = sum(
                1 for s in update.stages if s.status == ProgressStatus.COMPLETED
            )
            self._progress.update(
                self._task_id,
                completed=completed,
                description=f"{self.workflow_name}: {update.current_stage}",
            )

        # Refresh display
        if self._live:
            self._live.update(self._create_display())

    async def report_async(self, update: ProgressUpdate) -> None:
        """Async version of report."""
        self.report(update)

    def _create_display(self) -> Panel:
        """Create the Rich display panel.

        Returns:
            Rich Panel containing progress information
        """
        if not RICH_AVAILABLE or Panel is None or Table is None:
            raise RuntimeError("Rich not available")

        # Build metrics table
        metrics = Table(show_header=False, box=None, padding=(0, 2))
        metrics.add_column("Label", style="dim")
        metrics.add_column("Value", style="bold")

        metrics.add_row("Cost:", f"${self._cost:.4f}")
        metrics.add_row("Tokens:", f"{self._tokens:,}")
        metrics.add_row("Stage:", self._current_stage or "Starting...")

        # Status indicator
        status_style = {
            ProgressStatus.PENDING: "dim",
            ProgressStatus.RUNNING: "blue",
            ProgressStatus.COMPLETED: "green",
            ProgressStatus.FAILED: "red",
            ProgressStatus.FALLBACK: "yellow",
            ProgressStatus.RETRYING: "yellow",
        }.get(self._status, "white")

        status_text = Text(self._status.value.upper(), style=status_style)

        # Combine into panel
        if self._progress is not None:
            content = Group(self._progress, metrics)
        else:
            content = metrics

        return Panel(
            content,
            title=f"[bold]{self.workflow_name}[/bold]",
            subtitle=status_text,
            border_style=status_style,
        )

    def __enter__(self) -> RichProgressReporter:
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()


@contextmanager
def live_progress(
    workflow_name: str,
    stage_names: list[str],
    console: Console | None = None,
) -> Generator[tuple[ProgressTracker, RichProgressReporter | None], None, None]:
    """Context manager for live progress display during workflow execution.

    Provides a ProgressTracker with optional Rich-based live display.
    Falls back gracefully when Rich is unavailable or output is not a TTY.

    Args:
        workflow_name: Name of the workflow
        stage_names: List of stage names in order
        console: Optional Rich Console (creates new one if not provided)

    Yields:
        Tuple of (ProgressTracker, RichProgressReporter or None)

    Example:
        with live_progress("Code Review", ["analyze", "review", "summarize"]) as (tracker, _):
            tracker.start_workflow()
            for stage in stages:
                tracker.start_stage(stage)
                # ... do work ...
                tracker.complete_stage(stage, cost=0.01, tokens_in=100, tokens_out=50)
            tracker.complete_workflow()
    """
    tracker = ProgressTracker(
        workflow_name=workflow_name,
        workflow_id=uuid.uuid4().hex[:12],
        stage_names=stage_names,
    )

    reporter: RichProgressReporter | None = None

    # Use Rich if available and output is a TTY
    if RICH_AVAILABLE and sys.stdout.isatty():
        try:
            reporter = RichProgressReporter(workflow_name, stage_names)
            tracker.add_callback(reporter.report)
            reporter.start()
        except Exception:  # noqa: BLE001
            # INTENTIONAL: Rich display is optional - fall back to console output
            reporter = None
            simple_reporter = ConsoleProgressReporter(verbose=False)
            tracker.add_callback(simple_reporter.report)
    else:
        # No Rich or not a TTY - use simple console reporter
        simple_reporter = ConsoleProgressReporter(verbose=False)
        tracker.add_callback(simple_reporter.report)

    try:
        yield tracker, reporter
    finally:
        if reporter:
            reporter.stop()
