# MFG Predictive Maintenance Agent
**Slug**: `mfg-predictive-maintenance-agent`
**File**: `pilot-agents/mfg-predictive-maintenance-agent.py`
**Lifecycle**: sandbox (MFG pilot — registered in DB, wired into server.py and orchestrator.py)
**Last generated**: 2026-03-14 | **Last verified**: 2026-03-14

## Purpose

The MFG Predictive Maintenance Agent monitors Overall Equipment Effectiveness (OEE) across production lines and automatically creates maintenance work requests for lines that fall below performance thresholds. In a typical manufacturing environment, production supervisors manually check OEE dashboards, interpret declining trends, and raise maintenance tickets — a process that introduces delays and relies on human attention to catch gradual degradation before it becomes unplanned downtime.

The agent replaces that loop by fetching OEE data from the Mock MES API (port 3002), evaluating each line against two independent triggers (absolute OEE floor and week-over-week decline rate), and immediately POSTing maintenance requests for any flagged line. It is designed for CG/FMCG manufacturing environments with named production lines (Assembly, Processing, Packing). The agent logs every run to the `pilot_runs` table in `business_agents.db` via `agent_runner.log_to_db`, making its history visible in the dashboards and enterprise portfolio views.

## Inputs

- **Mock MES API** (live mode): `GET http://localhost:3002/api/oee` — returns a list of production line OEE objects. Per-line history fetched from `GET /api/oee/history/{line_id}` returning `oee_history_4wk` array (4-week history, most-recent last).
- **DRY_RUN_LINES** (dry-run / fallback): 5 hardcoded production line records:
  - `LINE-A`: Assembly Line A (Packaging) — OEE 82%, 4-week trend [84, 86, 84, 82%]
  - `LINE-B`: Assembly Line B (Filling) — OEE 71%, trend [80, 77, 74, 71%]
  - `LINE-C`: Processing Line C (Mixing) — OEE 88%, trend [85, 87, 88, 88%]
  - `LINE-D`: Processing Line D (Blending) — OEE 69%, trend [82, 79, 73, 69%]
  - `LINE-E`: Packing Line E (Labeling) — OEE 79%, trend [81, 80, 79, 79%]
  Each record also includes `downtime_minutes_today` and `quality_events_week`.
- **Flags**:
  - `--dry-run`: Uses DRY_RUN_LINES; skips all HTTP calls to MES; maintenance requests are simulated (not POSTed). Detected via `"--dry-run" in sys.argv`.

## Outputs

```json
{
  "run_at": "2026-03-14T09:00:00.000000",
  "agent": "mfg-predictive-maintenance-agent",
  "dry_run": true,
  "lines_analysed": 5,
  "lines_at_risk": [
    {
      "line_id": "LINE-B",
      "name": "Assembly Line B — Filling",
      "current_oee": 0.71,
      "week_delta": -0.09,
      "downtime_minutes_today": 45,
      "quality_events_week": 3,
      "flag_reason": ["OEE 71.0% below 75% threshold", "Week delta -9.0% below -5% threshold"],
      "maintenance_request": {
        "request_id": "MR-DRY-LINE-B",
        "line_id": "LINE-B",
        "maintenance_type": "predictive",
        "priority": "medium",
        "reason": "OEE 71.0% below threshold | Week delta: -9.0%",
        "requested_by": "predictive-maintenance-agent",
        "status": "simulated"
      },
      "action": "maintenance_request_created"
    }
  ],
  "maintenance_requests_created": 3,
  "lines_ok": ["LINE-A", "LINE-C", "LINE-E"]
}
```

Output is written to `pilot-agents/outputs/mfg_predictive_maintenance_YYYYMMDD_HHMMSS.json` via `agent_runner.write_output`. Run is logged to `pilot_runs` table in `business_agents.db`.

## Behavior

1. **Fetch OEE data**: In dry-run mode, return DRY_RUN_LINES. In live mode, call `GET /api/oee`. If the MES API is unavailable or returns an unexpected response shape, fall back to DRY_RUN_LINES silently.
2. **Fetch per-line history** (live mode only): For each line, call `GET /api/oee/history/{line_id}` to retrieve the 4-week OEE history array. Dry-run uses the embedded `oee_history_4wk` from DRY_RUN_LINES.
3. **Evaluate each line** against two independent thresholds:
   - `current_oee < 0.75` (75% OEE floor)
   - `week_delta = current_oee - oee_history_4wk[0]` < -0.05 (more than 5-percentage-point decline vs. 4 weeks ago)
   Either condition alone is sufficient to flag the line. Both conditions can fire simultaneously.
