"""Agent-to-LLM Feedback Loop for Quality-Based Learning.

Pattern 6 from Agent Coordination Architecture - Collect quality ratings
on LLM responses and use feedback to inform routing decisions.

Usage:
    # Record feedback after LLM response
    feedback = FeedbackLoop()
    feedback.record_feedback(
        workflow_name="code-review",
        stage_name="analysis",
        tier=ModelTier.CHEAP,
        quality_score=0.8,
        metadata={
            "response_length": 500,
            "tokens": 150,
            "latency_ms": 1200
        }
    )

    # Get tier recommendation based on historical performance
    recommendation = feedback.recommend_tier(
        workflow_name="code-review",
        stage_name="analysis"
    )
    if recommendation.recommended_tier == ModelTier.CAPABLE:
        print(f"Upgrade to CAPABLE tier (confidence: {recommendation.confidence})")

    # Get quality stats for analysis
    stats = feedback.get_quality_stats(
        workflow_name="code-review",
        stage_name="analysis"
    )
    print(f"Average quality: {stats.avg_quality}")

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


class ModelTier(str, Enum):
    """Model tier enum matching workflows.base.ModelTier."""

    CHEAP = "cheap"
    CAPABLE = "capable"
    PREMIUM = "premium"


@dataclass
class FeedbackEntry:
    """Quality feedback for an LLM response.

    Represents a single quality rating for a workflow stage execution.
    """

    feedback_id: str
    workflow_name: str
    stage_name: str
    tier: str  # ModelTier value
    quality_score: float  # 0.0 (bad) to 1.0 (excellent)
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "feedback_id": self.feedback_id,
            "workflow_name": self.workflow_name,
            "stage_name": self.stage_name,
            "tier": self.tier,
            "quality_score": self.quality_score,
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FeedbackEntry:
        """Create from dictionary."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif not isinstance(timestamp, datetime):
            timestamp = datetime.utcnow()

        return cls(
            feedback_id=data["feedback_id"],
            workflow_name=data["workflow_name"],
            stage_name=data["stage_name"],
            tier=data["tier"],
            quality_score=data["quality_score"],
            timestamp=timestamp,
            metadata=data.get("metadata", {}),
        )


@dataclass
class QualityStats:
    """Quality statistics for a workflow stage."""

    workflow_name: str
    stage_name: str
    tier: str
    avg_quality: float
    min_quality: float
    max_quality: float
    sample_count: int
    recent_trend: float  # -1.0 (declining) to 1.0 (improving)


@dataclass
class TierRecommendation:
    """Tier recommendation based on quality feedback."""

    current_tier: str
    recommended_tier: str
    confidence: float  # 0.0 (low) to 1.0 (high)
    reason: str
    stats: dict[str, QualityStats]  # Stats by tier


