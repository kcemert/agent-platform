# Kimre Retrofit Reorder Agent
**Slug**: `kimre-retrofit-reorder-agent`
**File**: `pilot-agents/kimre/retrofit_reorder_agent.py`
**Lifecycle**: sandbox
**Last generated**: 2026-03-14 | **Last verified**: 2026-03-14

## Purpose

The Kimre Retrofit Reorder Agent automates reorder opportunity identification and outreach drafting across Kimre's installed customer base. Kimre sells long-life industrial separation equipment (mist eliminators, coalescers, fiber bed filters) with typical replacement cycles of 12–36 months. Without the agent, Alex Torres (Sales/Applications Engineer) must manually track each account's last purchase date, calculate elapsed time against expected intervals, and draft personalised outreach messages from memory — an account management task that is easily deprioritised during busy quoting periods, resulting in missed retrofit and replacement revenue.

The agent fits into Kimre's proactive account management workflow. On each run it scans 15 customer accounts, computes months elapsed since the last order, compares against the account's typical reorder interval, and flags accounts that are within 2 months of their expected reorder date (proactive window) or already overdue. For each candidate it drafts a personalised outreach message from Alex, referencing the specific product, elapsed time, and an offer to review or requote. The output feeds the Kimre sales dashboard for Alex's review and one-click send.

## Inputs

- **`DRY_RUN_CUSTOMERS`**: Hardcoded list of 15 customer accounts. Each entry includes `account`, `contact`, `email`, `product_purchased`, `last_order_date`, `typical_reorder_interval_months`, and `order_value_typical` (GBP).
- **`REFERENCE_DATE`**: Hardcoded to `date(2026, 3, 13)` for deterministic elapsed-time calculations.
- **`PROACTIVE_WINDOW_MONTHS = 2`**: Accounts are flagged when `months_since >= (interval - 2)`, i.e., within 2 months of their expected reorder date.
- **`DAYS_PER_MONTH = 30.44`**: Average days per month used for elapsed-time calculation.
- **`--dry-run` flag**: Always dry-run only (`dry_run_mode = "--dry-run" in sys.argv or True`). No live CRM or ERP integration.
- **No environment variables required**.

## Outputs

Writes `pilot-agents/kimre/outputs/retrofit_reorder_agent_run_{YYYYMMDD_HHMMSS}.json` and prints the full JSON to stdout.

```json
{
  "run_at": "2026-03-14T09:00:00",
  "agent": "kimre-retrofit-reorder-agent",
  "dry_run": true,
  "reference_date": "2026-03-13",
  "accounts_checked": 15,
  "reorder_candidates": 7,
  "items": [
    {
      "account": "Atlas Fertilizer Corp",
      "contact": "Robert Kim",
      "email": "r.kim@atlasfert.com",
      "product_purchased": "B-GON® ME-72-SS",
      "last_order_date": "2024-08-20",
      "months_since": 18.7,
      "typical_interval": 18,
      "overdue_months": 0.7,
      "order_value_typical_gbp": 195000,
      "outreach_draft": "Hi Robert Kim,\n\nI hope you're doing well! I wanted to reach out as it's been approximately 19 months since your last order of B-GON® ME-72-SS.\n\nBased on your typical replacement schedule, you may be approaching the time for a refresh or inspection of your unit. Our B-GON® ME-72-SS units typically perform optimally for 18 months under normal operating conditions.\n\nWould you like us to conduct a free inspection review, or discuss your current unit's performance? We're also happy to provide an updated quote if you're planning for the next maintenance cycle.\n\nBest regards,\nAlex Torres\nSales / Applications Engineer — Kimre Inc.",
      "urgency": "medium",
      "rec_type": "reorder_outreach"
    },
    {
      "account": "Midwest Fertilizers",
      "contact": "Tom Johnson",
      "email": "t.johnson@midwestfert.com",
      "product_purchased": "B-GON® ME-36-PP",
      "last_order_date": "2024-04-01",
      "months_since": 23.4,
      "typical_interval": 18,
      "overdue_months": 5.4,
      "order_value_typical_gbp": 45000,
      "outreach_draft": "Hi Tom Johnson,\n\nI hope you're doing well! I wanted to reach out as it's been approximately 23 months since your last order of B-GON® ME-36-PP...",
      "urgency": "high",
      "rec_type": "reorder_outreach"
    },
    {
      "account": "Gulf Chemicals Trading",
      "contact": "Sarah Ahmed",
      "email": "s.ahmed@gulfchem.com",
      "product_purchased": "KON-TANE® KT-PP-2IN",
      "last_order_date": "2025-03-20",
      "months_since": 11.8,
      "typical_interval": 12,
      "overdue_months": -0.2,
      "order_value_typical_gbp": 34000,
      "outreach_draft": "Hi Sarah Ahmed,\n\nI hope you're doing well! I wanted to reach out as it's been approximately 12 months since your last order of KON-TANE® KT-PP-2IN...",
      "urgency": "medium",
      "rec_type": "reorder_outreach"
    }
  ]
}
```

## Behavior

