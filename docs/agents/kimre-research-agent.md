# Kimre Research Agent
**Slug**: `kimre-research-agent`
**File**: `pilot-agents/kimre/research_agent.py`
**Lifecycle**: sandbox (Kimre pilot — registered in server.py under slug `kimre-research-agent`)
**Last generated**: 2026-03-14 | **Last verified**: 2026-03-14

## Purpose

The Kimre Research Agent is the Kimre Inc.-specific instantiation of the generic research agent. It performs plant intelligence and regulatory lead-scoring against Kimre's core target market: chemical plants in four NAICS sectors — 325181 (Industrial Chemicals), 325311 (Nitrogenous Fertilizers), 331110 (Iron & Steel Mills), and 324110 (Petroleum Refineries).

The key difference from the generic version is that this agent does not attempt any live EPA ECHO API calls. All facilities are drawn exclusively from a curated `DRY_RUN_FACILITIES` list representing 8 real named accounts that Kimre's sales team should be targeting — Mosaic Fertilizer, Chemours Beaumont, Nucor Steel, OCI Nitrogen, Valero Corpus Christi, CF Industries, Gerdau Ameristeel, and Nutrien White Springs. Each facility's score is enriched with a Kimre-specific product recommendation (e.g., "B-GON® Mist Eliminator (CPVC/FRP) for H2SO4 mist control") rather than the generic product-family text used in the generic version.

There is no `--client-profile` or `--naics` or `--state` flag. All parameters are hardcoded. This agent is designed to run as-is for the Kimre sales dashboard without any configuration.

## Inputs

- **DRY_RUN_FACILITIES** (always used — no live API): 8 Kimre target facilities:
  - KF001: Mosaic Fertilizer New Wales (FL, NH3/HNO3, permit renewal_due, 480 inspection days)
  - KF002: Chemours Beaumont (TX, H2SO4, violation=True, 220 inspection days)
  - KF003: Nucor Steel Hertford (NC, HCl pickling, 310 days, no violation)
  - KF004: OCI Nitrogen Wever (IA, Ammonia + Urea, 155 days, no violation)
  - KF005: Valero Corpus Christi (TX, H2SO4 Alkylation, violation=True, 390 days)
  - KF006: CF Industries Donaldsonville (LA, Ammonia/UAN, permit renewal_due, 570 days)
  - KF007: Gerdau Ameristeel Tampa (FL, HCl pickling, violation=True, 200 days)
  - KF008: Nutrien White Springs (FL, Phosphoric Acid, 330 days)
- **KIMRE_PRODUCT_RECS**: 11-key application-to-Kimre-branded-product lookup (H2SO4, HCl, NH3, HNO3, Ammonia, Fertilizer, Phosphoric, Refinery, Pickling, Acid, with fallback to "B-GON® — application review recommended").
- **Flags**:
  - `--dry-run`: Always enabled (`dry_run=args.dry_run or True`). No EPA ECHO call is ever attempted in this version.
  - `--mode {plant-intelligence|regulatory-trigger}`: Selects scoring mode. Default: `plant-intelligence`.

## Outputs

```json
{
  "agent": "kimre-research-agent",
  "run_at": "2026-03-14T09:00:00",
  "dry_run": true,
  "mode": "plant-intelligence",
  "client": "Kimre Inc.",
  "facilities_scanned": 8,
  "leads_identified": 7,
  "items": [
    {
      "facility_id": "KF005",
      "facility_name": "Valero Corpus Christi Refinery",
      "state": "TX",
      "naics": "324110",
      "application": "H2SO4 Alkylation Unit",
      "rec_type": "prospect_lead",
      "lead_score": 5,
      "urgency": "high",
      "signal_type": "violation_flag + long_overdue_inspection",
      "product_recommendation": "B-GON® Mist Eliminator (CPVC/FRP) for H2SO4 mist control",
      "recommended_action": "Schedule application consultation — B-GON® Mist Eliminator (CPVC/FRP) for H2SO4 mist control",
      "violation_flag": true,
      "permit_status": "active",
      "last_inspection_days": 390
    }
  ],
  "recommendations": [
    {
      "rec_type": "prospect_lead",
      "item_id": "KF005",
      "item_label": "Valero Corpus Christi Refinery (TX) — H2SO4 Alkylation Unit",
      "urgency": "high",
      "recommended_action": "Schedule application consultation — B-GON® Mist Eliminator (CPVC/FRP) for H2SO4 mist control",
      "detail": {
        "lead_score": 5,
        "signal_type": "violation_flag + long_overdue_inspection",
        "product_recommendation": "B-GON® Mist Eliminator (CPVC/FRP) for H2SO4 mist control"
      }
    }
  ]
}
```

Unlike the generic version, `recommendations[].detail` includes `product_recommendation`. Only facilities with `lead_score >= 2` appear in `recommendations`. Output written to `pilot-agents/kimre/outputs/kimre_research_agent_run_YYYYMMDD_HHMMSS.json` (relative to cwd).

## Behavior

**plant-intelligence mode:**

1. Load all 8 DRY_RUN_FACILITIES.
2. For each facility, compute lead score (0–7):
   - `violation_flag == True`: +3 (KF002 Chemours, KF005 Valero, KF007 Gerdau)
   - `permit_status == "renewal_due"`: +2 (KF001 Mosaic, KF006 CF Industries)
   - `last_inspection_days > 365`: +2 (KF001 at 480d, KF005 at 390d, KF006 at 570d)
