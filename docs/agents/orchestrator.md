# Orchestrator
**Slug**: `orchestrator`
**File**: `pilot-agents/orchestrator.py`
**Lifecycle**: blueprint (coordination layer — not a DB blueprint; wraps other registered agents)
**Last generated**: 2026-03-14 | **Last verified**: 2026-03-14

## Purpose

The Orchestrator is a multi-agent coordination runner that executes multiple pilot agents in sequence, captures their individual outputs, and produces a combined cross-agent summary report. It solves the problem of running a full portfolio of agents in one command and aggregating their results into a single view — total estimated hours saved, total items requiring human review, per-agent metrics, and run duration.

Without the orchestrator, running 5 agents requires 5 separate commands, 5 separate output files, and manual aggregation of results. The orchestrator wraps this into a single `subprocess.run` loop, parsing each agent's stdout JSON and extracting standardized metrics per agent slug. The combined summary is written to `pilot-agents/outputs/orchestration_run_YYYYMMDD_HHMMSS.json` and is also printed to stdout so `server.py` can capture it when invoked via the Flask API endpoint.

The default agent set (when `--agents all` or no `--agents` flag) runs the 3 CG agents (replenishment, forecast, quality). The full set of 5 available agents includes those 3 plus the MFG maintenance agent and the AP invoice agent. Specifying explicit agent names by their short keys selects a custom subset.

## Inputs

- **Agent registry** (hardcoded in `AGENTS` dict): 5 agents, keyed by short name:
  - `replenishment` → `cg-replenishment-pr-agent` / `replenishment_agent.py`
  - `forecast` → `cg-demand-forecast-agent` / `demand_forecast_agent.py`
  - `quality` → `cg-quality-capa-agent` / `quality_capa_agent.py`
  - `maintenance` → `mfg-predictive-maintenance-agent` / `mfg-predictive-maintenance-agent.py`
  - `invoicing` → `ap-invoice-processing` / `ap-invoice-processing.py`
- **DEFAULT_AGENTS**: `["replenishment", "forecast", "quality"]` — used when `--agents all` or no agents specified.
- **Flags**:
  - `--agents <name> [name ...]`: One or more agent short names from the registry, or `all` to run all 5. Default: `["all"]` which resolves to DEFAULT_AGENTS (not ALL_AGENTS).
  - `--dry-run`: Pass `--dry-run` flag to each subprocess. Default: True (dry-run is the default unless `--live` is specified).
  - `--live`: Disable dry-run; run agents in live mode connecting to real APIs. Overrides `--dry-run`.

## Outputs

```json
{
  "orchestration_run_at": "2026-03-14T09:00:00.000000",
  "dry_run": true,
  "agents_requested": ["replenishment", "forecast", "quality"],
  "combined_summary": {
    "agents_run": 3,
    "agents_successful": 3,
    "total_hours_saved_est": 3.75,
    "total_requires_review": 4,
    "per_agent_metrics": {
      "cg-replenishment-pr-agent": {
        "prs_created": 3,
        "high_priority": 2,
        "hours_saved": 1.5
      },
      "cg-demand-forecast-agent": {
        "items_forecast": 8,
        "demand_cliffs": 2,
        "hours_saved": 1.5
      },
      "cg-quality-capa-agent": {
        "capa_actions": 3,
        "critical_events": 0,
        "hours_saved": 0.75
      }
    },
    "run_duration_secs_total": 4.2
  },
  "agent_outputs": {
    "cg-replenishment-pr-agent": {
      "slug": "cg-replenishment-pr-agent",
      "name": "replenishment",
      "description": "CG Inventory Replenishment PR Agent",
      "status": "success",
      "duration_secs": 1.4,
      "output": { "...": "full agent JSON output" },
      "stdout_tail": "...last 200 chars of stdout"
    }
  }
}
```

Written to `pilot-agents/outputs/orchestration_run_YYYYMMDD_HHMMSS.json`.

## Behavior

1. **Parse arguments**: Resolve `--agents` list to actual agent keys. If `all` or empty, use DEFAULT_AGENTS (replenishment, forecast, quality). Determine dry-run mode (default True; `--live` sets to False).
2. **Iterate agent list in sequence**: For each agent key:
   a. Check that the agent script file exists at its registered path. If not, mark status = "skipped" and continue.
   b. Build subprocess args: `[sys.executable, agent_file]` + `["--dry-run"]` if dry-run mode.
   c. Call `subprocess.run` with `capture_output=True`, `text=True`, `timeout=60`, `cwd=pilot-agents/`.
   d. Parse JSON from stdout: try each line of stdout as JSON; take the last valid dict. Fallback: try parsing entire stdout. Fallback 2: read the most recent `outputs/` file matching the agent slug pattern.
   e. Record outcome ("success" if returncode == 0, else "failed"), duration, and output JSON.
