#!/usr/bin/env python3
"""
scheduler.py — Cron-style agent scheduler for the Business Agents Platform.

Usage:
    python3 agent-runtime/scheduler.py [--once] [--agent <slug>] [--dry-run]

Options:
    --once          Run all enabled agents once immediately, then exit.
    --agent <slug>  Run only the specified agent (by slug).
    --dry-run       Print what would run without actually executing agents.

The scheduler reads agent_registry.json to determine which agents to run and
on what schedule. Each enabled agent is evaluated every 60 seconds. When the
current time matches an agent's cron expression, the agent's script is spawned
as a subprocess.

Cron field order: minute hour dom month dow
Supported specials: * (any), */n (step), n-m (range), comma-separated values.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

RUNTIME_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(RUNTIME_DIR)
REGISTRY_PATH = os.path.join(RUNTIME_DIR, "agent_registry.json")
LAST_RUN_PATH = os.path.join(RUNTIME_DIR, "last_run.json")
SCHEDULER_LOG = os.path.join(RUNTIME_DIR, "scheduler.log")

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SCHEDULER] %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(SCHEDULER_LOG),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("scheduler")


# ---------------------------------------------------------------------------
# Cron parser (stdlib only)
# ---------------------------------------------------------------------------

def _parse_field(field: str, lo: int, hi: int) -> Set[int]:
    """Parse a single cron field into a set of matching integers.

    Supported syntax:
        *       — all values in [lo, hi]
        */n     — every n-th value starting from lo
        a-b     — inclusive range
        a-b/n   — range with step
        n       — single value
        a,b,c   — comma-separated list of any of the above
    """
    result: Set[int] = set()
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


def cron_matches(expression: str, dt: datetime) -> bool:
    """Return True if *dt* matches the 5-field cron *expression*."""
    fields = expression.strip().split()
    if len(fields) != 5:
        raise ValueError(f"Invalid cron expression (need 5 fields): {expression!r}")
    minutes_f, hours_f, dom_f, month_f, dow_f = fields

    minutes = _parse_field(minutes_f, 0, 59)
    hours   = _parse_field(hours_f,   0, 23)
    doms    = _parse_field(dom_f,      1, 31)
    months  = _parse_field(month_f,    1, 12)
    dows    = _parse_field(dow_f,      0,  6)  # 0=Sunday

    # Python: weekday() → 0=Monday; cron: 0=Sunday
    py_dow = dt.weekday()          # 0=Mon … 6=Sun
    cron_dow = (py_dow + 1) % 7   # 0=Sun … 6=Sat

    return (
        dt.minute in minutes
        and dt.hour in hours
        and dt.day in doms
        and dt.month in months
        and cron_dow in dows
    )


# ---------------------------------------------------------------------------
# Registry helpers
# ---------------------------------------------------------------------------

def load_registry() -> List[Dict[str, Any]]:
    with open(REGISTRY_PATH) as fh:
        data = json.load(fh)
    return data.get("agents", [])


def load_last_run() -> Dict[str, Any]:
    if os.path.exists(LAST_RUN_PATH):
        with open(LAST_RUN_PATH) as fh:
            return json.load(fh)
    return {}


def save_last_run(last_run: Dict[str, Any]) -> None:
    with open(LAST_RUN_PATH, "w") as fh:
        json.dump(last_run, fh, indent=2)


# ---------------------------------------------------------------------------
# Agent execution
# ---------------------------------------------------------------------------

def run_agent(agent: Dict[str, Any], dry_run: bool = False) -> int:
    """Spawn the agent script as a subprocess and return its exit code."""
    slug   = agent["slug"]
    script = os.path.join(WORKSPACE_ROOT, agent["script"])

    if dry_run:
        log.info("[DRY-RUN] Would execute: python3 %s", script)
        return 0

    log.info("Starting agent '%s' → %s", slug, script)
    start_ts = datetime.now(timezone.utc).isoformat()

    try:
        result = subprocess.run(
            [sys.executable, script],
            cwd=WORKSPACE_ROOT,
            capture_output=False,
        )
        exit_code = result.returncode
    except Exception as exc:
        log.error("Agent '%s' failed to launch: %s", slug, exc)
        exit_code = 1

    end_ts = datetime.now(timezone.utc).isoformat()
    log.info(
        "Finished agent '%s' | exit_code=%d | started=%s ended=%s",
        slug, exit_code, start_ts, end_ts,
    )
    return exit_code


def record_run(slug: str, exit_code: int) -> None:
    """Persist last-run info to last_run.json."""
    last_run = load_last_run()
    last_run[slug] = {
        "last_run": datetime.now(timezone.utc).isoformat(),
        "last_exit_code": exit_code,
    }
    save_last_run(last_run)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Business Agents Platform Scheduler")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run all enabled agents once immediately, then exit.",
    )
    parser.add_argument(
        "--agent",
        metavar="SLUG",
        help="Run only the agent with this slug.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would run without executing agents.",
    )
    args = parser.parse_args()

    agents = load_registry()

    # Filter by slug if requested
    if args.agent:
        agents = [a for a in agents if a["slug"] == args.agent]
        if not agents:
            log.error("No agent found with slug '%s'", args.agent)
            sys.exit(1)

    # Filter to enabled agents
    enabled = [a for a in agents if a.get("enabled", False)]
    if not enabled:
        log.warning("No enabled agents found.")
        sys.exit(0)

    if args.dry_run:
        log.info("[DRY-RUN] Scheduler started. Enabled agents:")
        for a in enabled:
            log.info("  slug=%-20s  schedule='%s'  script=%s", a["slug"], a["schedule"], a["script"])
        if not args.once:
            log.info("[DRY-RUN] (Would run main loop checking schedules every 60 s)")
        return

    if args.once:
        log.info("--once mode: running all enabled agents immediately.")
        for agent in enabled:
            exit_code = run_agent(agent, dry_run=args.dry_run)
            record_run(agent["slug"], exit_code)
        log.info("--once mode complete. Exiting.")
        return

    # ---------------------------------------------------------------------------
    # Main scheduler loop
    # ---------------------------------------------------------------------------
    log.info("Scheduler started. Monitoring %d agent(s). Press Ctrl-C to stop.", len(enabled))
    fired_this_minute: Set[str] = set()
    last_minute = -1

    while True:
        now = datetime.now(timezone.utc)

        # Reset per-minute deduplication set when the minute rolls over
        if now.minute != last_minute:
            fired_this_minute = set()
            last_minute = now.minute

        for agent in enabled:
            slug = agent["slug"]
            if slug in fired_this_minute:
                continue
            try:
                if cron_matches(agent["schedule"], now):
                    fired_this_minute.add(slug)
                    exit_code = run_agent(agent)
                    record_run(slug, exit_code)
            except ValueError as exc:
                log.error("Bad cron expression for '%s': %s", slug, exc)

        time.sleep(60)


if __name__ == "__main__":
    main()
