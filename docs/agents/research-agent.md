# Research Agent
**Slug**: `research-agent`
**File**: `pilot-agents/research_agent.py`
**Lifecycle**: blueprint (generic — no DB blueprint entry; Kimre-specific version is in `pilot-agents/kimre/`)
**Last generated**: 2026-03-14 | **Last verified**: 2026-03-14

## Purpose

The Research Agent performs automated plant intelligence and regulatory lead-scoring against chemical manufacturing facilities using EPA enforcement and compliance data. Sales and business development teams in industrial equipment markets waste significant time manually searching regulatory databases (EPA ECHO, state agency portals) to identify prospects that are under compliance pressure — violations, permit renewals, or overdue inspections — which are the strongest buying signals for pollution-control equipment.

The agent calls the EPA ECHO REST API (`cwa_rest_services.get_facility_info`) to retrieve facility compliance records filterable by NAICS code and US state. It scores each facility on a 0–7 lead-score scale, surfaces top prospects, and drafts a recommended outreach action. If the live API is unavailable or `--dry-run` is set, the agent falls back to eight hardcoded DRY_RUN_FACILITIES representing realistic chemical plant profiles across TX, LA, OH, MS, FL, KS, AL, and TX.

The generic version is fully functional in dry-run mode and optionally live against EPA ECHO. The Kimre-specific variant (`pilot-agents/kimre/research_agent.py`) replaces the facility list with named Kimre target accounts and adds Kimre-specific product recommendations per application type. There is no `--client-profile` flag in the Kimre version — client context is hardcoded.

## Inputs

- **EPA ECHO API** (live mode only): `https://echo.epa.gov/api/echo/cwa_rest_services.get_facility_info?p_naics=<codes>&output=JSON[&p_st=<state>]`. Returns `Results.Facilities[]` with `FacilityId`, `FacilityName`, `StateName`, `NAICSCode`, `IndustryType`, `ViolationsInLastThreeYears`.
- **DRY_RUN_FACILITIES** (dry-run / fallback): 8 hardcoded facility records with `facility_id`, `name`, `state`, `naics`, `application`, `last_inspection_days`, `violation_flag`, `permit_status`.
- **Flags**:
  - `--dry-run`: Forces use of DRY_RUN_FACILITIES; skips EPA ECHO call. Entry point hardcodes `dry_run=args.dry_run or True`, so live mode is never reached via CLI.
  - `--mode {plant-intelligence|regulatory-trigger}`: Selects scoring mode. Default: `plant-intelligence`.
  - `--naics <codes>`: Comma-separated NAICS codes for EPA ECHO filter (e.g. `325181,325311`). Default: `325181`.
  - `--state <XX>`: Two-letter US state code for geographic filter. Optional.
  - `--client-profile <path>`: Optional path to client profile JSON. Loads `name` for output metadata only; does not change facility data.

## Outputs

```json
{
  "agent": "research-agent",
  "run_at": "2026-03-14T09:00:00",
  "dry_run": true,
  "mode": "plant-intelligence",
  "client": "generic",
  "facilities_scanned": 8,
  "leads_identified": 6,
  "items": [
    {
      "facility_id": "F001",
      "facility_name": "Clearwater Chemical Works",
      "state": "TX",
      "naics": "325181",
      "application": "Sulfuric Acid Processing",
      "rec_type": "prospect_lead",
      "lead_score": 5,
      "urgency": "high",
      "signal_type": "violation_flag + long_overdue_inspection",
      "recommended_action": "Schedule application consultation — mist elimination for Sulfuric Acid Processing",
      "violation_flag": true,
      "permit_status": "active",
      "last_inspection_days": 280
    }
  ],
  "recommendations": [
    {
      "rec_type": "prospect_lead",
      "item_id": "F001",
      "item_label": "Clearwater Chemical Works (TX) — Sulfuric Acid Processing",
      "urgency": "high",
      "recommended_action": "Schedule application consultation — mist elimination for Sulfuric Acid Processing",
      "detail": {
        "lead_score": 5,
        "signal_type": "violation_flag + long_overdue_inspection"
      }
    }
  ]
}
```

Only facilities with `lead_score >= 2` appear in `recommendations`. `items` contains all scored facilities, sorted by `lead_score` descending. Output is also written to `pilot-agents/outputs/research_agent_run_YYYYMMDD_HHMMSS.json`.

## Behavior

**plant-intelligence mode:**

1. Load DRY_RUN_FACILITIES (8 facilities). In non-dry-run mode, attempt EPA ECHO API call; fall back to DRY_RUN_FACILITIES on failure.
2. For each facility, compute lead score (0–7):
   - `violation_flag == True`: +3 points
   - `permit_status == "renewal_due"`: +2 points
   - `last_inspection_days > 365`: +2 points
