# Developer Guide — AI Agent Platform

**Last updated**: 2026-03-14
**Workspace root**: `/Users/keith_ai/Documents/Agentic Projects/`

This guide covers four worked examples for the most common extension tasks. Each section walks through real code patterns from the codebase — not pseudocode.

---

## Quick Reference

| Task | Key files to touch | Command to verify |
|---|---|---|
| Add a new agent | `pilot-agents/<agent>.py`, `dashboards/server.py` (2 dicts + 2 functions), `docs/agents/<slug>.md` | `python3 pilot-agents/<agent>.py --dry-run` |
| Add a new industry | `business-agents/seed_<industry>.py`, `registry.json`, `index.html` | `python3 business-agents/query.py opportunities <CODE>` |
| Add a new dashboard | `dashboards/<persona>.html`, `registry.json`, `index.html` | Open `http://localhost:8500/<persona>.html` |
| Add a new client portal | `clients/<slug>/profile.json`, `clients/<slug>/index.html`, `clients/seed_clients.py` | Open `clients/index.html` |

---

## 1. Adding a New Agent

**Worked example**: `energy-demand-response-agent` — monitors grid load signals and dispatches demand response events.

### Step 1: Start from the replenishment agent template

Every agent in this codebase follows the same structure as `pilot-agents/replenishment_agent.py`. Copy it to start:

```bash
cp "/Users/keith_ai/Documents/Agentic Projects/pilot-agents/replenishment_agent.py" \
   "/Users/keith_ai/Documents/Agentic Projects/pilot-agents/demand_response_agent.py"
```

The canonical structure is:

```
1. Module docstring with logic, usage, and --dry-run note
2. Imports (stdlib only + agent_runner)
3. Configuration constants (SLUG, SAP_BASE / MES_BASE, DB_PATH, PLANT)
4. record_value() hook for value_tracking table
5. DRY_RUN_* data — hardcoded realistic test fixtures
6. ts() and log() helpers
7. fetch_<data>() — calls API, falls back to DRY_RUN data
8. process_<item>() — the core action (POST, PATCH, etc.)
9. run(dry_run) — the 5-step pipeline
10. if __name__ == "__main__": entry point with --dry-run flag check
```

### Step 2: Define SLUG, constants, and DRY_RUN_DATA

Replace the configuration block at the top:

```python
SAP_BASE   = "http://localhost:3001"
MES_BASE   = "http://localhost:3002"
DB_PATH    = "/Users/keith_ai/Documents/Agentic Projects/business-agents/business_agents.db"
STORY_ID   = "energy-demand-response-agent"   # must match agent_blueprints.slug
REQUESTER  = "demand-response-agent-v1"
SITE       = "ENERGY01"
```

Define your dry-run fixtures — realistic enough to test all code paths:

```python
DRY_RUN_GRID_SIGNALS = [
    {"signal_id": "GS-001", "site": "ENERGY01", "load_kw": 4800, "threshold_kw": 4000,
     "event_type": "peak_demand", "duration_mins": 30, "curtailable_assets": ["HVAC-3", "Pump-7"]},
    {"signal_id": "GS-002", "site": "ENERGY01", "load_kw": 3200, "threshold_kw": 4000,
     "event_type": "normal", "duration_mins": 0, "curtailable_assets": []},
    {"signal_id": "GS-003", "site": "ENERGY01", "load_kw": 5100, "threshold_kw": 4000,
     "event_type": "critical_peak", "duration_mins": 60, "curtailable_assets": ["HVAC-1", "HVAC-2", "Chiller-1"]},
]
```

### Step 3: Implement the 5-step pipeline

The `run()` function always follows this pattern — modelled directly on `replenishment_agent.py`:

```python
def run(dry_run: bool = False):
    start_time = datetime.now()
    log(f"=== Demand Response Agent starting (dry_run={dry_run}) ===")

    # Step 1: Fetch data
    signals = fetch_grid_signals(dry_run)
    log(f"Grid signals fetched: {len(signals)} signals")

    events_dispatched = []
    normal_count = 0

    # Step 2 & 3: Analyze + decide
    for signal in signals:
        load       = signal.get("load_kw", 0)
        threshold  = signal.get("threshold_kw", 0)
        event_type = signal.get("event_type", "normal")

        if event_type == "normal" or load <= threshold:
            normal_count += 1
            continue

        # Determine severity
        pct_over  = (load - threshold) / threshold
        severity  = "critical" if pct_over > 0.2 else "high"

        log(f"Triggered: {signal['signal_id']} load={load}kw threshold={threshold}kw "
            f"pct_over={pct_over:.0%} severity={severity}")

        # Step 4: Execute action (POST to MES/SAP)
        result = dispatch_demand_response(signal, severity, dry_run)
        events_dispatched.append(result)

    log(f"Checked {len(signals)} signals — dispatched {len(events_dispatched)} DR events")

    # Step 5: Build output dict (server.py _build_summary reads from these keys)
    now     = datetime.now()
    ts_file = now.strftime("%Y%m%d_%H%M%S")
    output  = {
        "run_at":              now.isoformat(),
        "trigger":             "load_threshold_exceeded",
        "authority":           "medium",
        "dry_run":             dry_run,
        "signals_checked":     len(signals),
        "events_dispatched":   len(events_dispatched),
        "dispatch_details":    events_dispatched,
        "normal_signals":      normal_count,
        "escalations":         [],
    }

    filename = f"demand_response_run_{ts_file}.json"
    write_output(filename, output)

    duration = (datetime.now() - start_time).total_seconds()
    log_to_db(
        db_path       = DB_PATH,
        story_id      = STORY_ID,
        outcome       = "success" if events_dispatched else "partial",
        files_changed = [filename],
        tools_used    = ["GET /api/grid-signals", "POST /api/demand-response-events"],
        learnings     = (
            f"Checked {len(signals)} signals, dispatched {len(events_dispatched)} DR events. "
            f"{'DRY RUN. ' if dry_run else ''}"
        ),
        duration_secs = duration,
    )

    # Value tracking (mirrors replenishment_agent.py pattern exactly)
    try:
        record_value(
            blueprint_slug = STORY_ID,
            agent_name     = "demand_response_agent",
            run_ref        = filename,
            metric_type    = "events_dispatched",
            delta          = len(events_dispatched),
            unit           = "count",
        )
        record_value(
            blueprint_slug = STORY_ID,
            agent_name     = "demand_response_agent",
            run_ref        = filename,
            metric_type    = "hours_saved",
            delta          = round(len(events_dispatched) * 0.75, 2),
            unit           = "hours",
        )
    except Exception as e:
        log(f"[value_tracking] Warning: could not record value: {e}")

    log(f"=== Demand Response Agent complete ({duration:.1f}s) ===")
    return output
```