3. **Extract per-agent metrics** from each agent's output JSON using slug-specific field mappings:
   - `cg-replenishment-pr-agent`: `prs_created` (len), `high_priority` (len), `hours_saved` = prs * 0.5
   - `cg-demand-forecast-agent`: `items_forecast`, `demand_cliffs` (count where demand_cliff=True), `hours_saved` = 1.5 (fixed)
   - `cg-quality-capa-agent`: `capa_actions` (len), `critical_events` (count severity="critical"), `hours_saved` = capa * 0.25
   - `mfg-predictive-maintenance-agent`: `lines_at_risk` (len), `maintenance_requests_created`, `hours_saved` = requests * 1.0
   - `ap-invoice-processing`: `auto_approved`, `approval_required`, `anomalies_flagged`, `hours_saved` = auto_approved * 0.1
4. **Build combined summary**: Sum `total_hours_saved_est` and `total_requires_review` (high_priority + demand_cliffs + critical_events + lines_at_risk + approval_required) across successful agents.
5. **Write output file** to `pilot-agents/outputs/orchestration_run_YYYYMMDD_HHMMSS.json`.
6. **Print summary table** to stdout: agents run, hours saved, items requiring review, per-agent breakdown with hours saved.
7. **Print full JSON** to stdout (for `server.py` capture).

## HITL Decision Points

The orchestrator itself has no HITL gates. It is a runner and aggregator. HITL decisions are owned by the individual agents it invokes:

- **Items requiring review** (`total_requires_review`): This is a combined count surfaced in the summary. The individual items requiring human attention live in each agent's own output and dashboard view.
- **Agent failures**: If an agent returns a non-zero exit code (status = "failed") or times out (status = "timeout"), the orchestrator logs it but does not retry. A human should investigate the failed agent separately.
- **Skipped agents**: If an agent script file is missing (status = "skipped"), the orchestrator continues without it. No alert is raised.

## Limitations

- **Sequential execution**: Agents run one at a time via `subprocess.run`. There is no parallel execution. Total runtime is the sum of all agent runtimes.
- **60-second per-agent timeout**: Any agent that takes longer than 60 seconds is killed and marked as "timeout". This can happen under heavy API load in live mode.
- **Default "all" resolves to CG-only**: `DEFAULT_AGENTS = ["replenishment", "forecast", "quality"]` — specifying `all` does not run all 5 agents. To run all 5, use `--agents replenishment forecast quality maintenance invoicing`.
- **JSON parsing is fragile**: The orchestrator parses agent stdout by trying each line as JSON and taking the last valid dict. Agents that print non-JSON progress lines before the final JSON blob can cause parse failures.
- **Dry-run default**: `--dry-run` defaults to True. Live mode requires explicitly passing `--live`.
- **No DB logging**: The orchestrator itself does not log to `pilot_runs`. Only the individual agents log their own runs.
- **No dependency management**: Agents are run in the order listed on the command line regardless of output dependencies. There is no DAG or conditional branching.
- **`--agents all` quirk**: `all` resolves to DEFAULT_AGENTS (3 CG agents), not ALL_AGENTS (all 5). The variable `ALL_AGENTS = list(AGENTS.keys())` exists in the code but is not wired to the `all` keyword.

## Example Run

```bash
# Default: run 3 CG agents in dry-run mode
python3 "pilot-agents/orchestrator.py" --dry-run

# Run all 5 agents
python3 "pilot-agents/orchestrator.py" --agents replenishment forecast quality maintenance invoicing --dry-run

# Run just maintenance + invoicing
python3 "pilot-agents/orchestrator.py" --agents maintenance invoicing --dry-run
```

Condensed stdout for default 3-agent run:

```
============================================================
  Multi-Agent Orchestrator — Business Agents Platform
============================================================
[2026-03-14T09:00:00] Starting orchestration run: 3 agents
[2026-03-14T09:00:00] Mode: DRY-RUN
[2026-03-14T09:00:00] Agents: replenishment, forecast, quality

[2026-03-14T09:00:00] [1/3] CG Inventory Replenishment PR Agent
[2026-03-14T09:00:00]   Running CG Inventory Replenishment PR Agent...
[2026-03-14T09:00:01]      success (1.4s)

[2026-03-14T09:00:01] [2/3] CG Demand Forecast Agent
[2026-03-14T09:00:01]   Running CG Demand Forecast Agent...
[2026-03-14T09:00:02]      success (1.5s)

[2026-03-14T09:00:02] [3/3] CG Quality & CAPA Agent
[2026-03-14T09:00:02]   Running CG Quality & CAPA Agent...
[2026-03-14T09:00:03]      success (1.3s)

============================================================
  ORCHESTRATION COMPLETE
============================================================
  Agents run:         3 (3 successful)
  Est. hours saved:   3.75h
  Requires review:    4 items
  Total duration:     4.2s
  Output:             pilot-agents/outputs/orchestration_run_20260314_090003.json
============================================================

  PER-AGENT BREAKDOWN:
  CG Inventory Replenishment PR Agent              1.5h saved
  CG Demand Forecast Agent                         1.5h saved
  CG Quality & CAPA Agent                          0.8h saved
```
