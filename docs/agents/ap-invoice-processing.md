# AP Invoice Processing Agent
**Slug**: `ap-invoice-processing`
**File**: `pilot-agents/ap-invoice-processing.py`
**Lifecycle**: sandbox (cross-industry pilot — registered in DB, wired into server.py and orchestrator.py)
**Last generated**: 2026-03-14 | **Last verified**: 2026-03-14

## Purpose

The AP Invoice Processing Agent automates the triage and classification of open accounts payable invoices. In a typical finance team, AP clerks manually review every open purchase order, check amounts against approval thresholds, identify overdue items, and flag exceptions — a high-volume, repetitive task that scales linearly with invoice count and introduces risk of missed overdue items or unauthorized high-value approvals.

The agent fetches open invoices from the Mock SAP API (port 3001) and classifies each into one of three outcomes: `auto_approved` (normal parameters, safe to process), `approval_required` (high-value or overdue), or `anomaly` (amount variance vs. PO). Auto-approved items are ready for payment processing without further review. Flagged items surface in the dashboard HITL approval queue for finance team action. The agent also detects a hardcoded anomaly invoice (INV-2026-0135, representing a PO amount-variance scenario) to demonstrate exception handling.

DRY_RUN_INVOICES are drawn from an Italian food wholesale context (Bonfiglio SpA, Mutti SRL, De Cecco, San Pellegrino, Salinera Adriatica, Almeria Foods, Venchi, Wilkin & Sons) to illustrate a diverse supplier portfolio. The reference date is hardcoded to 2026-03-13 in dry-run mode; live mode uses `date.today()`.

## Inputs

- **Mock SAP API** (live mode): `GET http://localhost:3001/api/purchase-orders?status=open` — returns a list of open invoice/PO objects. The agent accepts list responses or dict responses with keys `items`, `invoices`, `purchase_orders`, `data`, or `results`.
- **DRY_RUN_INVOICES** (dry-run / fallback): 8 hardcoded invoice objects, each with:
  `invoice_id`, `po_number`, `vendor`, `description`, `amount` (GBP integer), `currency`, `due_date` (ISO date), `received_date`, `status`, `payment_terms`
- **ANOMALY_INVOICE_IDS**: Hardcoded set `{"INV-2026-0135"}` — invoices in this set are flagged as anomalies (amount variance) in dry-run mode.
- **HIGH_VALUE_THRESHOLD**: `50000` GBP (hardcoded constant).
- **REFERENCE_DATE**: `date(2026, 3, 13)` in dry-run mode; `date.today()` in live mode.
- **Flags**:
  - `--dry-run`: Uses DRY_RUN_INVOICES and REFERENCE_DATE; skips SAP API call. Detected via `"--dry-run" in sys.argv`.

## Outputs

```json
{
  "run_at": "2026-03-14T09:00:00.000000",
  "agent": "ap-invoice-processing",
  "dry_run": true,
  "reference_date": "2026-03-13",
  "invoices_processed": 8,
  "auto_approved": 4,
  "approval_required": 3,
  "anomalies_flagged": 1,
  "items": [
    {
      "invoice_id": "INV-2026-0142",
      "po_number": "PO-2026-0201",
      "vendor": "Bonfiglio SpA",
      "description": "Olive Oil Extra Virgin — 500 units",
      "amount": 18500,
      "currency": "GBP",
      "due_date": "2026-03-10",
      "received_date": "2026-02-25",
      "payment_terms": "Net 30",
      "status": "approval_required",
      "rec_type": "invoice_approval",
      "reason": "OVERDUE by 3 day(s) (due 2026-03-10). Immediate payment review required.",
      "urgency": "high",
      "overdue_days": 3,
      "high_value": false,
      "anomaly": false,
      "approval_required": true
    },
    {
      "invoice_id": "INV-2026-0140",
      "po_number": "PO-2026-0197",
      "vendor": "De Cecco",
      "description": "Pasta — mixed SKUs 3000 units",
      "amount": 14800,
      "currency": "GBP",
      "due_date": "2026-03-20",
      "received_date": "2026-03-01",
      "payment_terms": "Net 30",
      "status": "auto_approved",
      "rec_type": "invoice_approval",
      "reason": "Invoice within normal parameters — £14,800, due 2026-03-20. Auto-approved for payment processing.",
      "urgency": "low",
      "overdue_days": 0,
      "high_value": false,
      "anomaly": false,
      "approval_required": false
    }
  ]
}
```

Output is written to `pilot-agents/outputs/ap_invoice_processing_YYYYMMDD_HHMMSS.json` via `agent_runner.write_output`. Run is logged to `pilot_runs` table via `agent_runner.log_to_db`.

## Behavior

1. **Fetch invoices**: In dry-run mode, use DRY_RUN_INVOICES (8 items). In live mode, call `GET /api/purchase-orders?status=open`. If SAP API is unavailable or returns an unexpected shape, fall back to DRY_RUN_INVOICES.
2. **Set reference date**: `REFERENCE_DATE = date(2026, 3, 13)` in dry-run; `date.today()` in live.
3. **Process each invoice** through three independent classification checks (applied in priority order):
   - **Anomaly check**: If `invoice_id in ANOMALY_INVOICE_IDS` (dry-run) → status = "anomaly", rec_type = "invoice_anomaly", urgency = "high". Reason: amount variance vs. PO, manual verification required.
   - **High-value AND overdue**: `amount > £50,000 AND overdue_days > 0` → status = "approval_required", urgency = "critical". Senior Finance approval required.
   - **High-value only**: `amount > £50,000` → status = "approval_required", urgency = "high".
   - **Overdue only**: `overdue_days > 0` (i.e., `today > due_date`) → status = "approval_required", urgency = "high". Note: the code flags any invoice where today exceeds due_date by any amount — there is no grace period.
   - **Normal**: All other invoices → status = "auto_approved", urgency = "low".
