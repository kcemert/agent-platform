# Kimre Quality Compliance Agent
**Slug**: `kimre-quality-compliance-agent`
**File**: `pilot-agents/kimre/quality_compliance_agent.py`
**Lifecycle**: sandbox
**Last generated**: 2026-03-14 | **Last verified**: 2026-03-14

## Purpose

The Kimre Quality Compliance Agent performs automated pre-shipment quality checks on active production orders for Kimre Inc. It solves a manual audit problem: before each order ships, Pat Chen (Quality Engineer) must verify that the chosen construction material is chemically compatible with the customer's service environment, that material batch certificates have not expired, and that fabricated dimensions meet the specified tolerances. With 6–12 active orders at any time across multiple product families, this can take several hours per week and is prone to oversights.

The agent fits into Kimre's production-to-shipment workflow. It runs against all active orders, applies a chemical resistance compatibility matrix (EPA-aligned), checks certificate expiry windows (critical: ≤14 days, warning: ≤30 days), and verifies measured dimensions against nominal tolerances. It produces a structured checklist for each order and flags issues with urgency levels for Pat's review. All flagged orders require human action before shipment proceeds.

## Inputs

- **`DRY_RUN_ORDERS`**: Hardcoded list of 6 active production orders. Each entry includes `order_id`, `customer`, `product`, `application`, `application_chemical`, `material`, `cert_batch`, `cert_expiry`, `due_date`, and `dims` (`dia_nominal_in`, `dia_actual_in`, `tolerance_in`).
- **`--dry-run` flag**: This agent is always dry-run only (`dry_run_mode = "--dry-run" in sys.argv or True`). No live ERP, QMS, or metrology system is connected.
- **`REFERENCE_DATE`**: Hardcoded to `date(2026, 3, 13)` for deterministic cert-expiry calculations in demo context.
- **`COMPATIBILITY` matrix**: Hardcoded dict mapping 5 materials (Polypropylene, CPVC, FRP, Stainless_316L, PVC) to their lists of compatible chemicals.
- **`CERT_CRITICAL_DAYS = 14`**, **`CERT_HIGH_DAYS = 30`**: Expiry thresholds, hardcoded.
- **No environment variables required**.

## Outputs

Writes `pilot-agents/kimre/outputs/quality_compliance_agent_run_{YYYYMMDD_HHMMSS}.json` and prints the full JSON to stdout.

```json
{
  "run_at": "2026-03-14T08:00:00",
  "agent": "kimre-quality-compliance-agent",
  "dry_run": true,
  "reference_date": "2026-03-13",
  "orders_checked": 6,
  "compliant": 4,
  "flagged": 2,
  "items": [
    {
      "order_id": "KIM-049",
      "customer": "Atlas Fertilizer Corp",
      "product": "B-GON® ME-72-SS",
      "application_chemical": "NH3",
      "material": "Stainless_316L",
      "cert_batch": "SS-BATCH-2026-02",
      "cert_expiry": "2026-03-20",
      "compatibility": true,
      "cert_status": "expiring_critical",
      "cert_days_remaining": 7,
      "dimensional_check": "pass",
      "dimensional_detail": "72.00\" nominal ± 0.500\" — actual 72.00\" (deviation 0.000\") — PASS",
      "qc_items": [
        "Dimensional check: 72\" nominal ± 0.5\" — actual 72.0\" ✓",
        "Material compatibility: Stainless_316L in NH3 service ✓",
        "Certificate batch SS-BATCH-2026-02 — expiry 2026-03-20 ⚠ EXPIRING_CRITICAL",
        "Customer: Atlas Fertilizer Corp — Product: B-GON® ME-72-SS",
        "Ship due: 2026-03-25"
      ],
      "flags": [
        "CERT EXPIRY CRITICAL: SS-BATCH-2026-02 expires 2026-03-20 (7 days) — order ships 2026-03-25 — renew cert or source alternative batch immediately"
      ],
      "urgency": "critical",
      "rec_type": "compliance_flag"
    },
    {
      "order_id": "KIM-047",
      "customer": "Mosaic Steel Works",
      "product": "B-GON® ME-24-CPVC",
      "application_chemical": "HCl",
      "material": "CPVC",
      "cert_batch": "CPVC-2024-05",
      "cert_expiry": "2026-06-30",
      "compatibility": true,
      "cert_status": "ok",
      "cert_days_remaining": 109,
      "dimensional_check": "fail",
      "dimensional_detail": "24.00\" nominal ± 0.250\" — actual 23.70\" (deviation 0.300\") — FAIL: undersized by 0.050\"",
      "flags": [
        "DIMENSIONAL NON-CONFORMANCE: 24.00\" nominal ± 0.250\" — actual 23.70\" (deviation 0.300\") — FAIL: undersized by 0.050\""
      ],
      "urgency": "high",
      "rec_type": "compliance_flag"
    },
    {
      "order_id": "KIM-052",
      "customer": "Gulf Fertilizers Co.",
      "product": "B-GON® ME-48-PP",
      "application_chemical": "HNO3",
      "material": "Polypropylene",
      "cert_batch": "PP-2024-15",
      "cert_expiry": "2026-09-01",
      "compatibility": true,
      "cert_status": "ok",
      "cert_days_remaining": 172,
      "dimensional_check": "pass",
      "dimensional_detail": "48.00\" nominal ± 0.500\" — actual 47.80\" (deviation 0.200\") — PASS",
      "flags": [],
      "urgency": "low",
      "rec_type": "qc_ok"
    }
  ]
}
```

