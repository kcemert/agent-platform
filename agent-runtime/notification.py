#!/usr/bin/env python3
"""
notification.py — Notification module for Business Agents Platform.

Import and use:

    from agent_runtime.notification import notify

    notify(
        agent_slug="replenishment",
        level="INFO",        # INFO | WARNING | ESCALATE
        message="Created 4 purchase requisitions totaling $34,200",
        details={}           # optional dict
    )

Configuration is read from agent-runtime/notification_config.json.

Behaviour:
  - Slack: if slack_webhook_url is non-empty, POST to the webhook.
           Otherwise log to stdout.
  - Email: if email_config.smtp_host is non-empty, send via smtplib.
           Otherwise log to stdout.
  - ESCALATE level always writes to agent-runtime/escalations.log in
    addition to normal channels.
"""

from __future__ import annotations

import json
import logging
import os
import smtplib
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

RUNTIME_DIR   = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH   = os.path.join(RUNTIME_DIR, "notification_config.json")
ESCALATION_LOG = os.path.join(RUNTIME_DIR, "escalations.log")

# ---------------------------------------------------------------------------
# Module logger (stdout only — channels handle their own output)
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [NOTIFICATION] %(levelname)s %(message)s",
    stream=sys.stdout,
)
_log = logging.getLogger("notification")

# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

_DEFAULT_CONFIG: Dict[str, Any] = {
    "slack_webhook_url": "",
    "email_config": {
        "smtp_host": "",
        "smtp_port": 587,
        "from_address": "",
        "to_addresses": [],
    },
    "escalation_recipients": [],
}


def _load_config() -> Dict[str, Any]:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH) as fh:
                return json.load(fh)
        except Exception as exc:
            _log.warning("Could not read notification_config.json: %s — using defaults", exc)
    return _DEFAULT_CONFIG.copy()


# ---------------------------------------------------------------------------
# Escalation log writer
# ---------------------------------------------------------------------------

def _write_escalation_log(agent_slug: str, message: str, details: Dict[str, Any]) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": ts,
        "agent_slug": agent_slug,
        "level": "ESCALATE",
        "message": message,
        "details": details,
    }
    try:
        with open(ESCALATION_LOG, "a") as fh:
            fh.write(json.dumps(entry) + "\n")
    except Exception as exc:
        _log.error("Could not write to escalations.log: %s", exc)


# ---------------------------------------------------------------------------
# Slack channel
# ---------------------------------------------------------------------------

def _notify_slack(webhook_url: str, agent_slug: str, level: str, message: str, details: Dict[str, Any]) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    level_emoji = {"INFO": "ℹ️", "WARNING": "⚠️", "ESCALATE": "🚨"}.get(level, "")
    text = (
        f"{level_emoji} *[{level}]* Agent `{agent_slug}` @ {ts}\n"
        f"{message}"
    )
    if details:
        text += f"\n```{json.dumps(details, indent=2)}```"

    payload = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            _log.info("Slack notification sent (status %d)", resp.status)
    except urllib.error.URLError as exc:
        _log.error("Slack webhook failed: %s", exc)


# ---------------------------------------------------------------------------
# Email channel
# ---------------------------------------------------------------------------

def _notify_email(
    smtp_host: str,
    smtp_port: int,
    from_address: str,
    to_addresses: List[str],
    agent_slug: str,
    level: str,
    message: str,
    details: Dict[str, Any],
) -> None:
    if not to_addresses:
        _log.warning("Email notification skipped: no to_addresses configured.")
        return

    ts = datetime.now(timezone.utc).isoformat()
    subject = f"[{level}] Agent {agent_slug} notification — {ts}"
    body_parts = [f"Agent: {agent_slug}", f"Level: {level}", f"Time: {ts}", "", message]
    if details:
        body_parts.append("")
        body_parts.append("Details:")
        body_parts.append(json.dumps(details, indent=2))

    msg = MIMEText("\n".join(body_parts))
    msg["Subject"] = subject
    msg["From"]    = from_address
    msg["To"]      = ", ".join(to_addresses)

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.sendmail(from_address, to_addresses, msg.as_string())
        _log.info("Email notification sent to %s", to_addresses)
    except Exception as exc:
        _log.error("Email notification failed: %s", exc)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def notify(
    agent_slug: str,
    level: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """Send a notification through configured channels.

    Parameters
    ----------
    agent_slug:
        The slug of the calling agent (e.g. "replenishment").
    level:
        One of "INFO", "WARNING", or "ESCALATE".
    message:
        Human-readable notification message.
    details:
        Optional dictionary with additional structured data.
    """
    if details is None:
        details = {}

    level = level.upper()
    if level not in ("INFO", "WARNING", "ESCALATE"):
        _log.warning("Unknown notification level '%s'; defaulting to INFO.", level)
        level = "INFO"

    config = _load_config()
    slack_url  = config.get("slack_webhook_url", "")
    email_cfg  = config.get("email_config", {})
    smtp_host  = email_cfg.get("smtp_host", "")

    # Always write ESCALATE entries to the escalation log
    if level == "ESCALATE":
        _write_escalation_log(agent_slug, message, details)

    sent_via_channel = False

    # --- Slack ---
    if slack_url:
        _notify_slack(slack_url, agent_slug, level, message, details)
        sent_via_channel = True

    # --- Email ---
    if smtp_host:
        _notify_email(
            smtp_host=smtp_host,
            smtp_port=email_cfg.get("smtp_port", 587),
            from_address=email_cfg.get("from_address", ""),
            to_addresses=email_cfg.get("to_addresses", []),
            agent_slug=agent_slug,
            level=level,
            message=message,
            details=details,
        )
        sent_via_channel = True

    # --- Fallback: stdout log ---
    if not sent_via_channel:
        ts = datetime.now(timezone.utc).isoformat()
        _log.info(
            "[%s] agent=%s ts=%s message=%r details=%s",
            level, agent_slug, ts, message, json.dumps(details),
        )