4. **Accumulate counters**: `auto_approved`, `approval_required`, `anomalies_flagged`.
5. **Build output JSON** with all items and summary counters.
6. **Write output file** via `agent_runner.write_output`.
7. **Log to DB** via `agent_runner.log_to_db` with outcome = "success" (always), tools used = `["GET /api/purchase-orders"]`, and a learnings string summarizing counts.
8. **Print flagged items** to stdout in a summary table after the main output.

## HITL Decision Points

- **`auto_approved` items**: No human action required. Safe for payment processing queue.
- **`approval_required` items** (urgency = high): Finance team must review in the HITL approval queue before releasing payment. Includes:
  - Overdue invoices (any overdue days > 0)
  - High-value invoices (> £50K)
  - Combined high-value + overdue (urgency escalates to "critical")
- **`anomaly` items** (urgency = high): Require manual PO-to-invoice reconciliation before any payment action. The reason string specifies "amount variance detected — may not match PO within 10% tolerance."
- **"critical" urgency** (high-value AND overdue): Indicates a significant financial and relationship risk. Should be escalated to senior Finance approval same day.
- The dashboard action-queue displays all `approval_required` and `anomaly` items as HITL action cards.

## Limitations

- **Always dry-run via CLI**: Entry point detects `"--dry-run" in sys.argv` directly (no argparse), so the flag must be the literal string `--dry-run` as a command-line argument.
- **SAP dependency**: Live mode requires Mock SAP server at `localhost:3001`. If unavailable, agent falls back to DRY_RUN_INVOICES silently.
- **Overdue threshold is 0 days, not 3**: The docstring says ">3 days overdue = flag" but the code flags any invoice where `today > due_date` (overdue_days > 0). There is no grace period implemented.
- **ANOMALY_INVOICE_IDS is hardcoded**: The anomaly detection set `{"INV-2026-0135"}` is a static demo set. Live mode does not perform real amount-variance checking against PO records.
- **No PO matching**: The agent does not fetch PO records to validate invoice amounts. Anomaly detection is demo-only in dry-run.
- **DB path is hardcoded**: `DB_PATH` points to an absolute path on the original developer's machine.
- **GBP only**: The `HIGH_VALUE_THRESHOLD` is in GBP. Multi-currency invoices are evaluated against the threshold using their raw `amount` value without currency conversion.
- **No output `recommendations` array**: Unlike the generic agents, `ap-invoice-processing` does not produce a `recommendations[]` list. Classification outcomes are embedded in `items[].status` and `items[].rec_type`.

## Example Run

```bash
python3 "pilot-agents/ap-invoice-processing.py" --dry-run
```

Condensed output:

```
[2026-03-14T09:00:00] === AP Invoice Processing Agent starting (dry_run=True) ===
[2026-03-14T09:00:00] Reference date: 2026-03-13
[2026-03-14T09:00:00] DRY-RUN: Using simulated invoice data
[2026-03-14T09:00:00] Invoices fetched: 8
[2026-03-14T09:00:00]   INV-2026-0142: £18,500 | due=2026-03-10 | overdue=3d | high_value=False | anomaly=False
[2026-03-14T09:00:00]   INV-2026-0141: £9,200 | due=2026-03-15 | overdue=0d | high_value=False | anomaly=False
[2026-03-14T09:00:00]   INV-2026-0140: £14,800 | due=2026-03-20 | overdue=0d | high_value=False | anomaly=False
[2026-03-14T09:00:00]   INV-2026-0139: £6,500 | due=2026-03-18 | overdue=0d | high_value=False | anomaly=False
[2026-03-14T09:00:00]   INV-2026-0138: £11,200 | due=2026-03-25 | overdue=0d | high_value=False | anomaly=False
[2026-03-14T09:00:00]   INV-2026-0137: £68,500 | due=2026-03-08 | overdue=5d | high_value=True | anomaly=False
[2026-03-14T09:00:00]   INV-2026-0136: £24,800 | due=2026-03-05 | overdue=8d | high_value=False | anomaly=False
[2026-03-14T09:00:00]   INV-2026-0135: £31,200 | due=2026-03-12 | overdue=1d | high_value=False | anomaly=True
[2026-03-14T09:00:00] Processed 8 invoices — auto_approved=4 | approval_required=3 | anomalies=1
[2026-03-14T09:00:00] === AP Invoice Processing Agent complete (0.1s) ===

*** INVOICES REQUIRING ATTENTION ***
  INV-2026-0142 — Bonfiglio SpA — £18,500 [HIGH]: OVERDUE by 3 day(s) (due 2026-03-10)...
  INV-2026-0137 — Almeria Foods — £68,500 [CRITICAL]: HIGH VALUE AND OVERDUE by 5 day(s)...
  INV-2026-0136 — Venchi — £24,800 [HIGH]: OVERDUE by 8 day(s) (due 2026-03-05)...
  INV-2026-0135 — Wilkin & Sons — £31,200 [HIGH]: Amount variance detected...
```