## Behavior

1. **Iterate active orders**: Loops over all 6 entries in `DRY_RUN_ORDERS`.
2. **Compatibility check**: Looks up `material` in the `COMPATIBILITY` dict and checks whether `application_chemical` appears in the compatible chemicals list. Returns `True` (compatible) or `False` (incompatible). A `False` result immediately generates a `MATERIAL INCOMPATIBILITY` flag.
3. **Certificate expiry check**: Parses `cert_expiry` as an ISO date. Computes `days_remaining = cert_expiry - REFERENCE_DATE`. Maps to one of four statuses: `expired` (< 0 days), `expiring_critical` (≤ 14 days), `expiring_soon` (≤ 30 days), `ok`. Generates a flag string for any non-`ok` status.
4. **Dimensional conformance check**: Computes `deviation = abs(actual - nominal)`. Passes if `deviation <= tolerance`. On failure, labels direction as `oversized` or `undersized` and calculates the amount of exceedance (`deviation - tolerance`). Returns a detailed string including nominal, tolerance, actual, deviation, and pass/fail verdict.
5. **Build QC checklist**: Generates a 5-item plain-English checklist for each order summarising dimensional, compatibility, cert, customer, and ship-date information.
6. **Determine urgency**: `expired` cert or incompatible material → `critical`; `expiring_critical` cert → `critical`; `expiring_soon` cert or dimensional fail → `high`; all clear → `low`.
7. **Accumulate results**: Appends a `compliance_flag` record (if flags) or `qc_ok` record to `items`.
8. **Write output**: Saves JSON to `outputs/`, prints to stdout. Reports `compliant` and `flagged` counts.

## HITL Decision Points

- **All flagged orders require human action before shipment**: The agent produces flags only; it cannot block a shipment or update the ERP order status.
- **`urgency: critical` — CERT EXPIRY CRITICAL**: Pat must immediately source an alternative certified batch or obtain an emergency cert renewal. The order ships within 7–14 days of the cert expiry date in the flagged scenario (KIM-049: cert expires 2026-03-20, ships 2026-03-25).
- **`urgency: high` — DIMENSIONAL NON-CONFORMANCE**: Pat must rework or scrap the affected unit (KIM-047: undersized by 0.050"). Decision on rework vs. replacement requires engineering sign-off.
- **`urgency: critical` — MATERIAL INCOMPATIBILITY**: Entire material selection must be reviewed; the order cannot ship until a compatible material is confirmed. (No incompatibility exists in the current 6-order dry-run dataset, but the logic is exercised by the code.)
- **`rec_type: qc_ok`**: Orders with no flags are cleared for shipment by the agent's assessment; Pat still performs a final sign-off, but no corrective action is required.

## Limitations

- **Always dry-run**: The entry point forces `dry_run=True` regardless of the `--dry-run` flag. No live QMS, ERP, or metrology system is connected.
- **Hardcoded 6-order dataset**: The active order list is embedded in code. No integration with Kimre's production scheduling or ERP system.
- **Hardcoded reference date**: `REFERENCE_DATE = date(2026, 3, 13)` is fixed for demo consistency. In production, this should use `date.today()`.
- **Compatibility matrix is curated, not authoritative**: The `COMPATIBILITY` dict covers 5 materials and ~25 chemical combinations. Exotic chemicals, concentration-dependent compatibility, or temperature-dependent ratings are not modelled.
- **Single-dimension check**: Only vessel diameter is validated. Wall thickness, mesh density, weld quality, and other mechanical attributes are not checked.
- **No rework tracking**: The agent flags a non-conformance but has no mechanism to track whether rework was completed, re-inspected, and cleared.
- **No certificate database integration**: The agent checks the `cert_expiry` field in the order record. If this field is wrong (e.g., not updated after a cert was renewed), the check produces incorrect results.

## Example Run

```bash
python3 pilot-agents/kimre/quality_compliance_agent.py --dry-run
```

Condensed output (3 of 6 orders shown):

```
[2026-03-14T08:00:00] === kimre-quality-compliance-agent starting (dry_run=True) ===
[2026-03-14T08:00:00] Reference date: 2026-03-13
[2026-03-14T08:00:00] Checking 6 active orders for compliance...
[2026-03-14T08:00:00]   Checking KIM-052 — Gulf Fertilizers Co. (Polypropylene / HNO3)
[2026-03-14T08:00:00]     Compliant — all checks passed
[2026-03-14T08:00:00]   Checking KIM-049 — Atlas Fertilizer Corp (Stainless_316L / NH3)
[2026-03-14T08:00:00]     FLAGGED (critical): 1 issue(s)
[2026-03-14T08:00:00]   Checking KIM-048 — Southern Power Generation (FRP / H2SO4)
[2026-03-14T08:00:00]     Compliant — all checks passed
[2026-03-14T08:00:00]   Checking KIM-047 — Mosaic Steel Works (CPVC / HCl)
[2026-03-14T08:00:00]     FLAGGED (high): 1 issue(s)
[2026-03-14T08:00:00] === Run complete ===
[2026-03-14T08:00:00]   Orders checked: 6
[2026-03-14T08:00:00]   Compliant:      4
[2026-03-14T08:00:00]   Flagged:        2
[2026-03-14T08:00:00]   Output written: outputs/quality_compliance_agent_run_20260314_080000.json
```