class FeedbackLoop:
    """Agent-to-LLM feedback loop for quality-based learning.

    Collects quality ratings on LLM responses and uses feedback to:
    - Recommend tier upgrades/downgrades
    - Track quality trends over time
    - Identify underperforming stages
    - Optimize routing based on historical performance

    Attributes:
        FEEDBACK_TTL: Feedback entry TTL (7 days)
        MIN_SAMPLES: Minimum samples for recommendation (10)
        QUALITY_THRESHOLD: Quality threshold for tier upgrade (0.7)
    """

    FEEDBACK_TTL = 604800  # 7 days (60*60*24*7)
    MIN_SAMPLES = 10  # Minimum samples for recommendation
    QUALITY_THRESHOLD = 0.7  # Quality below this triggers upgrade recommendation

    def __init__(self, memory=None):
        """Initialize feedback loop.

        Args:
            memory: Memory instance for storing feedback
        """
        self.memory = memory

        if self.memory is None:
            try:
                from empathy_os.telemetry import UsageTracker

                tracker = UsageTracker.get_instance()
                if hasattr(tracker, "_memory"):
                    self.memory = tracker._memory
            except (ImportError, AttributeError):
                pass

        if self.memory is None:
            logger.warning("No memory backend available for feedback loop")

    def record_feedback(
        self,
        workflow_name: str,
        stage_name: str,
        tier: str | ModelTier,
        quality_score: float,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Record quality feedback for a workflow stage execution.

        Args:
            workflow_name: Name of workflow
            stage_name: Name of stage within workflow
            tier: Model tier used (CHEAP, CAPABLE, PREMIUM)
            quality_score: Quality rating 0.0-1.0 (0=bad, 1=excellent)
            metadata: Optional metadata (tokens, latency, etc.)

        Returns:
            Feedback ID if stored, empty string otherwise

        Example:
            >>> feedback = FeedbackLoop()
            >>> feedback.record_feedback(
            ...     workflow_name="code-review",
            ...     stage_name="analysis",
            ...     tier=ModelTier.CHEAP,
            ...     quality_score=0.85,
            ...     metadata={"tokens": 150, "latency_ms": 1200}
            ... )
        """
        if not self.memory:
            logger.debug("Cannot record feedback: no memory backend")
            return ""

        # Validate quality score
        if not 0.0 <= quality_score <= 1.0:
            logger.warning(f"Invalid quality score: {quality_score} (must be 0.0-1.0)")
            return ""

        # Convert tier to string if ModelTier enum
        if isinstance(tier, ModelTier):
            tier = tier.value

        feedback_id = f"feedback_{uuid4().hex[:8]}"

        entry = FeedbackEntry(
            feedback_id=feedback_id,
            workflow_name=workflow_name,
            stage_name=stage_name,
            tier=tier,
            quality_score=quality_score,
            timestamp=datetime.utcnow(),
            metadata=metadata or {},
        )

        # Store feedback
        # Key format: feedback:{workflow}:{stage}:{tier}:{id}
        key = f"feedback:{workflow_name}:{stage_name}:{tier}:{feedback_id}"

        try:
            # Use direct Redis access for custom TTL
            if hasattr(self.memory, "_client") and self.memory._client:
                import json

                self.memory._client.setex(key, self.FEEDBACK_TTL, json.dumps(entry.to_dict()))
            else:
                logger.warning("Cannot store feedback: no Redis backend available")
                return ""
        except Exception as e:
            logger.error(f"Failed to store feedback: {e}")
            return ""

        logger.debug(
            f"Recorded feedback: {workflow_name}/{stage_name} tier={tier} quality={quality_score:.2f}"
        )
        return feedback_id

    def get_feedback_history(
        self, workflow_name: str, stage_name: str, tier: str | ModelTier | None = None, limit: int = 100
    ) -> list[FeedbackEntry]:
        """Get feedback history for a workflow stage.

        Args:
            workflow_name: Name of workflow
            stage_name: Name of stage
            tier: Optional filter by tier
            limit: Maximum number of entries to return

        Returns:
            List of feedback entries (newest first)
        """
        if not self.memory or not hasattr(self.memory, "_client"):
            return []

        # Convert tier to string if ModelTier enum
        if isinstance(tier, ModelTier):
            tier = tier.value

        try:
            # Build search pattern
            if tier:
                pattern = f"feedback:{workflow_name}:{stage_name}:{tier}:*"
            else:
                pattern = f"feedback:{workflow_name}:{stage_name}:*"

            keys = self.memory._client.keys(pattern)

            entries = []
            for key in keys:
                if isinstance(key, bytes):
                    key = key.decode("utf-8")

                # Retrieve entry
                data = self._retrieve_feedback(key)
                if data:
                    entries.append(FeedbackEntry.from_dict(data))

                if len(entries) >= limit:
                    break

            # Sort by timestamp (newest first)
            entries.sort(key=lambda e: e.timestamp, reverse=True)

            return entries[:limit]
        except Exception as e:
            logger.error(f"Failed to get feedback history: {e}")
            return []

    def _retrieve_feedback(self, key: str) -> dict[str, Any] | None:
        """Retrieve feedback entry from memory."""
        if not self.memory:
            return None

        try:
            if hasattr(self.memory, "retrieve"):
                return self.memory.retrieve(key, credentials=None)
            elif hasattr(self.memory, "_client"):
                import json

                data = self.memory._client.get(key)
                if data:
                    if isinstance(data, bytes):
                        data = data.decode("utf-8")
                    return json.loads(data)
            return None
        except Exception as e:
            logger.debug(f"Failed to retrieve feedback: {e}")
            return None

    def get_quality_stats(
        self, workflow_name: str, stage_name: str, tier: str | ModelTier | None = None
    ) -> QualityStats | None:
        """Get quality statistics for a workflow stage.

        Args:
            workflow_name: Name of workflow
            stage_name: Name of stage
            tier: Optional filter by tier

        Returns:
            Quality statistics or None if insufficient data
        """
        history = self.get_feedback_history(workflow_name, stage_name, tier=tier)

        if not history:
            return None

        # Calculate statistics
        quality_scores = [entry.quality_score for entry in history]

        avg_quality = sum(quality_scores) / len(quality_scores)
        min_quality = min(quality_scores)
        max_quality = max(quality_scores)

        # Calculate trend (recent vs older feedback)
        if len(history) >= 4:
            recent = quality_scores[: len(quality_scores) // 2]
            older = quality_scores[len(quality_scores) // 2 :]
            recent_avg = sum(recent) / len(recent)
            older_avg = sum(older) / len(older)
            recent_trend = (recent_avg - older_avg) / max(older_avg, 0.1)  # Normalized difference
        else:
            recent_trend = 0.0

        tier_str = tier.value if isinstance(tier, ModelTier) else (tier or "all")

        return QualityStats(
            workflow_name=workflow_name,
            stage_name=stage_name,
            tier=tier_str,
            avg_quality=avg_quality,
            min_quality=min_quality,
            max_quality=max_quality,
            sample_count=len(history),
            recent_trend=recent_trend,
        )

    def recommend_tier(
        self, workflow_name: str, stage_name: str, current_tier: str | ModelTier | None = None
    ) -> TierRecommendation:
        """Recommend optimal tier based on quality feedback.

        Analyzes historical quality data and recommends:
        - Downgrade if current tier consistently delivers high quality (cost optimization)
        - Upgrade if current tier delivers poor quality (quality optimization)
        - Keep current if quality is acceptable

        Args:
            workflow_name: Name of workflow
            stage_name: Name of stage
            current_tier: Current tier in use (if known)

        Returns:
            Tier recommendation with confidence and reasoning
        """
        # Convert tier to string if ModelTier enum
        if isinstance(current_tier, ModelTier):
            current_tier = current_tier.value

        # Get stats for all tiers
        stats_by_tier = {}
        for tier in ["cheap", "capable", "premium"]:
            stats = self.get_quality_stats(workflow_name, stage_name, tier=tier)
            if stats:
                stats_by_tier[tier] = stats

        # No data - default recommendation
        if not stats_by_tier:
            return TierRecommendation(
                current_tier=current_tier or "unknown",
                recommended_tier=current_tier or "cheap",
                confidence=0.0,
                reason="No feedback data available",
                stats={},
            )

        # Determine current tier if not provided
        if not current_tier:
            # Use tier with most recent feedback
            all_history = self.get_feedback_history(workflow_name, stage_name, tier=None, limit=1)
            if all_history:
                current_tier = all_history[0].tier
            else:
                current_tier = "cheap"

        current_stats = stats_by_tier.get(current_tier)

        # Insufficient data for current tier
        if not current_stats or current_stats.sample_count < self.MIN_SAMPLES:
            return TierRecommendation(
                current_tier=current_tier,
                recommended_tier=current_tier,
                confidence=0.0,
                reason=f"Insufficient data (need {self.MIN_SAMPLES} samples, have {current_stats.sample_count if current_stats else 0})",
                stats=stats_by_tier,
            )

        # Analyze quality
        avg_quality = current_stats.avg_quality
        confidence = min(current_stats.sample_count / (self.MIN_SAMPLES * 2), 1.0)

        # Decision logic
        if avg_quality < self.QUALITY_THRESHOLD:
            # Poor quality - recommend upgrade
            if current_tier == "cheap":
                recommended = "capable"
                reason = f"Low quality ({avg_quality:.2f}) - upgrade for better results"
            elif current_tier == "capable":
                recommended = "premium"
                reason = f"Low quality ({avg_quality:.2f}) - upgrade to premium tier"
            else:  # premium
                recommended = "premium"
                reason = f"Already using premium tier (quality: {avg_quality:.2f})"
                confidence = 1.0
        elif avg_quality > 0.9 and current_tier != "cheap":
            # Excellent quality - consider downgrade for cost optimization
            if current_tier == "premium":
                # Check if capable tier also has good quality
                capable_stats = stats_by_tier.get("capable")
                if capable_stats and capable_stats.avg_quality > 0.85:
                    recommended = "capable"
                    reason = f"Excellent quality ({avg_quality:.2f}) - downgrade to save cost"
                else:
                    recommended = "premium"
                    reason = f"Excellent quality ({avg_quality:.2f}) - keep premium for consistency"
            elif current_tier == "capable":
                # Check if cheap tier also has good quality
                cheap_stats = stats_by_tier.get("cheap")
                if cheap_stats and cheap_stats.avg_quality > 0.85:
                    recommended = "cheap"
                    reason = f"Excellent quality ({avg_quality:.2f}) - downgrade to save cost"
                else:
                    recommended = "capable"
                    reason = f"Excellent quality ({avg_quality:.2f}) - keep capable tier"
            else:
                recommended = current_tier
                reason = f"Excellent quality ({avg_quality:.2f}) - maintain current tier"
        else:
            # Acceptable quality - keep current tier
            recommended = current_tier
            reason = f"Acceptable quality ({avg_quality:.2f}) - maintain current tier"

        return TierRecommendation(
            current_tier=current_tier,
            recommended_tier=recommended,
            confidence=confidence,
            reason=reason,
            stats=stats_by_tier,
        )

    def get_underperforming_stages(
        self, workflow_name: str, quality_threshold: float = 0.7
    ) -> list[tuple[str, QualityStats]]:
        """Get workflow stages with poor quality scores.

        Args:
            workflow_name: Name of workflow
            quality_threshold: Threshold below which stage is considered underperforming

        Returns:
            List of (stage_name, stats) tuples for underperforming stages
        """
        if not self.memory or not hasattr(self.memory, "_client"):
            return []

        try:
            # Find all feedback keys for this workflow
            pattern = f"feedback:{workflow_name}:*"
            keys = self.memory._client.keys(pattern)

            # Extract unique stages
            stages = set()
            for key in keys:
                if isinstance(key, bytes):
                    key = key.decode("utf-8")
                # Parse key: feedback:{workflow}:{stage}:{tier}:{id}
                parts = key.split(":")
                if len(parts) >= 4:
                    stages.add(parts[2])

            # Get stats for each stage
            underperforming = []
            for stage_name in stages:
                stats = self.get_quality_stats(workflow_name, stage_name)
                if stats and stats.avg_quality < quality_threshold:
                    underperforming.append((stage_name, stats))

            # Sort by quality (worst first)
            underperforming.sort(key=lambda x: x[1].avg_quality)

            return underperforming
        except Exception as e:
            logger.error(f"Failed to get underperforming stages: {e}")
            return []

    def clear_feedback(self, workflow_name: str, stage_name: str | None = None) -> int:
        """Clear feedback history for a workflow or stage.

        Args:
            workflow_name: Name of workflow
            stage_name: Optional stage name (clears all stages if None)

        Returns:
            Number of feedback entries cleared
        """
        if not self.memory or not hasattr(self.memory, "_client"):
            return 0

        try:
            if stage_name:
                pattern = f"feedback:{workflow_name}:{stage_name}:*"
            else:
                pattern = f"feedback:{workflow_name}:*"

            keys = self.memory._client.keys(pattern)
            if not keys:
                return 0

            deleted = self.memory._client.delete(*keys)
            return deleted
        except Exception as e:
            logger.error(f"Failed to clear feedback: {e}")
            return 0
