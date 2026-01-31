"""Configuration for hot-reload system.

Copyright 2025 Smart AI Memory, LLC
Licensed under Fair Source 0.9
"""

import os
from pathlib import Path


class HotReloadConfig:
    """Configuration for hot-reload system."""

    def __init__(self):
        """Initialize configuration from environment."""
        # Development mode (enables hot-reload)
        self.enabled = os.getenv("HOT_RELOAD_ENABLED", "false").lower() == "true"

        # Workflow directories to watch
        self.watch_dirs = self._get_watch_dirs()

        # WebSocket endpoint for notifications
        self.websocket_path = os.getenv("HOT_RELOAD_WS_PATH", "/ws/hot-reload")

        # Reload delay (seconds) to debounce multiple file changes
        self.reload_delay = float(os.getenv("HOT_RELOAD_DELAY", "0.5"))

    def _get_watch_dirs(self) -> list[Path]:
        """Get directories to watch for workflow changes.

        Returns:
            List of directories to watch

        """
        # Default workflow directories
        project_root = Path(__file__).parent.parent

        default_dirs = [
            project_root / "workflows",
            project_root / "empathy_software_plugin" / "workflows",
            project_root / "empathy_llm_toolkit" / "workflows",
        ]

        # Filter to only existing directories
        watch_dirs = [d for d in default_dirs if d.exists()]

        # Allow override via environment variable
        env_dirs = os.getenv("HOT_RELOAD_WATCH_DIRS")
        if env_dirs:
            watch_dirs = [Path(d.strip()) for d in env_dirs.split(",")]

        return watch_dirs

    def to_dict(self) -> dict:
        """Convert config to dictionary.

        Returns:
            Configuration as dictionary

        """
        return {
            "enabled": self.enabled,
            "watch_dirs": [str(d) for d in self.watch_dirs],
            "websocket_path": self.websocket_path,
            "reload_delay": self.reload_delay,
        }


# Global config instance
_config: HotReloadConfig | None = None


def get_hot_reload_config() -> HotReloadConfig:
    """Get the global hot-reload configuration.

    Returns:
        Global HotReloadConfig instance

    """
    global _config
    if _config is None:
        _config = HotReloadConfig()
    return _config
