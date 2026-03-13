#!/usr/bin/env python3
"""
health_check.py — Lightweight HTTP health-check server for Business Agents Platform.

Usage:
    python3 agent-runtime/health_check.py

Endpoints:
    GET /health  — JSON health report (200 ok / 503 degraded)
    GET /        — HTML status page (dark theme)

The server reads agent_registry.json and last_run.json to construct its response.
It runs on port 8080 by default.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

RUNTIME_DIR   = os.path.dirname(os.path.abspath(__file__))
REGISTRY_PATH = os.path.join(RUNTIME_DIR, "agent_registry.json")
LAST_RUN_PATH = os.path.join(RUNTIME_DIR, "last_run.json")

PORT = 8080


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def _load_registry() -> List[Dict[str, Any]]:
    try:
        with open(REGISTRY_PATH) as fh:
            return json.load(fh).get("agents", [])
    except Exception:
        return []


def _load_last_run() -> Dict[str, Any]:
    if os.path.exists(LAST_RUN_PATH):
        try:
            with open(LAST_RUN_PATH) as fh:
                return json.load(fh)
        except Exception:
            pass
    return {}


# ---------------------------------------------------------------------------
# Cron-based "next run" calculator (mirrors scheduler.py's parser)
# ---------------------------------------------------------------------------

def _parse_cron_field(field: str, lo: int, hi: int):
    result = set()
    for part in field.split(","):
        part = part.strip()
        step = 1
        if "/" in part:
            part, step_str = part.split("/", 1)
            step = int(step_str)
        if part == "*":
            values = range(lo, hi + 1)
        elif "-" in part:
            a, b = part.split("-", 1)
            values = range(int(a), int(b) + 1)
        else:
            values = range(int(part), int(part) + 1)
        result.update(v for v in values if lo <= v <= hi and (v - lo) % step == 0)
    return result


def _next_scheduled(expression: str) -> Optional[str]:
    """Return the next UTC ISO-8601 time the cron expression will fire."""
    try:
        fields = expression.strip().split()
        if len(fields) != 5:
            return None
        minutes_f, hours_f, dom_f, month_f, dow_f = fields
        minutes = sorted(_parse_cron_field(minutes_f, 0, 59))
        hours   = sorted(_parse_cron_field(hours_f,   0, 23))
        doms    = sorted(_parse_cron_field(dom_f,      1, 31))
        months  = sorted(_parse_cron_field(month_f,    1, 12))
        dows    = sorted(_parse_cron_field(dow_f,      0,  6))  # 0=Sunday

        now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        candidate = now + timedelta(minutes=1)

        # Search up to 8 days ahead (handles weekly schedules)
        for _ in range(8 * 24 * 60):
            py_dow    = candidate.weekday()        # 0=Mon
            cron_dow  = (py_dow + 1) % 7           # 0=Sun

            if (
                candidate.month  in months
                and candidate.day    in doms
                and cron_dow         in dows
                and candidate.hour   in hours
                and candidate.minute in minutes
            ):
                return candidate.isoformat()
            candidate += timedelta(minutes=1)
        return None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Health data builder
# ---------------------------------------------------------------------------

def _build_health() -> Dict[str, Any]:
    agents    = _load_registry()
    last_run  = _load_last_run()
    now_iso   = datetime.now(timezone.utc).isoformat()

    agent_statuses: List[Dict[str, Any]] = []
    all_healthy = True

    for agent in agents:
        if not agent.get("enabled", False):
            continue

        slug      = agent["slug"]
        run_info  = last_run.get(slug, {})
        last_run_ts    = run_info.get("last_run")
        last_exit_code = run_info.get("last_exit_code")

        if last_exit_code is None:
            status = "never_run"
            all_healthy = False
        elif last_exit_code == 0:
            status = "healthy"
        else:
            status = "failed"
            all_healthy = False

        agent_statuses.append({
            "slug":             slug,
            "name":             agent.get("name", slug),
            "enabled":          agent.get("enabled", False),
            "last_run":         last_run_ts,
            "last_exit_code":   last_exit_code,
            "next_scheduled":   _next_scheduled(agent.get("schedule", "")),
            "status":           status,
        })

    return {
        "status":    "ok" if all_healthy else "degraded",
        "timestamp": now_iso,
        "agents":    agent_statuses,
    }


# ---------------------------------------------------------------------------
# HTML status page
# ---------------------------------------------------------------------------

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Business Agents — Runtime Health</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: #0d1117;
      color: #c9d1d9;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      padding: 2rem;
    }}
    h1 {{ font-size: 1.5rem; margin-bottom: 0.25rem; color: #e6edf3; }}
    .subtitle {{ color: #8b949e; font-size: 0.875rem; margin-bottom: 2rem; }}
    .badge {{
      display: inline-block; padding: 0.25rem 0.75rem; border-radius: 999px;
      font-size: 0.75rem; font-weight: 700; letter-spacing: 0.05em;
      text-transform: uppercase;
    }}
    .badge-ok      {{ background: #1a4731; color: #3fb950; border: 1px solid #2ea043; }}
    .badge-degraded{{ background: #4b1c1c; color: #f85149; border: 1px solid #da3633; }}
    .badge-never   {{ background: #2d2208; color: #e3b341; border: 1px solid #9e6a03; }}
    table {{
      width: 100%; border-collapse: collapse; margin-top: 1.5rem;
      background: #161b22; border-radius: 8px; overflow: hidden;
    }}
    th {{
      background: #21262d; color: #8b949e; font-size: 0.75rem; font-weight: 600;
      text-transform: uppercase; letter-spacing: 0.06em;
      padding: 0.75rem 1rem; text-align: left;
    }}
    td {{ padding: 0.75rem 1rem; border-top: 1px solid #21262d; font-size: 0.875rem; }}
    tr:hover td {{ background: #1c2128; }}
    .dot {{
      display: inline-block; width: 8px; height: 8px; border-radius: 50%;
      margin-right: 0.5rem; vertical-align: middle;
    }}
    .dot-ok       {{ background: #3fb950; box-shadow: 0 0 6px #3fb950; }}
    .dot-failed   {{ background: #f85149; box-shadow: 0 0 6px #f85149; }}
    .dot-never    {{ background: #e3b341; box-shadow: 0 0 6px #e3b341; }}
    .mono {{ font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace; font-size: 0.8rem; }}
    footer {{ margin-top: 2rem; color: #484f58; font-size: 0.75rem; }}
  </style>
</head>
<body>
  <h1>Business Agents Platform — Runtime Health</h1>
  <p class="subtitle">Generated: {timestamp}</p>
  <span class="badge badge-{badge_class}">{overall_status}</span>
  <table>
    <thead>
      <tr>
        <th>Agent</th>
        <th>Status</th>
        <th>Last Run</th>
        <th>Exit Code</th>
        <th>Next Scheduled</th>
        <th>Schedule</th>
      </tr>
    </thead>
    <tbody>
{rows}
    </tbody>
  </table>
  <footer>Business Agents Platform &mdash; Epic 11 Agent Runtime &mdash; Port {port}</footer>
</body>
</html>
"""