3. Map score to urgency: >= 5 = high, >= 3 = medium, < 3 = low.
4. Build `signal_type` string concatenating active signal labels (e.g., `"violation_flag + long_overdue_inspection"`).
5. Build recommended action based on score: >= 5 = schedule application consultation; >= 3 = send capability overview; < 3 = add to watch list.
6. Mark facility as a lead if `score >= 2`; increment `leads_identified`.
7. Sort all items by `lead_score` descending.
8. Build `recommendations` list filtered to `lead_score >= 2`.
9. Write JSON output and print to stdout.

**regulatory-trigger mode:**

1. Same facility loading as above.
2. Filter to only facilities where `violation_flag == True` OR `permit_status == "renewal_due"`. Facilities with neither signal are excluded entirely.
3. All triggered facilities receive urgency = "high" regardless of score.
4. Apply same scoring and action-building logic.
5. Sort by lead_score descending; write output.

## HITL Decision Points

All outputs are recommendations — no automated outreach occurs. Human review workflow:

- **Score >= 5, urgency = high**: Sales engineer should schedule an application consultation call within 1–2 business days. These facilities have active violations AND long-overdue inspections, indicating acute compliance pressure.
- **Score 3–4, urgency = medium**: Send a product capability overview or case study within the week.
- **Score 2, urgency = low**: Add to a watch list for monitoring. Revisit in 30–60 days.
- **regulatory-trigger mode results**: All items are urgency = high by definition; prioritize accordingly.
- No emails or CRM entries are created automatically.

## Limitations

- **Always dry-run via CLI**: Entry point hardcodes `dry_run=args.dry_run or True`. The EPA ECHO API call is only reachable by importing `run()` directly with `dry_run=False`.
- **EPA ECHO fallback is silent**: If the API returns an unexpected JSON shape, the agent silently falls back to DRY_RUN_FACILITIES without raising an error.
- **Live EPA ECHO data gaps**: Live facilities from ECHO receive `last_inspection_days=180` and `permit_status="active"` as hardcoded defaults because ECHO does not expose those fields in the basic facility info endpoint.
- **No CRM write-back**: Leads are not persisted to any database. The output JSON is written to `outputs/` only.
- **`--client-profile` is metadata-only**: Loading a profile JSON changes only the `client` field in output. It does not filter facilities by geography, NAICS, or application type.
- **No deduplication**: Repeated runs against the same EPA data will produce duplicate lead records.
- **NAICS scope is narrow**: The default `--naics 325181` (Industrial Chemicals) targets acid plants; `325311` adds nitrogen fertilizers; `331110` adds steel pickling. Other chemical processes require explicit NAICS expansion.

## Example Run

```bash
python3 "pilot-agents/research_agent.py" --dry-run --mode plant-intelligence
```

Condensed output:

```
[2026-03-14T09:00:00] === research-agent starting (dry_run=True, mode=plant-intelligence) ===
[2026-03-14T09:00:00] Using DRY_RUN_FACILITIES (simulated data)
[2026-03-14T09:00:00] Scanning 8 facilities in plant-intelligence mode...
[2026-03-14T09:00:00]   F001 — Clearwater Chemical Works (TX) — score=5 — urgency=high
[2026-03-14T09:00:00]   F002 — Highpoint Fertilizer (LA) — score=2 — urgency=low
[2026-03-14T09:00:00]   F003 — Midwest Steel Pickling (OH) — score=3 — urgency=medium
[2026-03-14T09:00:00]   F004 — Delta Acid Plant (MS) — score=4 — urgency=medium
[2026-03-14T09:00:00]   F005 — Coastal Agri Corp (FL) — score=0 — urgency=low
[2026-03-14T09:00:00]   F006 — Great Plains Metals (KS) — score=3 — urgency=medium
[2026-03-14T09:00:00]   F007 — Southern Chem Partners (AL) — score=0 — urgency=low
[2026-03-14T09:00:00]   F008 — Prairie Phosphate Co (TX) — score=2 — urgency=low
[2026-03-14T09:00:00] === Run complete ===
[2026-03-14T09:00:00]   Facilities scanned: 8
[2026-03-14T09:00:00]   Leads identified:   6
[2026-03-14T09:00:00]   Output: outputs/research_agent_run_20260314_090000.json
```

```bash
python3 "pilot-agents/research_agent.py" --dry-run --mode regulatory-trigger
```

In regulatory-trigger mode, only F001 (violation), F003 (violation), F004 (permit renewal), and F006 (violation) appear in output — all at urgency = high.
