"""Standalone Dashboard Server - Reads Directly from Redis.

This version bypasses the telemetry API layer and reads directly from Redis.
Works with data populated by scripts/populate_redis_direct.py.

Zero external dependencies (uses Python stdlib only).

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

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class StandaloneDashboardHandler(BaseHTTPRequestHandler):
    """HTTP handler that reads directly from Redis."""

    # Class variable for Redis connection (shared across requests)
    _redis_client = None

    @classmethod
    def get_redis(cls):
        """Get or create Redis connection."""
        if not REDIS_AVAILABLE:
            return None

        if cls._redis_client is None:
            try:
                cls._redis_client = redis.Redis(host="localhost", port=6379, decode_responses=False)
                cls._redis_client.ping()  # Test connection
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                cls._redis_client = None

        return cls._redis_client

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
    # API Endpoints - Read Directly from Redis
    # ========================================================================

    def api_health(self):
        """System health endpoint."""
        try:
            r = self.get_redis()
            has_redis = r is not None

            if has_redis:
                # Count keys directly
                heartbeat_count = len(r.keys(b"heartbeat:*"))
                approval_count = len(r.keys(b"approval:pending:*"))
            else:
                heartbeat_count = 0
                approval_count = 0

            self.send_json(
                {
                    "status": "healthy" if has_redis else "degraded",
                    "redis_available": has_redis,
                    "active_agents": heartbeat_count,
                    "pending_approvals": approval_count,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        except Exception as e:
            self.send_json({"status": "error", "error": str(e)}, status=500)

    def api_agents(self):
        """List active agents."""
        try:
            r = self.get_redis()
            if not r:
                self.send_json([])
                return

            result = []
            for key in r.keys(b"heartbeat:*"):
                try:
                    data = r.get(key)
                    if data:
                        heartbeat = json.loads(data.decode("utf-8"))
                        result.append(
                            {
                                "agent_id": heartbeat.get("agent_id"),
                                "status": heartbeat.get("status"),
                                "last_seen": heartbeat.get("timestamp"),
                                "progress": heartbeat.get("progress", 0.0),
                                "current_task": heartbeat.get("current_task", "Unknown"),
                            }
                        )
                except Exception as e:
                    logger.error(f"Failed to parse heartbeat {key}: {e}")

            self.send_json(result)
        except Exception as e:
            logger.error(f"Failed to get agents: {e}")
            self.send_json([], status=500)

    def api_agent_detail(self, agent_id: str):
        """Get specific agent details."""
        try:
            r = self.get_redis()
            if not r:
                self.send_json({"error": "Redis not available"}, status=503)
                return

            key = f"heartbeat:{agent_id}".encode()
            data = r.get(key)

            if not data:
                self.send_json({"error": f"Agent {agent_id} not found"}, status=404)
                return

            heartbeat = json.loads(data.decode("utf-8"))
            self.send_json(
                {
                    "agent_id": heartbeat.get("agent_id"),
                    "status": heartbeat.get("status"),
                    "last_seen": heartbeat.get("timestamp"),
                    "progress": heartbeat.get("progress", 0.0),
                    "current_task": heartbeat.get("current_task"),
                    "metadata": heartbeat.get("metadata", {}),
                }
            )
        except Exception as e:
            self.send_json({"error": str(e)}, status=500)

    def api_signals(self, limit: int):
        """Get recent coordination signals."""
        try:
            r = self.get_redis()
            if not r:
                self.send_json([])
                return

            result = []
            for key in r.keys(b"empathy:signal:*")[:limit]:
                try:
                    data = r.get(key)
                    if data:
                        signal = json.loads(data.decode("utf-8"))
                        result.append(
                            {
                                "signal_type": signal.get("signal_type"),
                                "source_agent": signal.get("source_agent"),
                                "target_agent": signal.get("target_agent"),
                                "timestamp": signal.get("timestamp"),
                                "payload": signal.get("payload", {}),
                            }
                        )
                except Exception as e:
                    logger.error(f"Failed to parse signal {key}: {e}")

            # Sort by timestamp (newest first)
            result.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            self.send_json(result[:limit])
        except Exception as e:
            logger.error(f"Failed to get signals: {e}")
            self.send_json([])

    def api_events(self, event_type: str | None, limit: int):
        """Get recent events."""
        try:
            r = self.get_redis()
            if not r:
                self.send_json([])
                return

            result = []

            # Get from streams
            stream_patterns = [
                b"stream:workflow_progress",
                b"stream:agent_heartbeat",
                b"stream:coordination_signal",
            ]

            for stream_key in stream_patterns:
                try:
                    # Get last N entries from stream
                    entries = r.xrevrange(stream_key, count=limit)
                    for entry_id, fields in entries:
                        if b"data" in fields:
                            event = json.loads(fields[b"data"].decode("utf-8"))
                            result.append(
                                {
                                    "event_id": event.get("event_id"),
                                    "event_type": event.get("event_type"),
                                    "timestamp": event.get("timestamp"),
                                    "data": event.get("data", {}),
                                    "source": event.get("source"),
                                }
                            )
                except Exception as e:
                    logger.debug(f"Stream {stream_key} not found or empty: {e}")

            # Sort by timestamp
            result.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            self.send_json(result[:limit])
        except Exception as e:
            logger.error(f"Failed to get events: {e}")
            self.send_json([])

    def api_approvals(self):
        """Get pending approvals."""
        try:
            r = self.get_redis()
            if not r:
                self.send_json([])
                return

            result = []
            for key in r.keys(b"approval:pending:*"):
                try:
                    data = r.get(key)
                    if data:
                        approval = json.loads(data.decode("utf-8"))
                        result.append(
                            {
                                "request_id": approval.get("request_id"),
                                "approval_type": approval.get("approval_type"),
                                "agent_id": approval.get("agent_id"),
                                "context": approval.get("context", {}),
                                "timestamp": approval.get("timestamp"),
                                "timeout_seconds": approval.get("timeout_seconds", 300),
                            }
                        )
                except Exception as e:
                    logger.error(f"Failed to parse approval {key}: {e}")

            self.send_json(result)
        except Exception as e:
            logger.error(f"Failed to get approvals: {e}")
            self.send_json([])

    def api_approve(self, request_id: str, reason: str):
        """Approve request."""
        try:
            r = self.get_redis()
            if not r:
                self.send_json({"error": "Redis not available"}, status=503)
                return

            # Delete from pending
            key = f"approval:pending:{request_id}".encode()
            if r.delete(key):
                self.send_json({"status": "approved", "request_id": request_id})
            else:
                self.send_json({"error": "Request not found"}, status=404)
        except Exception as e:
            self.send_json({"error": str(e)}, status=500)

    def api_reject(self, request_id: str, reason: str):
        """Reject request."""
        try:
            r = self.get_redis()
            if not r:
                self.send_json({"error": "Redis not available"}, status=503)
                return

            # Delete from pending
            key = f"approval:pending:{request_id}".encode()
            if r.delete(key):
                self.send_json({"status": "rejected", "request_id": request_id})
            else:
                self.send_json({"error": "Request not found"}, status=404)
        except Exception as e:
            self.send_json({"error": str(e)}, status=500)

    def api_feedback_workflows(self):
        """Get workflow quality metrics."""
        try:
            r = self.get_redis()
            if not r:
                self.send_json([])
                return

            # Group feedback by workflow/stage/tier
            feedback_groups = {}

            for key in r.keys(b"feedback:*"):
                try:
                    data = r.get(key)
                    if data:
                        feedback = json.loads(data.decode("utf-8"))
                        workflow = feedback.get("workflow_name")
                        stage = feedback.get("stage_name")
                        tier = feedback.get("tier")
                        quality = feedback.get("quality_score")

                        group_key = f"{workflow}/{stage}/{tier}"
                        if group_key not in feedback_groups:
                            feedback_groups[group_key] = {
                                "workflow_name": workflow,
                                "stage_name": stage,
                                "tier": tier,
                                "qualities": [],
                            }
                        feedback_groups[group_key]["qualities"].append(quality)
                except Exception as e:
                    logger.error(f"Failed to parse feedback {key}: {e}")

            # Calculate stats
            result = []
            for group_key, group in feedback_groups.items():
                qualities = group["qualities"]
                if qualities:
                    avg_quality = sum(qualities) / len(qualities)
                    result.append(
                        {
                            "workflow_name": group["workflow_name"],
                            "stage_name": group["stage_name"],
                            "tier": group["tier"],
                            "avg_quality": avg_quality,
                            "sample_count": len(qualities),
                            "trend": 0,  # Simplified - no trend calculation
                        }
                    )

            self.send_json(result)
        except Exception as e:
            logger.error(f"Failed to get quality metrics: {e}")
            self.send_json([])

    def api_underperforming(self, threshold: float):
        """Get underperforming stages."""
        try:
            r = self.get_redis()
            if not r:
                self.send_json([])
                return

            # Get all feedback and group by workflow/stage
            feedback_groups = {}

            for key in r.keys(b"feedback:*"):
                try:
                    data = r.get(key)
                    if data:
                        feedback = json.loads(data.decode("utf-8"))
                        workflow = feedback.get("workflow_name")
                        stage = feedback.get("stage_name")
                        quality = feedback.get("quality_score")

                        group_key = f"{workflow}/{stage}"
                        if group_key not in feedback_groups:
                            feedback_groups[group_key] = {
                                "workflow_name": workflow,
                                "stage_name": stage,
                                "qualities": [],
                            }
                        feedback_groups[group_key]["qualities"].append(quality)
                except Exception as e:
                    logger.error(f"Failed to parse feedback {key}: {e}")

            # Find underperforming stages
            result = []
            for group_key, group in feedback_groups.items():
                qualities = group["qualities"]
                if qualities:
                    avg_quality = sum(qualities) / len(qualities)
                    if avg_quality < threshold:
                        result.append(
                            {
                                "workflow_name": group["workflow_name"],
                                "stage_name": group["stage_name"],
                                "avg_quality": avg_quality,
                                "sample_count": len(qualities),
                                "min_quality": min(qualities),
                                "max_quality": max(qualities),
                                "trend": 0,
                            }
                        )

            # Sort by quality (worst first)
            result.sort(key=lambda x: x["avg_quality"])
            self.send_json(result)
        except Exception as e:
            logger.error(f"Failed to get underperforming: {e}")
            self.send_json([])

    def log_message(self, format, *args):
        """Suppress default logging."""
        # Override to reduce noise - only log errors
        if args[1][0] in ("4", "5"):  # 4xx or 5xx errors
            logger.warning(f"{self.address_string()} - {format % args}")


def run_standalone_dashboard(host: str = "127.0.0.1", port: int = 8000):
    """Run standalone dashboard that reads directly from Redis.

    This version bypasses the telemetry API layer and works with
    data populated by scripts/populate_redis_direct.py.

    Args:
        host: Host to bind to (default: 127.0.0.1)
        port: Port to bind to (default: 8000)

    Example:
        >>> from empathy_os.dashboard.standalone_server import run_standalone_dashboard
        >>> run_standalone_dashboard(host="0.0.0.0", port=8080)
    """
    if not REDIS_AVAILABLE:
        print("⚠️  Warning: redis-py not installed. Install with: pip install redis")
        print("   Dashboard will start but won't show data.")
        print()

    server = HTTPServer((host, port), StandaloneDashboardHandler)

    print(f"🚀 Agent Coordination Dashboard (Standalone) running at http://{host}:{port}")
    print(f"📊 Open in browser: http://{host}:{port}")
    print()
    print("💡 This version reads directly from Redis")
    print("   Populate data with: python scripts/populate_redis_direct.py")
    print()
    print("Press Ctrl+C to stop")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down dashboard...")
        server.shutdown()


if __name__ == "__main__":
    run_standalone_dashboard()