_ROW_TEMPLATE = """\
      <tr>
        <td><strong>{name}</strong><br><span class="mono" style="color:#8b949e">{slug}</span></td>
        <td><span class="dot dot-{dot_class}"></span>{status_label}</td>
        <td class="mono">{last_run}</td>
        <td class="mono">{exit_code}</td>
        <td class="mono">{next_scheduled}</td>
        <td class="mono">{schedule}</td>
      </tr>"""


def _build_html(health: Dict[str, Any], registry: List[Dict[str, Any]]) -> str:
    schedule_map = {a["slug"]: a.get("schedule", "—") for a in registry}

    rows = []
    for ag in health["agents"]:
        status = ag["status"]
        if status == "healthy":
            dot_class    = "ok"
            status_label = "Healthy"
        elif status == "failed":
            dot_class    = "failed"
            status_label = "Failed"
        else:
            dot_class    = "never"
            status_label = "Never Run"

        rows.append(_ROW_TEMPLATE.format(
            name           = ag["name"],
            slug           = ag["slug"],
            dot_class      = dot_class,
            status_label   = status_label,
            last_run       = ag["last_run"]       or "—",
            exit_code      = str(ag["last_exit_code"]) if ag["last_exit_code"] is not None else "—",
            next_scheduled = ag["next_scheduled"] or "—",
            schedule       = schedule_map.get(ag["slug"], "—"),
        ))

    overall = health["status"]
    badge_class = "ok" if overall == "ok" else "degraded"
    return _HTML_TEMPLATE.format(
        timestamp      = health["timestamp"],
        badge_class    = badge_class,
        overall_status = overall.upper(),
        rows           = "\n".join(rows),
        port           = PORT,
    )


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------

class HealthHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        # Suppress default access log to reduce noise; replace with cleaner output
        print(f"[health_check] {self.address_string()} {format % args}")

    def do_GET(self) -> None:
        path = self.path.split("?")[0]

        if path == "/health":
            self._serve_json()
        elif path == "/":
            self._serve_html()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

    def _serve_json(self) -> None:
        health  = _build_health()
        body    = json.dumps(health, indent=2).encode("utf-8")
        status  = 200 if health["status"] == "ok" else 503

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_html(self) -> None:
        health   = _build_health()
        registry = _load_registry()
        html     = _build_html(health, registry)
        body     = html.encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    server = HTTPServer(("", PORT), HealthHandler)
    print(f"[health_check] Listening on http://0.0.0.0:{PORT}")
    print(f"[health_check]   GET /health  — JSON")
    print(f"[health_check]   GET /        — HTML dashboard")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[health_check] Shutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
