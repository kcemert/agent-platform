# CG Quality CAPA Agent
**Slug**: `cg-quality-capa-agent`
**File**: `pilot-agents/quality_capa_agent.py`
**Lifecycle**: sandbox
**Last generated**: 2026-03-14 | **Last verified**: 2026-03-14

## Purpose

The CG Quality CAPA Agent automates Corrective and Preventive Action (CAPA) initiation in response to open quality events and OEE performance alerts from the manufacturing execution system (MES). Without this agent, a quality engineer must manually review the MES event queue, decide on the appropriate CAPA action (PM work order, quality hold, or line shutdown), create a maintenance request in the MES, and send Slack notifications to the relevant teams — a process that is both time-sensitive and error-prone when multiple events arrive simultaneously.

The primary users are the quality engineer and operations manager personas. The agent is designed to run on an event-triggered or scheduled basis. It pulls open quality events, classifies each one against a rule table (6 issue types mapped to specific CAPA responses), creates maintenance requests in the MES, and sends mock Slack notifications. It also performs a parallel OEE sweep, creating maintenance requests for any production line below 65% OEE that does not already have an open MR. Authority level is MEDIUM — all actions are auto-executed with notifications sent, with no HITL approval gate before execution.

## Inputs

- **MES Quality Events API** (`GET http://localhost:3002/api/quality-events`): Returns open quality events with `event_id`, `line_id`, `severity`, `issue_type` (or `event_type` for live MES), `description`, and `status` fields.
- **MES OEE API** (`GET http://localhost:3002/api/oee`): Returns per-line OEE data with `line_id`, `oee_pct` (or `oee`), and `alert` fields.
- **MES Maintenance Requests API** (`GET http://localhost:3002/api/maintenance-requests`): Fetches existing open MRs to prevent duplicate OEE-triggered MRs for lines already being serviced.
- **MES Maintenance Requests POST** (`POST http://localhost:3002/api/maintenance-requests`): Creates new maintenance requests. Body includes `line_id`, `priority`, `issue_type`, `description`, `issue_description`, and `requested_by`.
- **`--dry-run` flag**: Bypasses all API calls. Uses `DRY_RUN_QUALITY_EVENTS` (3 events: sensor_failure/high, defect_rate/medium, contamination/high) and `DRY_RUN_OEE` (5 lines: 2 alerting at 62.4% and 49.1%).
- **Hardcoded configuration**: `MES_BASE = "http://localhost:3002"`, `OEE_ALERT_THRESHOLD = 65.0`, `REQUESTER = "quality-capa-agent-v1"`.

## Outputs

The agent writes `pilot-agents/outputs/quality_capa_run_{YYYYMMDD_HHMMSS}.json` and logs a run record plus two `value_tracking` rows (metric types: `exceptions_caught` and `hours_saved` at 1.0 hr per CAPA action).

```json
{
  "run_at": "2026-03-14T09:30:00.000000",
  "authority": "MEDIUM",
  "dry_run": true,
  "quality_events": 3,
  "capa_actions": [
    {
      "event_id": "QE-001",
      "line_id": "LINE-04",
      "severity": "high",
      "issue_type": "sensor_failure",
      "capa_action": "PM work order",
      "authority": "MEDIUM",
      "execution": "AUTO_EXECUTED + notification sent",
      "mr_created": {
        "mr_id": "MR-DRY-LINE-04-091500",
        "status": "simulated",
        "line_id": "LINE-04",
        "priority": "medium",
        "issue_type": "preventive_maintenance"
      }
    },
    {
      "event_id": "QE-003",
      "line_id": "LINE-01",
      "severity": "high",
      "issue_type": "contamination",
      "capa_action": "Line shutdown + notification",
      "authority": "MEDIUM",
      "execution": "AUTO_EXECUTED + notification sent",
      "mr_created": {
        "mr_id": "MR-DRY-LINE-01-091500",
        "status": "simulated",
        "line_id": "LINE-01",
        "priority": "critical",
        "issue_type": "line_shutdown"
      }
    }
  ],
  "oee_lines_checked": 5,
  "oee_mr_actions": [
    {
      "line_id": "LINE-02",
      "oee_pct": 62.4,
      "priority": "medium",
      "authority": "MEDIUM",
      "execution": "AUTO_EXECUTED + notification sent",
      "mr_created": { "mr_id": "MR-DRY-LINE-02-091500", "status": "simulated" }
    },
    {
      "line_id": "LINE-04",
      "oee_pct": 49.1,
      "priority": "high",
      "authority": "MEDIUM",
      "execution": "AUTO_EXECUTED + notification sent",
      "mr_created": { "mr_id": "MR-DRY-LINE-04-091501", "status": "simulated" }
    }
  ],
  "slack_messages": [
    {
      "channel": "#quality-alerts",
      "timestamp": "2026-03-14T09:30:00",
      "text": ":rotating_light: *CAPA AUTO-EXECUTED* | LINE-04 | Event: QE-001 | Action: PM work order | MR: MR-DRY-LINE-04-091500 | Severity: HIGH | Agent: quality-capa-agent-v1",
      "sent": true
    }
  ],
  "summary": {
    "total_mrs_created": 4,
    "high_severity_events": 2,
    "oee_alerts": 2
  }
}
```

## Behavior