3. Map score to urgency: >= 5 = high, >= 3 = medium, < 3 = low.
4. Build `signal_type` label string.
5. Look up `product_recommendation` from KIMRE_PRODUCT_RECS by application keyword (case-insensitive).
6. Build `recommended_action`: score >= 5 = "Schedule application consultation"; score >= 3 = "Send Kimre capability overview"; < 3 = "Add to Kimre watch list".
7. Mark as lead if score >= 2; increment `leads_identified`.
8. Sort all items by `lead_score` descending.
9. Filter `recommendations` to score >= 2.
10. Write JSON output and print to stdout.

**regulatory-trigger mode:**

1. Same facility loading.
2. Filter to only facilities with `violation_flag == True` OR `permit_status == "renewal_due"` (KF001, KF002, KF005, KF006, KF007 = 5 facilities).
3. All triggered facilities receive urgency = "high".
4. Apply same scoring, product recommendation, and action logic.
5. Sort by lead_score descending; write output.

**Lead score breakdown for dry-run facilities:**

| ID | Facility | Score | Signals |
|---|---|---|---|
| KF001 | Mosaic Fertilizer | 4 | permit_renewal + long_inspection |
| KF002 | Chemours Beaumont | 3 | violation |
| KF003 | Nucor Hertford | 0 | none |
| KF004 | OCI Nitrogen | 0 | none |
| KF005 | Valero Corpus Christi | 5 | violation + long_inspection |
| KF006 | CF Industries | 4 | permit_renewal + long_inspection |
| KF007 | Gerdau Ameristeel | 3 | violation |
| KF008 | Nutrien White Springs | 0 | none |

## HITL Decision Points

All outputs are prospect recommendations — no automated outreach occurs.

- **Score 5, urgency = high** (KF005 Valero): A violation + inspection overdue at a major H2SO4 alkylation unit. Schedule an application consultation immediately. This is Kimre's highest-value signal type.
- **Score 4, urgency = medium** (KF001 Mosaic, KF006 CF Industries): Permit renewals with long-overdue inspections. Send the Kimre capability overview for the relevant application (NH3/HNO3 for Mosaic, Ammonia/UAN for CF Industries).
- **Score 3, urgency = medium** (KF002 Chemours, KF007 Gerdau): Active violations. Send Kimre capability overview and reference case studies from comparable plants.
- **Score 0** (KF003 Nucor Hertford, KF004 OCI Nitrogen, KF008 Nutrien): No current regulatory trigger. Add to watch list and re-score quarterly.
- **regulatory-trigger mode**: Alex Torres should treat all 5 triggered facilities as high-priority outreach within the current quarter.

## Limitations

- **No live EPA ECHO integration**: The Kimre version always uses the hardcoded facility list. The generic version's EPA ECHO fallback path is removed entirely.
- **No `--naics`, `--state`, or `--client-profile` flags**: All configuration is hardcoded. Adding a new target facility requires editing the Python source.
- **Facility list is static and dated**: The 8 facilities represent a curated list as of the agent's creation date. New target accounts, acquisitions, or facility closures require manual updates.
- **Product recommendations are keyword-based**: KIMRE_PRODUCT_RECS uses case-insensitive keyword matching. Ambiguous application strings may fall through to the "B-GON® — application review recommended" fallback.
- **Always dry-run**: `dry_run=args.dry_run or True`. There is no live data path in this variant.
- **No CRM write-back**: Leads are not written to any contact or opportunity table. Output JSON only.
- **No deduplication**: Running twice produces duplicate recommendation entries for the same facilities.

## Example Run

```bash
python3 "pilot-agents/kimre/research_agent.py" --dry-run --mode plant-intelligence
```

Condensed output:

```
[2026-03-14T09:00:00] === kimre-research-agent starting (dry_run=True, mode=plant-intelligence) ===
[2026-03-14T09:00:00] Using Kimre DRY_RUN_FACILITIES (8 facilities)...
[2026-03-14T09:00:00]   KF001 — Mosaic Fertilizer New Wales (FL) — score=4 — urgency=medium
[2026-03-14T09:00:00]   KF002 — Chemours Beaumont Plant (TX) — score=3 — urgency=medium
[2026-03-14T09:00:00]   KF003 — Nucor Steel Hertford (NC) — score=0 — urgency=low
[2026-03-14T09:00:00]   KF004 — OCI Nitrogen Wever (IA) — score=0 — urgency=low
[2026-03-14T09:00:00]   KF005 — Valero Corpus Christi Refinery (TX) — score=5 — urgency=high
[2026-03-14T09:00:00]   KF006 — CF Industries Donaldsonville (LA) — score=4 — urgency=medium
[2026-03-14T09:00:00]   KF007 — Gerdau Ameristeel Tampa (FL) — score=3 — urgency=medium
[2026-03-14T09:00:00]   KF008 — Nutrien White Springs (FL) — score=0 — urgency=low
[2026-03-14T09:00:00] === Run complete ===
[2026-03-14T09:00:00]   Facilities scanned: 8
[2026-03-14T09:00:00]   Leads identified:   5
```

```bash
python3 "pilot-agents/kimre/research_agent.py" --dry-run --mode regulatory-trigger
```

Regulatory-trigger mode returns 5 facilities (KF001, KF002, KF005, KF006, KF007), all at urgency = high.
