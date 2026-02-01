"""Session End Hook

Persists session state and triggers pattern evaluation.
Ported from everything-claude-code/scripts/hooks/session-end.js

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def get_sessions_dir() -> Path:
    """Get the sessions directory path."""
    return Path.home() / ".empathy" / "sessions"


def save_session_state(
    session_id: str,
    state: dict[str, Any],
) -> Path:
    """Save session state to a file.

    Args:
        session_id: Unique session identifier
        state: Session state to save

    Returns:
        Path to saved file

    """
    sessions_dir = get_sessions_dir()
    sessions_dir.mkdir(parents=True, exist_ok=True)

    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"session_{session_id}_{timestamp}.json"
    file_path = sessions_dir / filename

    # Add metadata
    state_with_meta = {
        **state,
        "saved_at": datetime.now().isoformat(),
        "session_id": session_id,
    }

    with open(file_path, "w") as f:
        json.dump(state_with_meta, f, indent=2, default=str)

    logger.info("Saved session state to %s", file_path)
    return file_path


def cleanup_old_sessions(max_sessions: int = 50) -> int:
    """Remove old session files beyond max_sessions.

    Args:
        max_sessions: Maximum number of session files to keep

    Returns:
        Number of files removed

    """
    sessions_dir = get_sessions_dir()

    if not sessions_dir.exists():
        return 0

    session_files = sorted(
        sessions_dir.glob("session_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    removed = 0
    for old_file in session_files[max_sessions:]:
        try:
            old_file.unlink()
            removed += 1
            logger.debug("Removed old session file: %s", old_file)
        except OSError as e:
            logger.warning("Failed to remove %s: %s", old_file, e)

    return removed


def main(**context: Any) -> dict[str, Any]:
    """Session end hook main function.

    Persists:
    - Trust level and collaboration state
    - Detected patterns and preferences
    - Interaction statistics

    Args:
        **context: Hook context with session state

    Returns:
        Session end summary

    """
    session_id = context.get("session_id", datetime.now().strftime("%Y%m%d%H%M%S"))

    # Extract state to persist
    state_to_save = {
        "trust_level": context.get("trust_level", 0.5),
        "empathy_level": context.get("empathy_level", 4),
        "interaction_count": context.get("interaction_count", 0),
        "detected_patterns": context.get("detected_patterns", []),
        "user_preferences": context.get("user_preferences", {}),
        "completed_phases": context.get("completed_phases", []),
        "pending_handoff": context.get("pending_handoff"),
        "metrics": {
            "success_rate": context.get("success_rate", 0),
            "total_tokens": context.get("total_tokens", 0),
            "total_cost": context.get("total_cost", 0),
        },
    }

    result = {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "state_saved": False,
        "file_path": None,
        "old_sessions_removed": 0,
        "evaluate_for_learning": False,
        "messages": [],
    }

    try:
        # Save session state
        file_path = save_session_state(session_id, state_to_save)
        result["state_saved"] = True
        result["file_path"] = str(file_path)
        result["messages"].append(f"[SessionEnd] State saved to {file_path.name}")

        # Cleanup old sessions
        removed = cleanup_old_sessions()
        result["old_sessions_removed"] = removed
        if removed > 0:
            result["messages"].append(f"[SessionEnd] Removed {removed} old session file(s)")

        # Check if session should be evaluated for learning
        min_interactions = context.get("min_learning_interactions", 10)
        if state_to_save["interaction_count"] >= min_interactions:
            result["evaluate_for_learning"] = True
            result["messages"].append(
                f"[SessionEnd] Session has {state_to_save['interaction_count']} "
                f"interactions - evaluate for pattern extraction"
            )

    except Exception as e:
        logger.error("Failed to save session state: %s", e)
        result["messages"].append(f"[SessionEnd] Error: {e}")

    # Log messages
    for msg in result["messages"]:
        logger.info(msg)

    return result


if __name__ == "__main__":
    # Allow running as a script for testing

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    # Simulate some context
    test_context = {
        "session_id": "test_session",
        "trust_level": 0.75,
        "interaction_count": 15,
        "detected_patterns": [{"type": "preference", "value": "concise responses"}],
    }

    result = main(**test_context)
    print(json.dumps(result, indent=2))