1. **Fetch quality events**: Calls `GET /api/quality-events`. Falls back to dry-run data if MES is unavailable.
2. **Fetch existing maintenance requests**: Calls `GET /api/maintenance-requests` to build a set of `line_id` values that already have open MRs. Used in step 8 to avoid duplicate OEE-triggered MRs.
3. **Filter events**: Only processes events where `severity` is `"high"` or `"critical"`, OR `status` is `"open"`. Events that meet neither condition are skipped.
4. **Classify CAPA**: Looks up the event's `issue_type` (also accepts `event_type` for live MES compatibility) in `CAPA_RULES`. Six rules are defined:
   - `sensor_failure` → priority `medium`, issue_type `preventive_maintenance`, action `PM work order`
   - `equipment_fault` → priority `medium`, issue_type `preventive_maintenance`, action `PM work order`
   - `defect_rate` → priority `high`, issue_type `quality_hold`, action `Quality hold`
   - `out_of_spec` → priority `high`, issue_type `quality_hold`, action `Quality hold`
   - `contamination` → priority `critical`, issue_type `line_shutdown`, action `Line shutdown + notification`
   - `foreign_material` → priority `critical`, issue_type `line_shutdown`, action `Line shutdown + notification`
   - Unrecognised types fall back to `DEFAULT_CAPA` (priority `medium`, general_maintenance).
5. **Create maintenance request**: POSTs to `POST /api/maintenance-requests` with the classified body. Simulates an `mr_id` in dry-run.
6. **Send mock Slack notification**: Builds a Slack message for `#quality-alerts` (high/critical severity) or `#ops-notifications` (others) and appends it to `slack_messages`. Not a real Slack call — `sent: true` is always mocked.
7. **OEE sweep**: Fetches all lines from `GET /api/oee`. For each line where `oee_pct < 65.0` (or `alert: true`), checks whether the line already has an open MR (from step 2).
8. **Create OEE maintenance request**: For alerting lines without existing MRs, creates an MR with `issue_type: low_oee`. Priority is `high` if `oee_pct < 55`, otherwise `medium`. Sends a Slack mock to `#oee-alerts`.
9. **Build and write output**: Assembles the full output dict, writes JSON to `outputs/`, logs run to DB, records value metrics.

## HITL Decision Points

- **Authority level is MEDIUM**: All actions (PM work orders, quality holds, line shutdowns, OEE MRs) are auto-executed without a human approval gate. Notifications are sent simultaneously.
- **Contamination / foreign_material events** trigger a line shutdown CAPA automatically — the most consequential auto-execution. The Slack message explicitly calls out the QA manager and ops lead, but the shutdown MR is posted before they respond.
- **Line shutdowns** (critical priority) generate `#quality-alerts` Slack messages. The downstream decision to physically halt the line is human — the agent only creates the MR and sends the alert.
- **OEE MRs** are informational; the maintenance team decides when and how to schedule the investigation. The agent's deduplication logic (step 8) prevents notification storms.
- **No rejection path**: There is no mechanism for a human to reject or cancel an auto-executed MR through the agent. Cancellation would need to happen directly in the MES.

## Limitations

- **Dry-run only in demo context**: The mock MES server at `localhost:3002` is a test fixture; no live MES is connected.
- **`defect_rate` events with `medium` severity are skipped**: The filter requires `severity in ("high", "critical")` OR `status == "open"`. In the dry-run data, `QE-002` (defect_rate, medium, open) is processed because its status is `open`, but a medium-severity, non-open defect event would be skipped.
- **No escalation hierarchy**: There is no mechanism to escalate critical events to a supervisor or on-call manager beyond the mock Slack message.
- **Mock Slack only**: `mock_slack_message()` always returns `sent: True`. No real Slack integration or webhook is implemented.
- **No RCA tracking**: The agent creates maintenance requests but does not track whether root cause analysis was completed or whether the CAPA was effective.
- **No multi-facility support**: `REQUESTER` and all API endpoints are single-plant; no multi-site routing is implemented.
- **OEE threshold is hardcoded**: `OEE_ALERT_THRESHOLD = 65.0` cannot be configured at runtime.

## Example Run

```bash
python3 pilot-agents/quality_capa_agent.py --dry-run
```

Condensed output:

```
[2026-03-14T09:30:00] === Quality CAPA Agent starting (dry_run=True) ===
[2026-03-14T09:30:00] Quality events fetched: 3
[2026-03-14T09:30:00] Existing maintenance requests: 0 (lines: set())
[2026-03-14T09:30:00] Processing QE-001: line=LINE-04 severity=high type=sensor_failure
[2026-03-14T09:30:00]   DRY-RUN: Would POST MR for LINE-04 [medium] — preventive_maintenance
[2026-03-14T09:30:00]   ACTION: PM work order — AUTO_EXECUTED | Slack -> #quality-alerts
[2026-03-14T09:30:00] Processing QE-002: line=LINE-02 severity=medium type=defect_rate
[2026-03-14T09:30:00]   DRY-RUN: Would POST MR for LINE-02 [high] — quality_hold
[2026-03-14T09:30:00]   ACTION: Quality hold — AUTO_EXECUTED | Slack -> #ops-notifications
[2026-03-14T09:30:00] Processing QE-003: line=LINE-01 severity=high type=contamination
[2026-03-14T09:30:00]   DRY-RUN: Would POST MR for LINE-01 [critical] — line_shutdown
[2026-03-14T09:30:00]   ACTION: Line shutdown + notification — AUTO_EXECUTED | Slack -> #quality-alerts
[2026-03-14T09:30:00] --- OEE Check ---
[2026-03-14T09:30:00]   OEE Alert: LINE-02 OEE=62.4% (threshold 65.0%)
[2026-03-14T09:30:00]   OEE MR created for LINE-02 | AUTO_EXECUTED | Slack -> #oee-alerts
[2026-03-14T09:30:00]   OEE Alert: LINE-04 OEE=49.1% (threshold 65.0%)
[2026-03-14T09:30:00]   OEE MR created for LINE-04 | AUTO_EXECUTED | Slack -> #oee-alerts

=== Summary ===
  Total MRs created:       5
  High severity events:    2
  OEE alerts actioned:     2
  Slack messages sent:     5
```
