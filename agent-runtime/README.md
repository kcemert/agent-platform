# Agent Runtime Framework — Epic 11

Productionised runtime for Business Agents Platform pilot agents.
Provides scheduling, observability, notifications, retry logic, and a health-check HTTP server.
Python stdlib only. No Docker required.

---

## Directory layout

```
agent-runtime/
  __init__.py             Package init
  agent_registry.json     Agent config (slug, script, schedule, authority)
  notification_config.json  Notification channel config (Slack / email)
  scheduler.py            Cron-style agent scheduler
  notification.py         Notification module (Slack + email + stdout fallback)
  retry.py                Retry decorator + circuit breaker
  health_check.py         HTTP health-check server (port 8080)
  scheduler.log           Written by scheduler at runtime
  last_run.json           Per-agent last-run timestamps (written at runtime)
  escalations.log         ESCALATE-level notifications (written at runtime)
  retry.log               Retry / circuit-breaker log (written at runtime)
  circuit_state.json      Circuit-breaker state (written at runtime)
agent_runtime -> agent-runtime   Symlink for Python imports
```

---

## 1. Starting the scheduler

Run continuously (checks every 60 s, fires agents whose cron matches):

```bash
python3 agent-runtime/scheduler.py
```

Run all enabled agents once immediately then exit (useful for CI / manual tests):

```bash
python3 agent-runtime/scheduler.py --once
```

Run a single agent by slug:

```bash
python3 agent-runtime/scheduler.py --once --agent replenishment
```

Preview what would run without executing anything:

```bash
python3 agent-runtime/scheduler.py --dry-run
```

Logs are written to `agent-runtime/scheduler.log` and also streamed to stdout.
Last-run metadata (timestamp + exit code) is persisted in `agent-runtime/last_run.json`.

---

## 2. Configuring Slack notifications

Edit `agent-runtime/notification_config.json`:

```json
{
  "slack_webhook_url": "https://hooks.slack.com/services/T.../B.../...",
  "email_config": {
    "smtp_host": "",
    "smtp_port": 587,
    "from_address": "",
    "to_addresses": []
  },
  "escalation_recipients": []
}
```

- Set `slack_webhook_url` to your Incoming Webhook URL.
- If the field is empty, notifications fall back to stdout logging.
- ESCALATE-level messages are always written to `agent-runtime/escalations.log`
  regardless of channel configuration.

Use the notify function inside an agent:

```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent_runtime.notification import notify

notify(
    agent_slug="replenishment",
    level="INFO",       # INFO | WARNING | ESCALATE
    message="Created 4 purchase requisitions totaling $34,200",
    details={"skus": ["CG-SKU-001", "CG-SKU-003"]}
)
```

---

## 3. Running a health check

Start the HTTP server (keep running in background or a dedicated terminal):

```bash
python3 agent-runtime/health_check.py
```

The server listens on port 8080.

JSON endpoint (for monitoring / uptime tools):

```bash
curl http://localhost:8080/health
```

Returns HTTP 200 with `"status": "ok"` when all enabled agents last exited with code 0.
Returns HTTP 503 with `"status": "degraded"` if any agent failed or has never run.

HTML dashboard (browser):

```
http://localhost:8080/
```

Dark-themed table showing each agent's name, status, last run time, exit code, and
next scheduled run time.

---

## 4. Adding a new agent to the registry

1. Place your agent script anywhere accessible from the workspace root
   (convention: `pilot-agents/my_new_agent.py`).

2. Add an entry to `agent-runtime/agent_registry.json`:

```json
{
  "slug": "my-agent",
  "name": "My New Agent",
  "script": "pilot-agents/my_new_agent.py",
  "schedule": "0 8 * * 1-5",
  "authority_level": "LOW",
  "enabled": true,
  "description": "Short description of what this agent does"
}
```

Cron field order: `minute hour day-of-month month day-of-week`
Supported syntax: `*`, `*/n` (step), `n-m` (range), comma-separated values.

3. Restart the scheduler for the new agent to be picked up:

```bash
python3 agent-runtime/scheduler.py
```

4. Verify with a dry run:

```bash
python3 agent-runtime/scheduler.py --dry-run
```

The new agent will appear in the list.

---

## 5. Using retry and circuit breaker in agents

```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent_runtime.retry import with_retry, CircuitBreaker, CircuitOpenError

# Retry decorator: 3 attempts, exponential backoff starting at 2 s
@with_retry(max_attempts=3, backoff_seconds=2)
def call_sap_api(endpoint, payload):
    ...

# Circuit breaker: opens after 3 consecutive failures, resets after 5 min
cb = CircuitBreaker(name="sap-api", failure_threshold=3, reset_timeout=300)

try:
    result = cb.call(call_sap_api, "/api/inventory", {})
except CircuitOpenError as e:
    print(f"Circuit open: {e}")
```

State is persisted in `agent-runtime/circuit_state.json` across restarts.
Behaviour is logged to `agent-runtime/retry.log`.

---

## Authority levels

| Level  | Meaning                                                  |
|--------|----------------------------------------------------------|
| LOW    | Read-only / reporting. No system writes.                 |
| MEDIUM | Can create records (e.g. purchase requisitions) within budget thresholds. |
| HIGH   | Can draft CAPA recommendations; human approval required before execution. |

---

## Runtime files generated automatically

| File                        | Written by       | Contents                                   |
|-----------------------------|------------------|--------------------------------------------|
| `scheduler.log`             | scheduler.py     | Start/end timestamps and exit codes        |
| `last_run.json`             | scheduler.py     | Per-agent last run time and exit code      |
| `escalations.log`           | notification.py  | All ESCALATE-level notification payloads   |
| `retry.log`                 | retry.py         | Retry attempts and circuit-breaker events  |
| `circuit_state.json`        | retry.py         | Circuit-breaker state (open/closed/count)  |
