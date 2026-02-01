"""Session Start Hook

Loads previous context and patterns on new session start.
Ported from everything-claude-code/scripts/hooks/session-start.js

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def get_sessions_dir() -> Path:
    """Get the sessions directory path."""
    return Path.home() / ".empathy" / "sessions"


def get_patterns_dir() -> Path:
    """Get the patterns directory path."""
    return Path.home() / ".empathy" / "patterns"


def get_learned_skills_dir() -> Path:
    """Get the learned skills directory path."""
    return Path.home() / ".empathy" / "skills" / "learned"


def find_recent_files(
    directory: Path,
    pattern: str = "*.json",
    max_age_days: int = 7,
) -> list[Path]:
    """Find files matching pattern modified within max_age_days.

    Args:
        directory: Directory to search
        pattern: Glob pattern for files
        max_age_days: Maximum file age in days

    Returns:
        List of matching file paths, sorted by modification time (newest first)

    """
    if not directory.exists():
        return []

    cutoff = datetime.now() - timedelta(days=max_age_days)
    matching = []

    for file_path in directory.glob(pattern):
        if file_path.is_file():
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            if mtime >= cutoff:
                matching.append((file_path, mtime))

    # Sort by modification time, newest first
    matching.sort(key=lambda x: x[1], reverse=True)
    return [path for path, _ in matching]


def load_session_state(session_file: Path) -> dict[str, Any] | None:
    """Load session state from a file.

    Args:
        session_file: Path to session state file

    Returns:
        Session state dict or None if failed

    """
    try:
        with open(session_file) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to load session state from %s: %s", session_file, e)
        return None


def main(**context: Any) -> dict[str, Any]:
    """Session start hook main function.

    Loads:
    - Previous session state (trust level, patterns, preferences)
    - Learned skills from previous sessions
    - Project-specific patterns

    Args:
        **context: Hook context (session_id, project_path, etc.)

    Returns:
        Session initialization data

    """
    sessions_dir = get_sessions_dir()
    patterns_dir = get_patterns_dir()
    learned_dir = get_learned_skills_dir()

    # Ensure directories exist
    sessions_dir.mkdir(parents=True, exist_ok=True)
    patterns_dir.mkdir(parents=True, exist_ok=True)
    learned_dir.mkdir(parents=True, exist_ok=True)

    result = {
        "initialized": True,
        "timestamp": datetime.now().isoformat(),
        "loaded_state": None,
        "learned_skills_count": 0,
        "patterns_count": 0,
        "messages": [],
    }

    # Find and load recent session state
    recent_sessions = find_recent_files(sessions_dir, "*.json", max_age_days=7)

    if recent_sessions:
        latest = recent_sessions[0]
        state = load_session_state(latest)

        if state:
            result["loaded_state"] = {
                "file": str(latest),
                "trust_level": state.get("trust_level"),
                "interaction_count": state.get("interaction_count", 0),
                "patterns_detected": len(state.get("detected_patterns", [])),
            }
            result["messages"].append(f"[SessionStart] Restored state from {latest.name}")
            logger.info("Loaded session state from %s", latest)

    # Count learned skills
    learned_skills = list(learned_dir.glob("*.md"))
    result["learned_skills_count"] = len(learned_skills)

    if learned_skills:
        result["messages"].append(
            f"[SessionStart] {len(learned_skills)} learned skill(s) available"
        )

    # Count patterns
    pattern_files = list(patterns_dir.glob("*.json"))
    result["patterns_count"] = len(pattern_files)

    if pattern_files:
        result["messages"].append(f"[SessionStart] {len(pattern_files)} pattern file(s) loaded")

    # Log summary
    for msg in result["messages"]:
        logger.info(msg)

    return result


if __name__ == "__main__":
    # Allow running as a script for testing

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    result = main()
    print(json.dumps(result, indent=2))
