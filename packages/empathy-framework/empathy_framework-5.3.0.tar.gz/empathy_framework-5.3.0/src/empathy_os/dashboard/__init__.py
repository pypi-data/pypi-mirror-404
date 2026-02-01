"""Agent Coordination Dashboard.

Web-based monitoring dashboard for all 6 agent coordination patterns.

Usage (Standalone - Direct Redis Access):
    >>> from empathy_os.dashboard import run_standalone_dashboard
    >>> run_standalone_dashboard(host="0.0.0.0", port=8080)

Usage (Simple Server - Uses Telemetry API):
    >>> from empathy_os.dashboard import run_simple_dashboard
    >>> run_simple_dashboard(host="0.0.0.0", port=8080)

Usage (FastAPI - Requires fastapi and uvicorn):
    >>> from empathy_os.dashboard import run_dashboard
    >>> run_dashboard(host="0.0.0.0", port=8080)

Features:
- Real-time agent status monitoring (Pattern 1)
- Coordination signal viewer (Pattern 2)
- Event stream monitor (Pattern 4)
- Approval request manager (Pattern 5)
- Quality feedback analytics (Pattern 6)
- Auto-refresh every 5 seconds

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

# Standalone server - reads directly from Redis
# Simple server - uses telemetry API classes
from .simple_server import run_simple_dashboard
from .standalone_server import run_standalone_dashboard

# Optional FastAPI version (requires dependencies)
try:
    from .app import app, run_dashboard

    __all__ = ["app", "run_dashboard", "run_simple_dashboard", "run_standalone_dashboard"]
except ImportError:
    # FastAPI not installed
    __all__ = ["run_simple_dashboard", "run_standalone_dashboard"]