The fetch function uses the same fallback pattern as replenishment:

```python
def fetch_grid_signals(dry_run: bool) -> list[dict]:
    if dry_run:
        log("DRY-RUN: Using simulated grid signal data")
        return DRY_RUN_GRID_SIGNALS

    url = f"{MES_BASE}/api/grid-signals"
    log(f"Calling GET {url}")
    status, data = call_api(url)

    if status is None:
        log("WARNING: MES API unavailable — switching to dry-run mode")
        return DRY_RUN_GRID_SIGNALS

    if status != 200:
        log(f"WARNING: MES returned HTTP {status} — switching to dry-run mode")
        return DRY_RUN_GRID_SIGNALS

    # Handle multiple response shapes
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("signals", "items", "data", "results"):
            if key in data and isinstance(data[key], list):
                return data[key]

    log("WARNING: Unexpected response shape — switching to dry-run mode")
    return DRY_RUN_GRID_SIGNALS
```

### Step 4: Register in server.py

Four edits are required in `dashboards/server.py`. All edits are additive — no existing code needs to change.

**Edit 1 — AGENT_PATHS dict** (lines 25–43 in the real file):

```python
AGENT_PATHS = {
    # ... existing entries ...
    # ── Energy Agents ──
    "energy-demand-response-agent": str(AGENTS_DIR / "demand_response_agent.py"),
}
```

**Edit 2 — PERSONA_MAP dict** (lines 45–59 in the real file):

```python
PERSONA_MAP = {
    # ... existing entries ...
    "energy-demand-response-agent": "operations",   # or "finance" for cost-focused view
}
```

The valid persona values that map to dashboard files are:
`"operations"`, `"finance"`, `"compliance"`, `"sales"`, `"engineering"`, `"customer-service"`, `"executive"`

**Edit 3 — `_extract_recommendations()` function** (starts at line 361 in the real file):

Add a new `elif` block inside the try:

```python
elif slug == "energy-demand-response-agent":
    for event in output.get("dispatch_details", []):
        severity = event.get("severity", "medium")
        urgency  = "critical" if severity == "critical" else "high"
        item_id  = event.get("signal_id", "")
        label    = f"DR Event {item_id} — {event.get('event_type', 'demand response')}"
        action   = (f"Curtail {len(event.get('curtailed_assets', []))} assets "
                    f"for {event.get('duration_mins', '?')} min")
        conn.execute("""
            INSERT INTO recommendations
                (run_id, slug, rec_type, item_id, item_label, urgency, recommended_action, detail_json)
            VALUES (?, ?, 'dr_event', ?, ?, ?, ?, ?)
        """, (run_id, slug, item_id, label, urgency, action, json.dumps(event)))
        recs.append({
            "item_id": item_id, "item_label": label,
            "urgency": urgency, "recommended_action": action, "rec_type": "dr_event"
        })
```

**Edit 4 — `_build_summary()` function** (starts at line 640 in the real file):

Add a new `elif` block:

```python
elif slug == "energy-demand-response-agent":
    n = len(output.get("dispatch_details", []))
    s = output.get("signals_checked", 0)
    return f"{s} signals checked — {n} demand response events dispatched"
```

### Step 5: Write the agent spec

Create `docs/agents/energy-demand-response-agent.md` following the exact format of `docs/agents/cg-replenishment-pr-agent.md`:

```markdown
# Energy Demand Response Agent
**Slug**: `energy-demand-response-agent`
**File**: `pilot-agents/demand_response_agent.py`
**Lifecycle**: blueprint
**Last generated**: YYYY-MM-DD | **Last verified**: YYYY-MM-DD

## Purpose
[One paragraph: what problem it solves, who uses it, how it fits the workflow]

## Inputs
- **MES Grid Signal API** (`GET http://localhost:3002/api/grid-signals`): ...
- **`--dry-run` flag**: ...
- **Hardcoded configuration**: ...

## Outputs
[Output JSON schema with a realistic example]

## Behavior
1. Fetch grid signals ...
2. Evaluate each signal ...
3. ...

## HITL Decision Points
- **Authority level is `medium`**: Agent dispatches DR events but requires ...
- **Escalations**: ...

## Limitations
- ...

## Example Run
```bash
python3 pilot-agents/demand_response_agent.py --dry-run
```
```

Required sections (in order): Purpose, Inputs, Outputs, Behavior, HITL Decision Points, Limitations, Example Run.

### Step 6: Register in the orchestrator

Add to the `AGENTS` dict in `pilot-agents/orchestrator.py`:

```python
AGENTS = {
    # ... existing entries ...
    "demand-response": {
        "slug":         "energy-demand-response-agent",
        "file":         str(SCRIPT_DIR / "demand_response_agent.py"),
        "description":  "Energy Demand Response Agent",
        "category":     "energy",
        "value_metric": "events_dispatched",
    },
}
```

Then add metric extraction to `extract_summary_metrics()`:

```python
elif slug == "energy-demand-response-agent":
    metrics["events_dispatched"] = len(output.get("dispatch_details", []))
    metrics["hours_saved"]       = round(metrics["events_dispatched"] * 0.75, 2)
