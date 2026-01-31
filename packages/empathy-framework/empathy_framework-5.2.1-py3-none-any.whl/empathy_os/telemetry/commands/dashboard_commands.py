"""Dashboard command implementations for telemetry CLI.

Provides interactive HTML dashboard generation for telemetry data.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

import http.server
import socketserver
import tempfile
import webbrowser
from collections import Counter
from datetime import datetime
from typing import Any

from ..usage_tracker import UsageTracker


def cmd_telemetry_dashboard(args: Any) -> int:
    """Open interactive telemetry dashboard in browser.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success)

    """
    tracker = UsageTracker.get_instance()
    entries = tracker.export_to_dict(days=getattr(args, "days", 30))

    if not entries:
        print("No telemetry data available.")
        return 0

    # Calculate statistics
    total_cost = sum(e.get("cost", 0) for e in entries)
    total_calls = len(entries)
    avg_duration = (
        sum(e.get("duration_ms", 0) for e in entries) / total_calls if total_calls > 0 else 0
    )

    # Tier distribution
    tiers = [e.get("tier", "UNKNOWN") for e in entries]
    tier_counts = Counter(tiers)
    tier_distribution = {tier: (count / total_calls) * 100 for tier, count in tier_counts.items()}

    # Calculate savings (baseline: all PREMIUM tier)
    premium_input_cost = 0.015 / 1000  # per token
    premium_output_cost = 0.075 / 1000  # per token

    baseline_cost = sum(
        (e.get("tokens", {}).get("input", 0) * premium_input_cost)
        + (e.get("tokens", {}).get("output", 0) * premium_output_cost)
        for e in entries
    )

    saved = baseline_cost - total_cost
    savings_pct = (saved / baseline_cost * 100) if baseline_cost > 0 else 0

    # Generate HTML
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Empathy Telemetry Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        .header {{
            color: white;
            text-align: center;
            margin-bottom: 40px;
        }}
        .header h1 {{
            font-size: 48px;
            font-weight: 700;
            margin-bottom: 10px;
        }}
        .header p {{
            font-size: 18px;
            opacity: 0.9;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .savings-card {{
            grid-column: span 2;
            background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
            color: white;
        }}
        .stat-label {{
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
            opacity: 0.8;
        }}
        .stat-value {{
            font-size: 56px;
            font-weight: 700;
            margin-bottom: 5px;
        }}
        .stat-sublabel {{
            font-size: 16px;
            opacity: 0.7;
        }}
        .tier-distribution {{
            display: flex;
            gap: 10px;
            margin-top: 15px;
            height: 50px;
        }}
        .tier-bar {{
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 8px;
            font-weight: 600;
            color: white;
            font-size: 14px;
        }}
        .tier-premium {{ background: linear-gradient(135deg, #9c27b0, #7b1fa2); }}
        .tier-capable {{ background: linear-gradient(135deg, #2196f3, #1976d2); }}
        .tier-cheap {{ background: linear-gradient(135deg, #4caf50, #388e3c); }}
        table {{
            width: 100%;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        th, td {{
            padding: 16px;
            text-align: left;
        }}
        th {{
            background: #f5f5f5;
            font-weight: 600;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #666;
        }}
        tr:hover {{
            background: #f9f9f9;
        }}
        .tier-badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            color: white;
        }}
        .badge-premium {{ background: #9c27b0; }}
        .badge-capable {{ background: #2196f3; }}
        .badge-cheap {{ background: #4caf50; }}
        .cache-hit {{ color: #4caf50; font-weight: 600; }}
        .cache-miss {{ color: #999; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Empathy Telemetry Dashboard</h1>
            <p>Last {len(entries)} LLM API calls • Real-time cost tracking</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card savings-card">
                <div class="stat-label">Cost Savings (Tier Routing)</div>
                <div class="stat-value">${saved:.2f}</div>
                <div class="stat-sublabel">
                    {savings_pct:.1f}% saved • Baseline: ${baseline_cost:.2f} • Actual: ${
        total_cost:.2f}
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-label">Total Cost</div>
                <div class="stat-value">${total_cost:.2f}</div>
                <div class="stat-sublabel">{total_calls} API calls</div>
            </div>

            <div class="stat-card">
                <div class="stat-label">Avg Duration</div>
                <div class="stat-value">{avg_duration / 1000:.1f}s</div>
                <div class="stat-sublabel">Per API call</div>
            </div>
        </div>

        <div class="stat-card">
            <div class="stat-label">Tier Distribution</div>
            <div class="tier-distribution">
                {
        "".join(
            f'<div class="tier-bar tier-{tier.lower()}">{tier}: {pct:.1f}%</div>'
            for tier, pct in tier_distribution.items()
        )
    }
            </div>
        </div>

        <h2 style="color: white; margin: 40px 0 20px 0; font-size: 28px;">Recent LLM Calls</h2>
        <table>
            <thead>
                <tr>
                    <th>Time</th>
                    <th>Workflow</th>
                    <th>Stage</th>
                    <th>Tier</th>
                    <th>Cost</th>
                    <th>Tokens</th>
                    <th>Cache</th>
                    <th>Duration</th>
                </tr>
            </thead>
            <tbody>
                {
        "".join(
            f'''<tr>
                    <td>{datetime.fromisoformat(e.get("ts", "").replace("Z", "+00:00")).strftime("%H:%M:%S")}</td>
                    <td>{e.get("workflow", "")}</td>
                    <td>{e.get("stage", "")}</td>
                    <td><span class="tier-badge badge-{e.get("tier", "").lower()}">{e.get("tier", "")}</span></td>
                    <td>${e.get("cost", 0):.4f}</td>
                    <td>{e.get("tokens", {}).get("input", 0)}/{e.get("tokens", {}).get("output", 0)}</td>
                    <td class="cache-{"hit" if e.get("cache", {}).get("hit") else "miss"}">
                        {"HIT" if e.get("cache", {}).get("hit") else "MISS"}
                    </td>
                    <td>{e.get("duration_ms", 0) / 1000:.1f}s</td>
                </tr>'''
            for e in list(reversed(entries))[:20]
        )
    }
            </tbody>
        </table>
    </div>
</body>
</html>"""

    # Write to temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html_content)
        temp_path = f.name

    print(f"📊 Opening dashboard in browser: {temp_path}")
    webbrowser.open(f"file://{temp_path}")

    return 0