4. **Classify priority**: Lines with `current_oee < 0.70` (70% floor) get priority = "high". Lines between 70–74% get priority = "medium".
5. **Create maintenance requests**: For each flagged line, build a maintenance request body and POST to `http://localhost:3002/api/maintenance-requests`. In dry-run mode, return a simulated response with `request_id = "MR-DRY-{line_id}"` and `status = "simulated"`.
6. **Build output JSON** with `lines_analysed`, `lines_at_risk` (full detail including maintenance_request), `maintenance_requests_created`, and `lines_ok` (list of OK line IDs).
7. **Write output file** to `outputs/` via `agent_runner.write_output`.
8. **Log to DB** via `agent_runner.log_to_db`: records `story_id`, outcome ("success" if requests > 0, "partial" if 0), `files_changed`, `tools_used`, `learnings`, and `duration_secs` into `pilot_runs` table.

## HITL Decision Points

- **Maintenance requests are auto-created** (live mode): The agent POSTs maintenance requests to the MES without human approval. This is a L2 (analyze + execute) pattern.
- **Priority = "high" lines** (OEE < 70%): Should trigger immediate production supervisor notification. The dashboard displays these in the HITL approval queue for confirmation and scheduling.
- **Priority = "medium" lines** (OEE 70–74% or week delta < -5%): Maintenance request is created; a maintenance planner should schedule within 24–48 hours.
- **No auto-escalation to shutdown**: The agent does not stop or pause production lines. It raises requests only. Production decisions remain with humans.
- **In dry-run mode**: All maintenance requests are simulated — no MES calls are made. The full output is suitable for dashboard demo and run theater replay.

## Limitations

- **MES dependency**: Live mode requires the Mock MES server running at `localhost:3002` via `cd sandbox-systems && ./start-all.sh`. If unavailable, the agent silently falls back to dry-run data without alerting the operator.
- **Fixed thresholds**: OEE floor (75%) and week-delta threshold (-5%) are hardcoded constants. There is no per-line configuration or dynamic threshold learning.
- **4-week history window only**: The week_delta compares current OEE to 4 weeks prior (the first element of `oee_history_4wk`). Intermediate trend analysis (e.g., 2-week slope) is not performed.
- **No shift or time-of-day context**: OEE is evaluated as a daily aggregate; shift-level anomalies are not detectable.
- **DB path is hardcoded**: `DB_PATH = "/Users/keith_ai/Documents/Agentic Projects/business-agents/business_agents.db"`. Portability to another machine requires changing this constant.
- **No maintenance request deduplication**: Running the agent twice on the same low-OEE data will create duplicate maintenance requests in the MES.
- **`pilot_runs` table required**: The `log_to_db` call will fail silently if the `pilot_runs` table does not exist in the DB.

## Example Run

```bash
python3 "pilot-agents/mfg-predictive-maintenance-agent.py" --dry-run
```

Condensed output:

```
[2026-03-14T09:00:00] === MFG Predictive Maintenance Agent starting (dry_run=True) ===
[2026-03-14T09:00:00] DRY-RUN: Using simulated production line OEE data
[2026-03-14T09:00:00] Lines fetched: 5
[2026-03-14T09:00:00] OK:      LINE-A OEE=82.0% delta=-2.0%
[2026-03-14T09:00:00] FLAGGED: LINE-B — OEE 71.0% below 75% threshold | Week delta -9.0% below -5% threshold
[2026-03-14T09:00:00] OK:      LINE-C OEE=88.0% delta=3.0%
[2026-03-14T09:00:00] FLAGGED: LINE-D — OEE 69.0% below 75% threshold | Week delta -13.0% below -5% threshold
[2026-03-14T09:00:00] OK:      LINE-E OEE=79.0% delta=-2.0%
[2026-03-14T09:00:00] Lines at risk: 2 | Lines OK: 3
[2026-03-14T09:00:00]   DRY-RUN: Would POST maintenance request for LINE-B [medium]
[2026-03-14T09:00:00]   DRY-RUN: Would POST maintenance request for LINE-D [high]
[2026-03-14T09:00:00] Maintenance requests created: 2
[2026-03-14T09:00:00] === MFG Predictive Maintenance Agent complete (0.1s) ===

*** LINES AT RISK — MAINTENANCE REQUIRED ***
  LINE-B: OEE=71.0% | delta=-9.0% | Request: MR-DRY-LINE-B [medium]
  LINE-D: OEE=69.0% | delta=-13.0% | Request: MR-DRY-LINE-D [high]
```