```

### Step 7: Test

```bash
# Dry-run (always safe, no API calls)
python3 "/Users/keith_ai/Documents/Agentic Projects/pilot-agents/demand_response_agent.py" --dry-run

# Via orchestrator
python3 "/Users/keith_ai/Documents/Agentic Projects/pilot-agents/orchestrator.py" \
  --agents demand-response --dry-run

# Via dashboard server (start server first)
python3 "/Users/keith_ai/Documents/Agentic Projects/dashboards/server.py"
# Then POST: curl -X POST http://localhost:8500/api/run/energy-demand-response-agent
```

### Common Pitfalls — New Agents

1. **Missing `output_json` key in server.py**: The `/api/run/<slug>` endpoint reads the agent's stdout looking for a JSON object. Agents must either `print(json.dumps(output))` or write to `outputs/` — the server tries both. The `write_output()` function from `agent_runner` handles the file path automatically.

2. **`STORY_ID` mismatch**: The `STORY_ID` constant must exactly match the `slug` field in `agent_blueprints` table. The DB lookup in `_extract_recommendations` queries `pilot_runs.slug` which is set from the URL route parameter, not from the agent file itself.

3. **`record_value()` is fire-and-forget**: It wraps everything in try/except. If `value_tracking` table doesn't exist, it silently continues. Do not rely on it for control flow.

4. **`call_api()` uses stdlib only**: No `requests` library. The function signature is `call_api(url, method="GET", body=None, timeout=5)`. Always check `if status is None` before checking `if status != 200` — `None` means the server was unreachable, not an HTTP error.

5. **`log_to_db()` `story_id` parameter**: The function auto-increments `iteration_num` per `story_id`. If you use the wrong slug here, your run history will be split across two entries in the DB.

---

## 2. Adding a New Industry

**Worked example**: Agriculture (code `AGR`) — 3 blueprints, ~50 processes.

### Step 1: Create the seeder script

Copy the pattern from `business-agents/seed_retail.py` — it is the most recent and cleanest seeder. The file structure is:

```
1. Module docstring with schema documentation
2. DB_PATH using os.path.abspath(__file__)
3. Helper functions: get_industry_id, get_function_id, get_process_id,
   upsert_process, link_industry_process, add_process_action,
   add_capability, upsert_system, link_process_system