def cmd_file_test_dashboard(args: Any) -> int:
    """Open interactive file test status dashboard in browser.

    Args:
        args: Parsed command-line arguments
            - port: Port to serve on (default: 8765)

    Returns:
        Exit code (0 for success)
    """
    from empathy_os.models.telemetry import get_telemetry_store

    port = getattr(args, "port", 8765)

    def generate_dashboard_html() -> str:
        """Generate the dashboard HTML with current data."""
        store = get_telemetry_store()
        all_records = store.get_file_tests(limit=100000)

        if not all_records:
            return _generate_empty_dashboard()

        # Get latest record per file
        latest_by_file: dict[str, Any] = {}
        for record in all_records:
            existing = latest_by_file.get(record.file_path)
            if existing is None or record.timestamp > existing.timestamp:
                latest_by_file[record.file_path] = record

        records = list(latest_by_file.values())

        # Calculate stats
        total = len(records)
        passed = sum(1 for r in records if r.last_test_result == "passed")
        failed = sum(1 for r in records if r.last_test_result in ("failed", "error"))
        no_tests = sum(1 for r in records if r.last_test_result == "no_tests")
        stale = sum(1 for r in records if r.is_stale)

        # Sort by status priority: failed > stale > no_tests > passed
        def sort_key(r):
            if r.last_test_result in ("failed", "error"):
                return (0, r.file_path)
            if r.is_stale:
                return (1, r.file_path)
            if r.last_test_result == "no_tests":
                return (2, r.file_path)
            return (3, r.file_path)

        records.sort(key=sort_key)

        # Generate table rows
        rows_html = ""
        for record in records:
            result = record.last_test_result
            if result == "passed":
                status_class = "passed"
                status_icon = "✅"
            elif result in ("failed", "error"):
                status_class = "failed"
                status_icon = "❌"
            elif result == "no_tests":
                status_class = "no-tests"
                status_icon = "⚠️"
            else:
                status_class = "skipped"
                status_icon = "⏭️"

            stale_badge = '<span class="badge stale">STALE</span>' if record.is_stale else ""

            try:
                dt = datetime.fromisoformat(record.timestamp.rstrip("Z"))
                ts_display = dt.strftime("%Y-%m-%d %H:%M")
            except (ValueError, AttributeError):
                ts_display = record.timestamp[:16] if record.timestamp else "-"

            rows_html += f"""
            <tr class="{status_class}">
                <td class="file-path">{record.file_path}</td>
                <td class="status">{status_icon} {result.upper()} {stale_badge}</td>
                <td class="numeric">{record.test_count}</td>
                <td class="numeric passed-count">{record.passed}</td>
                <td class="numeric failed-count">{record.failed + record.errors}</td>
                <td class="numeric">{record.duration_seconds:.1f}s</td>
                <td class="timestamp">{ts_display}</td>
            </tr>
            """

        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>File Test Status Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #ffffff;
            color: #333;
            padding: 20px;
            min-height: 100vh;
        }
        .container { max-width: 1600px; margin: 0 auto; }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid #e0e0e0;
        }
        .header h1 { font-size: 28px; color: #333; }
        .refresh-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .refresh-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        .refresh-btn:active { transform: translateY(0); }
        .refresh-btn.spinning .icon { animation: spin 1s linear infinite; }
        @keyframes spin { 100% { transform: rotate(360deg); } }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .stat-card.passed { border-left: 4px solid #22c55e; }
        .stat-card.failed { border-left: 4px solid #ef4444; }
        .stat-card.no-tests { border-left: 4px solid #f59e0b; }
        .stat-card.stale { border-left: 4px solid #8b5cf6; }
        .stat-card.total { border-left: 4px solid #3b82f6; }
        .stat-value { font-size: 36px; font-weight: bold; }
        .stat-label { font-size: 14px; color: #666; margin-top: 5px; }
        .stat-card.passed .stat-value { color: #22c55e; }
        .stat-card.failed .stat-value { color: #ef4444; }
        .stat-card.no-tests .stat-value { color: #f59e0b; }
        .stat-card.stale .stat-value { color: #8b5cf6; }
        .stat-card.total .stat-value { color: #3b82f6; }
        .filter-bar {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .filter-btn {
            background: #f8f9fa;
            color: #666;
            border: 1px solid #e0e0e0;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .filter-btn:hover, .filter-btn.active {
            background: #667eea;
            color: #fff;
            border-color: #667eea;
        }
        .search-input {
            flex: 1;
            min-width: 200px;
            background: #fff;
            border: 1px solid #e0e0e0;
            color: #333;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 14px;
        }
        .search-input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: #fff;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        th, td { padding: 12px 16px; text-align: left; }
        th {
            background: #f8f9fa;
            font-weight: 600;
            color: #333;
            position: sticky;
            top: 0;
            border-bottom: 2px solid #e0e0e0;
        }
        tr { border-bottom: 1px solid #f0f0f0; }
        tr:hover { background: #f8f9fa; }
        tr.failed { background: rgba(239, 68, 68, 0.08); }
        tr.no-tests { background: rgba(245, 158, 11, 0.05); }
        .file-path { font-family: 'Monaco', 'Menlo', monospace; font-size: 13px; color: #333; }
        .numeric { text-align: right; font-family: monospace; }
        .passed-count { color: #22c55e; }
        .failed-count { color: #ef4444; }
        .timestamp { color: #888; font-size: 12px; }
        .badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: bold;
            margin-left: 8px;
        }
        .badge.stale { background: #8b5cf6; color: #fff; }
        .hidden { display: none; }
        .last-updated { color: #888; font-size: 12px; margin-top: 20px; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 File Test Status Dashboard</h1>
            <button class="refresh-btn" onclick="refreshData()">
                <span class="icon">🔄</span>
                <span>Refresh</span>
            </button>
        </div>

        <div class="stats">
            <div class="stat-card total">
                <div class="stat-value">""" + str(total) + """</div>
                <div class="stat-label">Total Files</div>
            </div>
            <div class="stat-card passed">
                <div class="stat-value">""" + str(passed) + """</div>
                <div class="stat-label">Passed</div>
            </div>
            <div class="stat-card failed">
                <div class="stat-value">""" + str(failed) + """</div>
                <div class="stat-label">Failed</div>
            </div>
            <div class="stat-card no-tests">
                <div class="stat-value">""" + str(no_tests) + """</div>
                <div class="stat-label">No Tests</div>
            </div>
            <div class="stat-card stale">
                <div class="stat-value">""" + str(stale) + """</div>
                <div class="stat-label">Stale</div>
            </div>
        </div>

        <div class="filter-bar">
            <button class="filter-btn active" data-filter="all">All</button>
            <button class="filter-btn" data-filter="passed">✅ Passed</button>
            <button class="filter-btn" data-filter="failed">❌ Failed</button>
            <button class="filter-btn" data-filter="no-tests">⚠️ No Tests</button>
            <button class="filter-btn" data-filter="stale">🔄 Stale</button>
            <input type="text" class="search-input" placeholder="Search files..." id="searchInput">
        </div>

        <table id="fileTable">
            <thead>
                <tr>
                    <th>File Path</th>
                    <th>Status</th>
                    <th>Tests</th>
                    <th>Passed</th>
                    <th>Failed</th>
                    <th>Duration</th>
                    <th>Last Run</th>
                </tr>
            </thead>
            <tbody>
                """ + rows_html + """
            </tbody>
        </table>

        <div class="last-updated">
            Last updated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """
        </div>
    </div>

    <script>
        // Filter functionality
        const filterBtns = document.querySelectorAll('.filter-btn');
        const rows = document.querySelectorAll('#fileTable tbody tr');
        const searchInput = document.getElementById('searchInput');

        let currentFilter = 'all';

        filterBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                filterBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentFilter = btn.dataset.filter;
                applyFilters();
            });
        });

        searchInput.addEventListener('input', applyFilters);

        function applyFilters() {
            const searchTerm = searchInput.value.toLowerCase();
            rows.forEach(row => {
                const filePath = row.querySelector('.file-path').textContent.toLowerCase();
                const matchesSearch = filePath.includes(searchTerm);
                const matchesFilter = currentFilter === 'all' ||
                    (currentFilter === 'passed' && row.classList.contains('passed')) ||
                    (currentFilter === 'failed' && row.classList.contains('failed')) ||
                    (currentFilter === 'no-tests' && row.classList.contains('no-tests')) ||
                    (currentFilter === 'stale' && row.innerHTML.includes('STALE'));

                row.classList.toggle('hidden', !(matchesSearch && matchesFilter));
            });
        }

        // Refresh functionality
        function refreshData() {
            const btn = document.querySelector('.refresh-btn');
            btn.classList.add('spinning');
            btn.disabled = true;

            // Reload the page to get fresh data
            setTimeout(() => {
                window.location.reload();
            }, 500);
        }

        // Auto-refresh every 60 seconds (optional)
        // setInterval(refreshData, 60000);
    </script>
</body>
</html>"""

    def _generate_empty_dashboard() -> str:
        """Generate dashboard HTML when no data available."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>File Test Status Dashboard</title>
    <style>
        body {
            font-family: -apple-system, sans-serif;
            background: #ffffff;
            color: #333;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            text-align: center;
        }
        .message { max-width: 500px; }
        h1 { margin-bottom: 20px; color: #333; }
        code {
            background: #f8f9fa;
            color: #333;
            padding: 10px 20px;
            border-radius: 6px;
            display: block;
            margin-top: 20px;
            border: 1px solid #e0e0e0;
        }
    </style>
</head>
<body>
    <div class="message">
        <h1>📊 No Test Data Available</h1>
        <p>Run the file test tracker to populate data:</p>
        <code>empathy file-tests --scan</code>
        <p style="margin-top: 20px; color: #888;">Or track individual files:</p>
        <code>python -c "from empathy_os.workflows.test_runner import track_file_tests; track_file_tests('src/your_file.py')"</code>
    </div>
</body>
</html>"""

    class DashboardHandler(http.server.SimpleHTTPRequestHandler):
        """Custom handler for the dashboard."""

        def do_GET(self):
            """Handle GET requests."""
            if self.path == "/" or self.path == "/index.html":
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                html = generate_dashboard_html()
                self.wfile.write(html.encode())
            else:
                self.send_error(404)

        def log_message(self, format, *args):
            """Suppress logging."""
            pass

    print(f"Starting File Test Dashboard on http://localhost:{port}")
    print("Press Ctrl+C to stop the server")

    # Open browser
    webbrowser.open(f"http://localhost:{port}")

    # Start server
    with socketserver.TCPServer(("", port), DashboardHandler) as httpd:
        httpd.allow_reuse_address = True
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nDashboard server stopped.")

    return 0
