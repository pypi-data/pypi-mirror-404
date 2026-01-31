"""Simple Dashboard Server - Zero External Dependencies.

Uses only Python standard library (http.server, json) to serve the dashboard.
No FastAPI, Flask, or other web frameworks required.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from empathy_os.telemetry import (
    ApprovalGate,
    CoordinationSignals,
    EventStreamer,
    FeedbackLoop,
    HeartbeatCoordinator,
)

logger = logging.getLogger(__name__)


class DashboardHandler(BaseHTTPRequestHandler):
    """HTTP request handler for dashboard."""

    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # Route requests
        if path == "/" or path == "/index.html":
            self.serve_file("index.html", "text/html")
        elif path == "/static/style.css":
            self.serve_file("style.css", "text/css")
        elif path == "/static/app.js":
            self.serve_file("app.js", "application/javascript")
        elif path == "/api/health":
            self.api_health()
        elif path == "/api/agents":
            self.api_agents()
        elif path.startswith("/api/agents/"):
            agent_id = path.split("/")[-1]
            self.api_agent_detail(agent_id)
        elif path == "/api/signals":
            limit = int(query.get("limit", [50])[0])
            self.api_signals(limit)
        elif path == "/api/events":
            event_type = query.get("event_type", [None])[0]
            limit = int(query.get("limit", [100])[0])
            self.api_events(event_type, limit)
        elif path == "/api/approvals":
            self.api_approvals()
        elif path == "/api/feedback/workflows":
            self.api_feedback_workflows()
        elif path == "/api/feedback/underperforming":
            threshold = float(query.get("threshold", [0.7])[0])
            self.api_underperforming(threshold)
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        """Handle POST requests."""
        parsed = urlparse(self.path)
        path = parsed.path

        # Get request body
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        data = json.loads(body.decode("utf-8")) if body else {}

        # Route requests
        if "/approve" in path:
            request_id = path.split("/")[-2]
            self.api_approve(request_id, data.get("reason", "Approved via dashboard"))
        elif "/reject" in path:
            request_id = path.split("/")[-2]
            self.api_reject(request_id, data.get("reason", "Rejected via dashboard"))
        else:
            self.send_error(404, "Not Found")

    def serve_file(self, filename: str, content_type: str):
        """Serve static file."""
        try:
            static_dir = Path(__file__).parent / "static"
            file_path = static_dir / filename

            if not file_path.exists():
                self.send_error(404, f"File not found: {filename}")
                return

            content = file_path.read_bytes()

            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        except Exception as e:
            logger.error(f"Failed to serve file {filename}: {e}")
            self.send_error(500, str(e))

    def send_json(self, data: dict | list, status: int = 200):
        """Send JSON response."""
        try:
            content = json.dumps(data).encode("utf-8")

            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Access-Control-Allow-Origin", "*")  # CORS
            self.end_headers()
            self.wfile.write(content)

        except Exception as e:
            logger.error(f"Failed to send JSON: {e}")
            self.send_error(500, str(e))

    # ========================================================================
    # API Endpoints
    # ========================================================================

    def api_health(self):
        """System health endpoint."""
        try:
            coordinator = HeartbeatCoordinator()
            has_redis = coordinator.memory is not None

            active_agents = len(coordinator.get_active_agents()) if has_redis else 0

            gate = ApprovalGate()
            pending_approvals = len(gate.get_pending_approvals()) if has_redis else 0

            self.send_json(
                {
                    "status": "healthy" if has_redis else "degraded",
                    "redis_available": has_redis,
                    "active_agents": active_agents,
                    "pending_approvals": pending_approvals,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        except Exception as e:
            self.send_json({"status": "error", "error": str(e)}, status=500)

    def api_agents(self):
        """List active agents."""
        try:
            coordinator = HeartbeatCoordinator()
            active_agents = coordinator.get_active_agents()

            result = []
            for agent_id in active_agents:
                heartbeat = coordinator.get_heartbeat(agent_id)
                if heartbeat:
                    result.append(
                        {
                            "agent_id": agent_id,
                            "status": heartbeat.status,
                            "last_seen": heartbeat.timestamp.isoformat(),
                            "progress": heartbeat.progress,
                            "current_task": heartbeat.current_task,
                        }
                    )

            self.send_json(result)
        except Exception as e:
            logger.error(f"Failed to get agents: {e}")
            self.send_json([], status=500)

    def api_agent_detail(self, agent_id: str):
        """Get specific agent details."""
        try:
            coordinator = HeartbeatCoordinator()
            heartbeat = coordinator.get_heartbeat(agent_id)

            if not heartbeat:
                self.send_json({"error": f"Agent {agent_id} not found"}, status=404)
                return

            self.send_json(
                {
                    "agent_id": agent_id,
                    "status": heartbeat.status,
                    "last_seen": heartbeat.timestamp.isoformat(),
                    "progress": heartbeat.progress,
                    "current_task": heartbeat.current_task,
                    "metadata": heartbeat.metadata,
                }
            )
        except Exception as e:
            self.send_json({"error": str(e)}, status=500)

    def api_signals(self, limit: int):
        """Get recent coordination signals."""
        try:
            signals = CoordinationSignals()
            recent = signals.get_recent_signals(limit=limit)

            result = [
                {
                    "signal_type": sig.signal_type,
                    "source_agent": sig.source_agent,
                    "target_agent": sig.target_agent,
                    "timestamp": sig.timestamp.isoformat(),
                    "payload": sig.payload,
                }
                for sig in recent
            ]

            self.send_json(result)
        except Exception as e:
            logger.error(f"Failed to get signals: {e}")
            self.send_json([])

    def api_events(self, event_type: str | None, limit: int):
        """Get recent events."""
        try:
            streamer = EventStreamer()

            if event_type:
                events = list(streamer.get_recent_events(event_type, limit=limit))
            else:
                # Get events from multiple streams
                all_events = []
                for evt_type in ["agent_heartbeat", "coordination_signal", "workflow_progress"]:
                    events = list(streamer.get_recent_events(evt_type, limit=20))
                    all_events.extend(events)

                all_events.sort(key=lambda e: e.timestamp, reverse=True)
                events = all_events[:limit]

            result = [
                {
                    "event_id": evt.event_id,
                    "event_type": evt.event_type,
                    "timestamp": evt.timestamp.isoformat(),
                    "data": evt.data,
                    "source": evt.source,
                }
                for evt in events
            ]

            self.send_json(result)
        except Exception as e:
            logger.error(f"Failed to get events: {e}")
            self.send_json([])

    def api_approvals(self):
        """Get pending approvals."""
        try:
            gate = ApprovalGate()
            pending = gate.get_pending_approvals()

            result = [
                {
                    "request_id": req.request_id,
                    "approval_type": req.approval_type,
                    "agent_id": req.agent_id,
                    "context": req.context,
                    "timestamp": req.timestamp.isoformat(),
                    "timeout_seconds": req.timeout_seconds,
                }
                for req in pending
            ]

            self.send_json(result)
        except Exception as e:
            logger.error(f"Failed to get approvals: {e}")
            self.send_json([])

    def api_approve(self, request_id: str, reason: str):
        """Approve request."""
        try:
            gate = ApprovalGate()
            success = gate.respond_to_approval(
                request_id=request_id, approved=True, responder="dashboard", reason=reason
            )

            if success:
                self.send_json({"status": "approved", "request_id": request_id})
            else:
                self.send_json({"error": "Failed to approve"}, status=500)
        except Exception as e:
            self.send_json({"error": str(e)}, status=500)

    def api_reject(self, request_id: str, reason: str):
        """Reject request."""
        try:
            gate = ApprovalGate()
            success = gate.respond_to_approval(
                request_id=request_id, approved=False, responder="dashboard", reason=reason
            )

            if success:
                self.send_json({"status": "rejected", "request_id": request_id})
            else:
                self.send_json({"error": "Failed to reject"}, status=500)
        except Exception as e:
            self.send_json({"error": str(e)}, status=500)

    def api_feedback_workflows(self):
        """Get workflow quality metrics."""
        try:
            feedback = FeedbackLoop()

            workflows = ["code-review", "test-generation", "refactoring"]
            results = []

            for workflow in workflows:
                for stage in ["analysis", "generation", "validation"]:
                    for tier in ["cheap", "capable", "premium"]:
                        stats = feedback.get_quality_stats(workflow, stage, tier=tier)
                        if stats and stats.sample_count > 0:
                            results.append(
                                {
                                    "workflow_name": workflow,
                                    "stage_name": stage,
                                    "tier": tier,
                                    "avg_quality": stats.avg_quality,
                                    "sample_count": stats.sample_count,
                                    "trend": stats.recent_trend,
                                }
                            )

            self.send_json(results)
        except Exception as e:
            logger.error(f"Failed to get quality metrics: {e}")
            self.send_json([])

    def api_underperforming(self, threshold: float):
        """Get underperforming stages."""
        try:
            feedback = FeedbackLoop()

            workflows = ["code-review", "test-generation", "refactoring"]
            all_underperforming = []

            for workflow in workflows:
                underperforming = feedback.get_underperforming_stages(workflow, quality_threshold=threshold)
                for stage_name, stats in underperforming:
                    all_underperforming.append(
                        {
                            "workflow_name": workflow,
                            "stage_name": stage_name,
                            "avg_quality": stats.avg_quality,
                            "sample_count": stats.sample_count,
                            "min_quality": stats.min_quality,
                            "max_quality": stats.max_quality,
                            "trend": stats.recent_trend,
                        }
                    )

            all_underperforming.sort(key=lambda x: x["avg_quality"])
            self.send_json(all_underperforming)
        except Exception as e:
            logger.error(f"Failed to get underperforming: {e}")
            self.send_json([])

    def log_message(self, format, *args):
        """Suppress default logging."""
        # Override to reduce noise - only log errors
        if args[1][0] in ("4", "5"):  # 4xx or 5xx errors
            logger.warning(f"{self.address_string()} - {format % args}")


def run_simple_dashboard(host: str = "127.0.0.1", port: int = 8000):
    """Run dashboard using only Python standard library.

    No external dependencies required (no FastAPI, Flask, etc).

    Args:
        host: Host to bind to (default: 127.0.0.1)
        port: Port to bind to (default: 8000)

    Example:
        >>> from empathy_os.dashboard.simple_server import run_simple_dashboard
        >>> run_simple_dashboard(host="0.0.0.0", port=8080)
    """
    server = HTTPServer((host, port), DashboardHandler)

    print(f"🚀 Agent Coordination Dashboard running at http://{host}:{port}")
    print(f"📊 Open in browser: http://{host}:{port}")
    print("Press Ctrl+C to stop")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down dashboard...")
        server.shutdown()


if __name__ == "__main__":
    run_simple_dashboard()