4. seed_processes(conn)  — processes + industry_processes links
5. seed_systems(conn)    — systems + process_systems links
6. seed_blueprints(conn) — agent_blueprints rows
7. main()               — connect, PRAGMA foreign_keys ON, call all seeds, commit
```

Create `/Users/keith_ai/Documents/Agentic Projects/business-agents/seed_agriculture.py`:

```python
"""
seed_agriculture.py — Seeds the Agriculture (AGR) sector into business_agents.db.

Run: python3 business-agents/seed_agriculture.py

Idempotent — safe to re-run. Uses upsert_process (checks apqc_code existence)
and INSERT OR IGNORE for all junction tables.

Schema constraints:
  process_agent_actions.action_type IN ('monitor','analyze','generate','execute','coordinate')
  process_systems.integration       IN ('read','write','read_write')
  agent_blueprints.trigger_type     IN ('scheduled','event','threshold','manual')
  agent_blueprints.authority_level  IN ('low','medium','high')
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "business_agents.db")
NOW     = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def get_industry_id(conn, code):
    row = conn.execute("SELECT id FROM industries WHERE code=?", (code,)).fetchone()
    if not row:
        raise ValueError(f"Industry code '{code}' not found — insert it first.")
    return row[0]


def get_function_id(conn, name_fragment):
    row = conn.execute(
        "SELECT id FROM functions WHERE name LIKE ?", (f"%{name_fragment}%",)
    ).fetchone()
    if not row:
        raise ValueError(f"Function matching '{name_fragment}' not found")
    return row[0]


def get_process_id(conn, apqc_code):
    row = conn.execute(
        "SELECT id FROM processes WHERE apqc_code=?", (apqc_code,)
    ).fetchone()
    if not row:
        raise ValueError(f"Process with apqc_code '{apqc_code}' not found")
    return row[0]


def upsert_process(conn, apqc_code, function_id, parent_apqc, level, name, description=None):
    existing = conn.execute(
        "SELECT id FROM processes WHERE apqc_code=?", (apqc_code,)
    ).fetchone()
    if existing:
        return
    parent_id = None
    if parent_apqc:
        parent_id = get_process_id(conn, parent_apqc)
    conn.execute(
        """INSERT INTO processes
               (apqc_code, function_id, parent_id, level, name, description, is_universal)
               VALUES (?,?,?,?,?,?,0)""",
        (apqc_code, function_id, parent_id, level, name, description),
    )


def link_industry_process(conn, industry_id, apqc_code, relevance, notes=None):
    proc_id = get_process_id(conn, apqc_code)
    conn.execute(
        """INSERT OR IGNORE INTO industry_processes
               (industry_id, process_id, relevance, industry_notes)
               VALUES (?,?,?,?)""",
        (industry_id, proc_id, relevance, notes),
    )


def add_process_action(conn, apqc_code, industry_id, action_type, feasibility, value, notes=None):
    proc_id = get_process_id(conn, apqc_code)
    conn.execute(
        """INSERT OR IGNORE INTO process_agent_actions
               (process_id, industry_id, action_type, feasibility, value, notes)
               VALUES (?,?,?,?,?,?)""",
        (proc_id, industry_id, action_type, feasibility, value, notes),
    )


def upsert_system(conn, name, vendor, category, description=None):
    existing = conn.execute("SELECT id FROM systems WHERE name=?", (name,)).fetchone()
    if existing:
        return existing[0]
    conn.execute(
        "INSERT INTO systems (name, vendor, category, description) VALUES (?,?,?,?)",
        (name, vendor, category, description),
    )
    return conn.execute(
        "SELECT id FROM systems WHERE name=? ORDER BY id DESC LIMIT 1", (name,)
    ).fetchone()[0]


def link_process_system(conn, apqc_code, system_id, industry_id, integration, notes=None):
    proc_id = get_process_id(conn, apqc_code)
    conn.execute(
        """INSERT OR IGNORE INTO process_systems
               (process_id, system_id, industry_id, integration, notes)
               VALUES (?,?,?,?,?)""",
        (proc_id, system_id, industry_id, integration, notes),
    )


def seed_industry(conn):
    """Insert the AGR industry row if not present."""
    existing = conn.execute("SELECT id FROM industries WHERE code='AGR'").fetchone()
    if existing:
        print("[INFO] AGR industry already exists")
        return existing[0]
    conn.execute(
        "INSERT INTO industries (name, code, description) VALUES (?,?,?)",
        ("Agriculture", "AGR", "Crop production, livestock, precision agriculture, and agri-tech")
    )
    row = conn.execute("SELECT id FROM industries WHERE code='AGR'").fetchone()
    print(f"[INFO] Inserted AGR industry id={row[0]}")
    return row[0]


def seed_processes(conn, ind_id):
    f4 = get_function_id(conn, "Deliver Physical Products")
    f9 = get_function_id(conn, "Manage Financial Resources")

    # Level 1 processes
    upsert_process(conn, "AGR-4.1", f4, None, 1,
        "Crop Production Planning",
        "Plan planting schedules, field allocations, and resource requirements based on demand and yield forecasts")

    upsert_process(conn, "AGR-4.2", f4, None, 1,
        "Precision Irrigation Management",
        "Monitor soil moisture, weather forecasts, and crop water stress to automate irrigation scheduling")

    upsert_process(conn, "AGR-4.3", f4, None, 1,
        "Harvest Scheduling and Logistics",
        "Optimize harvest timing, equipment routing, and transport coordination to minimize post-harvest loss")

    # Level 2 sub-processes
    upsert_process(conn, "AGR-4.1.1", f4, "AGR-4.1", 2,
        "Yield Forecast Modeling",
        "Integrate satellite imagery, weather data, and historical yields to forecast crop output by field and variety")

    upsert_process(conn, "AGR-4.1.2", f4, "AGR-4.1", 2,
        "Input Procurement Planning",
        "Calculate seed, fertilizer, and chemical requirements from yield forecast; generate procurement requisitions")

    # Link to industry
    for code in ["AGR-4.1", "AGR-4.2", "AGR-4.3", "AGR-4.1.1", "AGR-4.1.2"]:
        link_industry_process(conn, ind_id, code, relevance=8, notes="Core agriculture operations")

    # Agent actions
    add_process_action(conn, "AGR-4.1.1", ind_id, "analyze",   feasibility=8, value=9,
        notes="ML yield forecast from satellite + weather data")
    add_process_action(conn, "AGR-4.2",   ind_id, "monitor",   feasibility=9, value=8,
        notes="Real-time soil moisture monitoring and irrigation trigger")
    add_process_action(conn, "AGR-4.1.2", ind_id, "generate",  feasibility=7, value=8,
        notes="Auto-generate input procurement requisitions from yield forecast")
    add_process_action(conn, "AGR-4.3",   ind_id, "coordinate", feasibility=7, value=9,
        notes="Harvest logistics coordination — equipment and transport routing")

    print("[2] Processes seeded")


def seed_systems(conn, ind_id):
    systems = [
        ("John Deere Operations Center", "John Deere", "Precision-Ag",
         "Field management platform for planting, application, and harvest data"),
        ("Trimble Ag Software", "Trimble", "Precision-Ag",
         "Agronomy planning and field operations management with GPS integration"),
        ("Climate FieldView", "Bayer", "Analytics",
         "Digital agronomy platform for field data, benchmarking, and prescription maps"),
        ("SAP Agribusiness", "SAP", "ERP",
         "Commodity trading, risk management, and supply chain for agribusiness"),
    ]
    sys_ids = {}
    for name, vendor, category, desc in systems:
        sys_ids[name] = upsert_system(conn, name, vendor, category, desc)

    link_process_system(conn, "AGR-4.1.1", sys_ids["Climate FieldView"], ind_id, "read",
        "Yield forecast data source")
    link_process_system(conn, "AGR-4.2",   sys_ids["Trimble Ag Software"], ind_id, "read_write",
        "Irrigation control integration")
    link_process_system(conn, "AGR-4.1.2", sys_ids["SAP Agribusiness"],   ind_id, "write",
        "Procurement requisition target")
    print("[3] Systems seeded")


def seed_blueprints(conn, ind_id):
    blueprints = [
        {
            "slug":    "agr-crop-yield-forecast-agent",
            "title":   "Crop Yield Forecast Agent",
            "trigger_type": "scheduled",
            "trigger_spec": "Weekly on Monday 06:00 local",
            "authority_level": "low",
            "estimated_time_saved_hrs_week": 6,
            "business_value": "Replaces manual agronomist yield estimation; feeds procurement planning",
            "kpis": "Forecast accuracy ±10%, procurement lead time reduction 20%",
        },
        {
            "slug":    "agr-precision-irrigation-agent",
            "title":   "Precision Irrigation Agent",
            "trigger_type": "threshold",
            "trigger_spec": "Soil moisture < field capacity threshold",
            "authority_level": "medium",
            "estimated_time_saved_hrs_week": 8,
            "business_value": "Reduces water use 15–25% while maintaining yield — automated irrigation scheduling",
            "kpis": "Water consumption kL/hectare, yield per hectare",
        },
        {
            "slug":    "agr-harvest-logistics-agent",
            "title":   "Harvest Logistics Coordination Agent",
            "trigger_type": "event",
            "trigger_spec": "Crop maturity signal from remote sensing",
            "authority_level": "low",
            "estimated_time_saved_hrs_week": 10,
            "business_value": "Minimises post-harvest loss through timely logistics coordination",
            "kpis": "Post-harvest loss %, equipment utilisation rate",
        },
    ]
    for bp in blueprints:
        existing = conn.execute(
            "SELECT id FROM agent_blueprints WHERE slug=?", (bp["slug"],)
        ).fetchone()
        if existing:
            print(f"   Blueprint {bp['slug']} already exists — skipping")
            continue
        conn.execute(
            """INSERT INTO agent_blueprints
                   (slug, title, version, status, trigger_type, trigger_spec,
                    authority_level, business_value, estimated_time_saved_hrs_week, kpis,
                    lifecycle_stage, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,'blueprint',?,?)""",
            (bp["slug"], bp["title"], "1.0", "draft", bp["trigger_type"], bp["trigger_spec"],
             bp["authority_level"], bp["business_value"],
             bp["estimated_time_saved_hrs_week"], bp["kpis"], NOW, NOW),
        )
        print(f"   + Blueprint: {bp['slug']}")
    print("[4] Blueprints seeded")


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    print(f"Connected to: {DB_PATH}")

    ind_id = seed_industry(conn)
    seed_processes(conn, ind_id)
    seed_systems(conn, ind_id)
    seed_blueprints(conn, ind_id)

    conn.commit()
    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
```

### Step 2: Run the seeder

```bash
python3 "/Users/keith_ai/Documents/Agentic Projects/business-agents/seed_agriculture.py"
```

Expected output:

```
Connected to: .../business_agents.db
[INFO] Inserted AGR industry id=14
[2] Processes seeded
[3] Systems seeded
[4] Blueprints seeded
Done.
```

### Step 3: Verify

```bash
# Check opportunities scored for AGR
python3 "/Users/keith_ai/Documents/Agentic Projects/business-agents/query.py" opportunities AGR

# Check processes were linked
python3 "/Users/keith_ai/Documents/Agentic Projects/business-agents/query.py" processes
```

### Step 4: Update registry.json and index.html

Add the industry to `registry.json` at the workspace root. Follow the existing entry format exactly:

```json
{
  "id": "agr-industry-view",
  "title": "Agriculture Industry View",
  "description": "Crop production, precision irrigation, and harvest logistics processes and agent blueprints",
  "path": "business-agents/browser/index.html?industry=AGR",
  "category": "platform",
  "audience": ["ops", "engineering", "internal"],
  "status": "active",
  "tags": ["agriculture", "agr", "precision-ag", "processes", "blueprints"]
}
```

Then add a tile in `index.html` at the workspace root, mirroring the pattern used for other industry entries.

### Common Pitfalls — New Industry

1. **`apqc_code` uniqueness is manually enforced**: There is no UNIQUE constraint on `processes.apqc_code`. The `upsert_process` helper checks existence with a SELECT before inserting. If you skip this check and call INSERT directly, you will create duplicate rows and the `get_process_id()` function will return the first one — silently ignoring your new data.

2. **`action_type` constraint**: Only five values are valid: `monitor`, `analyze`, `generate`, `execute`, `coordinate`. Using `track`, `evaluate`, `report`, or anything else will violate the CHECK constraint and the INSERT will fail silently if foreign keys are off.

3. **`integration` constraint**: Only `read`, `write`, `read_write` (with underscore). NOT `read-write` or `readwrite`.

4. **`authority_level` must be lowercase**: The DB stores `low`, `medium`, `high`. The blueprint viewer and dashboard display code both assume lowercase. Inserting `LOW` or `MEDIUM` will break the badge color rendering.

5. **Industry must exist before processes**: The `get_industry_id()` function raises `ValueError` if the code isn't in the `industries` table. If you're seeding a truly new industry (not just new processes for an existing one), you must insert the industry row first — as shown in `seed_industry()` above.

6. **Process browser does not auto-refresh**: After seeding, open `business-agents/browser/index.html` and hard-refresh (Cmd+Shift+R on macOS) or re-run `generate.py` if it's a pre-generated static file.

---

## 3. Adding a New Dashboard

**Worked example**: `hr.html` — HR manager persona dashboard showing agent recruitment and onboarding activity.

### Step 1: Copy operations.html as the template

```bash
cp "/Users/keith_ai/Documents/Agentic Projects/dashboards/operations.html" \
   "/Users/keith_ai/Documents/Agentic Projects/dashboards/hr.html"
```

`operations.html` is the cleanest base — it has the full nav, KPI strip, agent tiles, and offline fallback pattern.

### Step 2: Update the key components

**Page title and persona name** — change at the top of the file:

```html
<title>HR Manager Dashboard — Business Agents Platform</title>
```

**Nav tab — mark this persona as active**. In the `.nav-personas` section, find and update the active tab:

```html
<!-- Change the active tab to match your persona -->
<a class="nav-tab active" href="hr.html">HR</a>
```

**KPI strip** — `operations.html` uses IDs like `kpi-agents-running`, `kpi-runs-week`, `kpi-avg-outcome`, `kpi-hours-saved`. Keep these IDs — the `renderKPIs()` function writes to them. Change display labels only:

```html
<div class="kpi-card">
  <div class="kpi-label">ONBOARDING IN PROGRESS</div>
  <div class="kpi-value" id="kpi-agents-running">—</div>
</div>
<div class="kpi-card">
  <div class="kpi-label">AGENTS ACTIVE THIS WEEK</div>
  <div class="kpi-value" id="kpi-runs-week">—</div>
</div>
```

**Agent slug references** — find `OPS_SLUGS` in the JavaScript block and replace with the slugs relevant to HR:

```javascript
const OPS_SLUGS = [
    'employee-onboarding',       // replace with your agent slugs
    'agr-crop-yield-forecast-agent',
];
```

**Fallback data** — update `FALLBACK_AGENTS` with HR-relevant placeholder data:

```javascript
const FALLBACK_AGENTS = [
    { slug: 'employee-onboarding', status: 'sandbox',
      title: 'Employee Onboarding Agent', last_run_outcome: 'success' },
];
```

### Step 3: The dark theme CSS variables

All dashboards share the same CSS custom properties. Copy these exactly into any new dashboard's `<style>` block — do not change them:

```css
:root {
  --bg:              #0d1117;
  --card:            #1c2128;
  --card-hover:      #21262d;
  --border:          #30363d;
  --accent:          #58a6ff;
  --text:            #e6edf3;
  --text-secondary:  #8b949e;
  --text-muted:      #6e7681;

  /* Lifecycle stage colors */
  --sandbox:         #39d353;
  --sandbox-dim:     #39d35320;
  --blueprint-col:   #8b949e;
  --blueprint-dim:   #8b949e20;

  /* Authority / urgency colors */
  --low:             #3fb950;
  --low-dim:         #3fb95020;
  --medium:          #d29922;
  --medium-dim:      #d2992220;
  --high:            #f85149;
  --high-dim:        #f8514920;

  --cyan:            #56d364;
}
```

These are defined in `operations.html` lines 10–33 and are consistent across all persona dashboards.

### Step 4: How the offline-first pattern works

The dashboards use a try/catch pattern — not a named `fetchWithFallback` function. The real pattern from `operations.html`:

```javascript
const API = window.location.hostname === 'localhost'
  ? 'http://localhost:8500'
  : '';                          // relative path when deployed to GitHub Pages

async function fetchAll() {
  try {
    const agents = await fetch(`${API}/api/agents`).then(r => {
      if (!r.ok) throw new Error('Server error');
      return r.json();
    });

    // Run parallel fetches for all agent slugs
    const allRuns = {};
    await Promise.all(
      OPS_SLUGS.map(async slug => {
        try {
          const runs = await fetch(`${API}/api/runs/${slug}`).then(r => r.json());
          allRuns[slug] = runs;
        } catch (e) {
          allRuns[slug] = [];
        }
      })
    );

    // Hide offline banner, render live data
    document.getElementById('offline-banner').style.display = 'none';
    renderAgentTiles(agents);
    renderKPIs(agents, allRuns);

  } catch (e) {
    // Server not reachable — show banner, render fallback data
    document.getElementById('offline-banner').style.display = 'block';
    renderFallback();
  }
}
```

The offline banner HTML (place after `<body>`):

```html
<div id="offline-banner">
  &#9888; Server offline &mdash; start with:
  <code>cd dashboards &amp;&amp; python3 server.py</code>
</div>
```

### Step 5: Server registration — nothing required

Static HTML files in `dashboards/` are served automatically. The Flask server is configured as:

```python
# dashboards/server.py, line 62
app = Flask(__name__, static_folder=str(BASE_DIR), static_url_path="")
```

`BASE_DIR` is `dashboards/`. Any `.html` file you place there is immediately accessible at `http://localhost:8500/<filename>.html`. No route registration needed.

The only server change needed is if your dashboard needs to trigger an agent — add to `AGENT_PATHS` and `PERSONA_MAP` as described in Section 1 Step 4.

### Step 6: Add to registry.json and index.html

**registry.json** — add an entry:

```json
{
  "id": "hr-dashboard",
  "title": "HR Manager Dashboard",
  "description": "HR persona dashboard — onboarding agent activity, recruitment pipeline, and compliance status",
  "path": "dashboards/hr.html",
  "category": "dashboards",
  "audience": ["hr", "internal"],
  "status": "active",
  "tags": ["hr", "persona", "onboarding", "dashboard"]
}
```

**index.html** — add a tool card in the dashboards section. Find an existing card like the operations dashboard block and copy its structure.

### Step 7: Validate the HTML

```bash
python3 -c "
import html.parser, pathlib
content = pathlib.Path('/Users/keith_ai/Documents/Agentic Projects/dashboards/hr.html').read_text()
p = html.parser.HTMLParser()
p.feed(content)
print('HTML parsed OK — no hard errors')
"
```

Note: this only catches malformed HTML, not logic errors. Open the file in a browser at `http://localhost:8500/hr.html` to visually verify.

### Common Pitfalls — New Dashboards

1. **`API` variable must handle both localhost and GitHub Pages**: The pattern `window.location.hostname === 'localhost' ? 'http://localhost:8500' : ''` is critical. If you hardcode `http://localhost:8500`, the dashboard will silently fail on GitHub Pages because cross-origin requests are blocked.

2. **KPI element IDs must match what `renderKPIs()` writes to**: If you change IDs like `kpi-agents-running`, the JavaScript will write to a non-existent element and the KPI strip will stay blank. Change the label text only, not the IDs.

3. **Nav tab `active` class**: Only one `nav-tab` should have `class="nav-tab active"`. The nav is hand-coded in each file — there is no shared component. If you add a new persona, you need to add a tab entry to every existing dashboard file too, or users will not see the link when on other dashboards.

4. **`FALLBACK_AGENTS` must be defined before `fetchAll()`**: JavaScript hoisting does not apply to `const`. If the fallback array is defined after the fetch function, and the server is offline, `renderFallback()` will throw a ReferenceError.

5. **The `pilot_runs` table stores runs, not `agent_runs`**: The `/api/runs/<slug>` endpoint queries `pilot_runs` (created by `init_db()` in server.py), not the `agent_runs` table that the agents write to directly. These are separate tables with different schemas.

---

## 4. Adding a New Client Portal

**Worked example**: `AcmeCorp` — a 500-person retail company at Pilot engagement tier.

### Step 1: Create the client directory

```bash
mkdir -p "/Users/keith_ai/Documents/Agentic Projects/clients/acmecorp"
```

### Step 2: Write profile.json

The profile schema is defined by Framework 20 (F20 Client Profile Schema). Here is the full schema modelled on `clients/kimre/profile.json`:

```json
{
  "slug": "acmecorp",
  "name": "Acme Corporation",
  "website": "https://www.acmecorp.example.com",
  "hq": "Chicago, IL",
  "founded": 1988,
  "employees": "501–1000",
  "size_tier": "ENT",
  "industry_code": "RETAIL",
  "industry_name": "Retail",
  "business_model": "MTS",
  "business_model_name": "Make-to-Stock",
  "regulatory_score": 2,
  "integration_tier": "T2",
  "data_readiness_score": 18,
  "engagement_tier": "Pilot",
  "primary_contact": "Jane Doe",
  "primary_contact_title": "VP Operations",
  "key_products": ["Apparel", "Home Goods", "Electronics"],
  "key_markets": ["North America", "Canada"],
  "agent_opportunities": [
    {
      "rank": 1,
      "name": "Inventory Replenishment Agent",
      "closest_blueprint": "retail-inventory-replenishment-agent",
      "process": "Automated Stock Replenishment",
      "value_hrs_week": 14,
      "authority": "LOW",
      "integration_tier": "T2",
      "priority": "pilot"
    },
    {
      "rank": 2,
      "name": "Markdown Optimization Agent",
      "closest_blueprint": "retail-markdown-optimization-agent",
      "process": "Promotional Pricing Decision",
      "value_hrs_week": 8,
      "authority": "MEDIUM",
      "integration_tier": "T2",
      "priority": "next"
    },
    {
      "rank": 3,
      "name": "Customer Churn Agent",
      "closest_blueprint": "retail-customer-churn-agent",
      "process": "Retention Outreach",
      "value_hrs_week": 6,
      "authority": "LOW",
      "integration_tier": "T1",
      "priority": "platform"
    }
  ],
  "pilot_recommendation": {
    "agent": "Inventory Replenishment Agent",
    "rationale": "Closest to existing replenishment blueprint, T2 integration, LOW authority, clear measurable output",
    "timeline_weeks": 8,
    "expected_value_year1_usd": 52000
  },
  "personas": [
    {"role": "VP Operations", "name": "Jane Doe", "focus": "Inventory efficiency, cost reduction, ROI"},
    {"role": "Store Operations Manager", "name": "TBD", "focus": "Replenishment alerts, stockouts, shelf availability"},
    {"role": "Finance Director", "name": "TBD", "focus": "Markdown ROI, budget impact, cost avoidance"},
    {"role": "IT Manager", "name": "TBD", "focus": "Integration complexity, data feeds, security"}
  ]
}
```

**F20 field definitions**:

| Field | Type | Values / Notes |
|---|---|---|
| `slug` | string | Lowercase, no spaces — used as directory name and URL path |
| `size_tier` | string | `SMB`, `MID`, `ENT` |
| `industry_code` | string | Must match `industries.code` in DB (13 valid codes) |
| `business_model` | string | `ETO`, `MTO`, `MTS`, `Distribution`, `Service`, `SaaS` |
| `regulatory_score` | int | 1–5 (1=minimal, 5=heavily regulated) |
| `integration_tier` | string | `T1` (REST/flat file), `T2` (mid-complexity ERP), `T3` (SAP core), `T4` (mainframe) |
| `data_readiness_score` | int | 5–25 (sum of 5 dimensions × 1–5 each) |
| `engagement_tier` | string | `Discovery`, `Pilot`, `Platform` |

### Step 3: Generate the portal HTML

The generator at `clients/portal/generate.py` reads `profile.json` and produces a basic portal `index.html`:

```bash
python3 "/Users/keith_ai/Documents/Agentic Projects/clients/portal/generate.py" --slug acmecorp
```

This produces `clients/acmecorp/index.html`. The generator uses the `ACCENT_MAP` dict in `generate.py` to pick a brand color from `industry_code`:

```python
ACCENT_MAP = {
    "CG":     "#f97316",
    "MFG":    "#6366f1",
    "FS":     "#22c55e",
    "PHARMA": "#a855f7",
    "RETAIL": "#06b6d4",
    "HEALTH": "#ef4444",
}
```

If your industry code is not in `ACCENT_MAP`, it defaults to `#6366f1`. Add it to the map before generating.

For a hand-crafted portal (like Kimre), skip the generator and write `index.html` directly — copy `clients/kimre/index.html` as the starting point and replace all content.

### Step 4: Add the client to seed_clients.py

Open `clients/seed_clients.py` and add a new entry to the `CLIENTS` list:

```python
CLIENTS = [
    # ... existing entries ...
    {
        "slug": "acmecorp",
        "name": "Acme Corporation",
        "industry_code": "RETAIL",
        "size_tier": "ENT",
        "business_model": "MTS",
        "regulatory_score": 2,
        "integration_tier": "T2",
        "data_readiness_score": 18,
        "engagement_tier": "Pilot",
        "pilot_agent_slug": "retail-inventory-replenishment-agent",
        "pilot_year1_value_gbp": 40000,
        "hours_recoverable_wk": 28,
        "annual_value_gbp": 155000,
        "contact_name": "Jane Doe",
        "contact_email": "jane.doe@acmecorp.example.com",
    },
]
```

Run the seeder:

```bash
python3 "/Users/keith_ai/Documents/Agentic Projects/clients/seed_clients.py"
```

The seeder is idempotent — it checks `slug` existence before inserting and skips duplicates. It also reads `clients/acmecorp/profile.json` automatically and stores it in the `profile_json` column.

### Step 5: Verify the client appears in the portfolio

Open `clients/index.html` in a browser. If AcmeCorp does not appear, the portfolio listing is static HTML — open the file and add a card manually following the existing pattern.

Check the DB:

```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('/Users/keith_ai/Documents/Agentic Projects/business-agents/business_agents.db')
rows = conn.execute('SELECT slug, name, engagement_tier, annual_value_gbp FROM clients').fetchall()
for r in rows: print(r)
"
```

### Step 6: Add persona dashboards (F21 framework)

For a full engagement, build persona dashboards following the 5-artifact Framework 21 (Dashboard Specification Framework):

1. **Persona Brief** (`clients/acmecorp/personas.md`) — role, name, JTBD (Jobs-to-be-Done), success metrics
2. **JTBDs** — 3–5 tasks the persona must accomplish each day, wired to agent outputs
3. **Data Contract** — which `/api/` endpoints the dashboard fetches (agents, runs, recommendations, approvals)
4. **Component Palette** — which components from `dashboards/COMPONENTS.md` to use
5. **Quality Gates** — minimum score on the 5-dimension rubric (Framework 19): Narrative, Interactivity, HITL, Data, Persona Fit

Create dashboards at `clients/acmecorp/<persona>.html`. The Kimre set (`clients/kimre/sales.html`, `engineering.html`, `customer-service.html`, `executive.html`, `quality.html`) is the reference implementation for the F21 pattern.

### Common Pitfalls — New Client Portals

1. **`generate.py` expects `agent_opportunities` key but the template references `agents` key**: The generator at line 138 reads `p.get("agents", [])` — but `profile.json` uses `"agent_opportunities"`. If you want the generator to render the opportunity list, you must use the key `agents` in the profile, not `agent_opportunities`. This is an existing inconsistency between the Kimre profile (which uses `agent_opportunities`) and the generator (which reads `agents`). Work around it by either renaming the key or editing the generator.

2. **`pilot_year1_value_gbp` in seed_clients.py vs `expected_value_year1_usd` in profile.json**: The DB schema stores GBP; the profile JSON uses USD. These are different fields for different purposes — the DB value feeds the portfolio dashboard, the profile JSON value feeds the portal generator. Keep them consistent in intent even if the currency differs.

3. **The `clients` DB table has `UNIQUE NOT NULL` on `slug`**: Running `seed_clients.py` twice for the same slug will skip (not error) because of the `existing` set check. But if you manually INSERT via SQL, you will hit the UNIQUE constraint.

4. **`profile_json` column stores the raw file contents as a string**: The seeder reads the file and stores the entire JSON as a text blob. If you update `profile.json` after seeding, you must re-run the seeder — but it will skip because the slug already exists. Add an UPDATE path or delete the row first:
   ```bash
   python3 -c "
   import sqlite3
   conn = sqlite3.connect('.../business_agents.db')
   conn.execute(\"DELETE FROM clients WHERE slug='acmecorp'\")
   conn.commit()
   "
   python3 clients/seed_clients.py
   ```

5. **Portal generator uses `£` symbol hardcoded**: The template at line 83 of `generate.py` renders `£{annual_value_gbp:,}`. If your `profile.json` stores USD amounts in `annual_value_gbp`, the portal will display incorrect currency. The field name is a legacy artifact from an earlier version.

---

## Appendix: DB Schema Quick Reference

```sql
-- Key constraints (enforced by CHECK or application logic)
process_agent_actions.action_type IN ('monitor','analyze','generate','execute','coordinate')
process_systems.integration       IN ('read','write','read_write')
agent_blueprints.trigger_type     IN ('scheduled','event','threshold','manual')
agent_blueprints.authority_level  IN ('low','medium','high')   -- lowercase only
agent_blueprints.lifecycle_stage  IN ('blueprint','scaffolded','sandbox','validated','pilot_ready','production')

-- Useful queries
SELECT code, name FROM industries ORDER BY code;
SELECT slug, title, lifecycle_stage FROM agent_blueprints ORDER BY slug;
SELECT name, apqc_code FROM processes WHERE apqc_code LIKE 'AGR-%';
SELECT slug, name, engagement_tier FROM clients;
```

## Appendix: Agent Output JSON Contract

Every agent `run()` function must return a dict with at minimum these keys for server.py to function correctly:

```json
{
  "run_at":    "2026-03-14T09:15:00.000000",
  "dry_run":   true,
  "authority": "low | medium | high",
  "trigger":   "human-readable trigger description"
}
```

The agent-specific keys (e.g., `prs_created`, `events_dispatched`) are what `_extract_recommendations()` and `_build_summary()` look for. Define these keys in the agent and add matching blocks to both functions in server.py.

## Appendix: Running the Full Stack

```bash
# 1. Start mock APIs (SAP on :3001, MES on :3002)
cd "/Users/keith_ai/Documents/Agentic Projects/sandbox-systems"
./start-all.sh

# 2. Start the dashboard server
python3 "/Users/keith_ai/Documents/Agentic Projects/dashboards/server.py"
# → http://localhost:8500

# 3. Run any agent in dry-run (no APIs needed)
python3 "/Users/keith_ai/Documents/Agentic Projects/pilot-agents/replenishment_agent.py" --dry-run

# 4. Run all CG agents via orchestrator
python3 "/Users/keith_ai/Documents/Agentic Projects/pilot-agents/orchestrator.py" --dry-run

# 5. Query the DB
python3 "/Users/keith_ai/Documents/Agentic Projects/business-agents/query.py" blueprints
python3 "/Users/keith_ai/Documents/Agentic Projects/business-agents/query.py" opportunities CG
```