1. **Iterate customer accounts**: Loops over all 15 entries in `DRY_RUN_CUSTOMERS`.
2. **Calculate months elapsed**: Computes `days_elapsed = REFERENCE_DATE - last_order_date`. Converts to months using `DAYS_PER_MONTH = 30.44`. Rounds to 1 decimal place.
3. **Calculate overdue months**: `overdue_months = months_since - typical_interval`. Negative values indicate the account is before its reorder date (proactive window); positive values indicate overdue.
4. **Apply candidacy threshold**: Flags an account if `overdue_months >= -PROACTIVE_WINDOW_MONTHS` (i.e., within 2 months of expected reorder date, or already past it). Accounts with `overdue_months < -2.0` are skipped.
5. **Assign urgency**: `overdue_months >= 2.0` → `"high"` (significantly overdue, high risk of competitor capture); `0.0 <= overdue_months < 2.0` → `"medium"` (at or just past reorder date); `overdue_months < 0.0` (proactive window) → `"low"`.
6. **Draft outreach message**: Generates a personalised email from Alex Torres. The message references the contact by name, names the specific product, states the elapsed months (rounded to nearest whole number), recalls the typical interval, and offers three options: free inspection review, performance discussion, or updated quote.
7. **Accumulate candidates**: Appends qualifying accounts to the `items` list as `reorder_outreach` records.
8. **Write output**: Saves JSON to `outputs/`, prints to stdout. Reports `accounts_checked` and `reorder_candidates` counts.

## HITL Decision Points

- **All outreach drafts require Alex's review before sending**: The agent generates draft messages only. Alex reviews each draft in the Kimre sales dashboard, edits as needed, and sends.
- **`urgency: high` (overdue ≥ 2 months)**: These accounts are significantly past their expected reorder cycle — highest risk of the customer having already sourced from a competitor, or of operating degraded equipment. Alex should prioritise phone outreach over email for these accounts.
- **`urgency: medium` (at/just past reorder date, or proactive within 2 months)**: Standard email outreach is appropriate. Alex may personalise further based on relationship context.
- **`urgency: low` (proactive, > 2 months before due)**: These are early-window contacts. Alex may choose to wait or send a lighter-touch newsletter instead.
- **High-value accounts**: The `order_value_typical_gbp` field is included to help Alex prioritise. Atlas Fertilizer (£195K, 18-month interval) and Northeast Power (£110K, 36-month interval) warrant executive-level outreach even at `medium` urgency.

## Limitations

- **Always dry-run**: The entry point forces `dry_run=True`. No CRM, email, or ERP integration exists.
- **Hardcoded 15-account dataset**: Customer list is embedded in code. No integration with Kimre's CRM or account management system.
- **Hardcoded reference date**: `REFERENCE_DATE = date(2026, 3, 13)`. In production, should use `date.today()`.
- **Uniform interval assumption**: The agent uses `typical_reorder_interval_months` as a fixed schedule. It does not account for extended operating life from recent maintenance, performance data indicating early degradation, or customer-stated schedule changes.
- **No active order deduplication**: The agent does not check whether a customer already has an active order in progress (e.g., Gulf Fertilizers Co. is currently in KIM-052 fabrication). Reaching out to a customer about reordering while their current order is still being built is potentially awkward. The `order_notifier_agent` and `retrofit_reorder_agent` operate independently.
- **Outreach message is templated**: The draft is a structured fill-in. It does not incorporate relationship notes, recent communications history, or application-specific performance context.
- **No send tracking**: There is no log of which outreach messages were sent, which generated responses, or which converted to orders.

## Example Run

```bash
python3 pilot-agents/kimre/retrofit_reorder_agent.py --dry-run
```

Condensed output (3 of ~7 candidates shown from 15 accounts checked):

```
[2026-03-14T09:00:00] === kimre-retrofit-reorder-agent starting (dry_run=True) ===
[2026-03-14T09:00:00] Reference date: 2026-03-13
[2026-03-14T09:00:00] Scanning 15 customer accounts for reorder opportunities...
[2026-03-14T09:00:00]   Gulf Fertilizers Co.: 18.0 months since last order (interval: 18mo, overdue: +0.0mo)
[2026-03-14T09:00:00]     -> CANDIDATE (medium) — drafting outreach message
[2026-03-14T09:00:00]   Atlas Fertilizer Corp: 18.7 months since last order (interval: 18mo, overdue: +0.7mo)
[2026-03-14T09:00:00]     -> CANDIDATE (medium) — drafting outreach message
[2026-03-14T09:00:00]   Midwest Fertilizers: 23.4 months since last order (interval: 18mo, overdue: +5.4mo)
[2026-03-14T09:00:00]     -> CANDIDATE (high) — drafting outreach message
[2026-03-14T09:00:00]   Delta Chemical Corp: 21.0 months since last order (interval: 24mo, overdue: -3.0mo)
[2026-03-14T09:00:00]   Northeast Power Ltd: 27.4 months since last order (interval: 36mo, overdue: -8.6mo)
[2026-03-14T09:00:00]   Gulf Chemicals Trading: 11.8 months since last order (interval: 12mo, overdue: -0.2mo)
[2026-03-14T09:00:00]     -> CANDIDATE (medium) — drafting outreach message
[2026-03-14T09:00:00] === Run complete ===
[2026-03-14T09:00:00]   Accounts checked:      15
[2026-03-14T09:00:00]   Reorder candidates:    7
[2026-03-14T09:00:00]   Output written:        outputs/retrofit_reorder_agent_run_20260314_090000.json
```
