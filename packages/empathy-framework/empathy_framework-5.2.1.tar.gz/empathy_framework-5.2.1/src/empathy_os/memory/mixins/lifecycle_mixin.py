"""Lifecycle management mixin for UnifiedMemory.

Provides resource cleanup and context manager protocol.

Copyright 2025 Smart AI Memory, LLC
Licensed under Fair Source 0.9
"""

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from ..file_session import FileSessionMemory
    from ..short_term import RedisShortTermMemory

logger = structlog.get_logger(__name__)


class LifecycleMixin:
    """Mixin providing lifecycle management for UnifiedMemory."""

    # Type hints for attributes that will be provided by UnifiedMemory
    _file_session: "FileSessionMemory | None"
    _short_term: "RedisShortTermMemory | None"

    def save(self) -> None:
        """Explicitly save all memory state."""
        if self._file_session:
            self._file_session.save()
        logger.debug("memory_saved")

    def close(self) -> None:
        """Close all memory backends and save state."""
        if self._file_session:
            self._file_session.close()

        if self._short_term and hasattr(self._short_term, "close"):
            self._short_term.close()

        logger.info("unified_memory_closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - close all backends."""
        self.close()
