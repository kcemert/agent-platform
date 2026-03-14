# Kimre Marketing Agent
**Slug**: `kimre-marketing-agent`
**File**: `pilot-agents/kimre/marketing_agent.py`
**Lifecycle**: sandbox (Kimre pilot — registered in server.py under slug `kimre-marketing-agent`)
**Last generated**: 2026-03-14 | **Last verified**: 2026-03-14

## Purpose

The Kimre Marketing Agent is the Kimre Inc.-specific instantiation of the generic marketing agent. It automates outbound marketing follow-up for Kimre's two core go-to-market motions: converting trade show contacts into qualified sales conversations and triggering reorder outreach to installed-base accounts approaching their replacement cycle.

Kimre is a 50-year-old Miami-based manufacturer of mist eliminators, drift eliminators, and coalescers for chemical, fertilizer, steel, and power generation industries. Their sales cycle is relationship-driven and technically complex — each follow-up email must reference the specific application discussed (e.g., H2SO4 absorber, HCl pickling tank, NH3 converter), the correct Kimre product grade, and the contact's seniority. Without automation, Alex Torres (Kimre's sales engineer) manually drafts these emails from notes taken at trade shows, often days or weeks after the event.

This agent differs from the generic version in three ways: (1) DRY_RUN_CONTACTS contains 4 real Kimre trade show contacts (Mosaic Fertilizer, Nucor, Chemours, OCI Nitrogen) from actual 2024 conferences; (2) KIMRE_PRODUCT_MAP uses branded product names with registered trademark symbols (B-GON®, LIQUI-NOMIX®, DRIFTOR®); (3) email drafts are signed by Alex Torres with the real Kimre phone number and email. There is no `--client-profile` flag — client context is fully hardcoded.

## Inputs

- **DRY_RUN_CONTACTS** (trade-show-followup mode): 4 Kimre trade show contacts:
  - KC001: James Holloway @ Mosaic Fertilizer LLC — HNO3 scrubber, AIChE Annual 2024, 18 days
  - KC002: Priya Nambiar @ Nucor Steel Birmingham — HCl pickling, METALS USA 2024, 9 days
  - KC003: David Strickland @ Chemours Beaumont — H2SO4 absorber, AIChE Spring 2024, 31 days
  - KC004: Maria Santos @ OCI Nitrogen — NH3 converter, Ammonia Forum 2024, 5 days
- **DRY_RUN_ACCOUNTS** (installed-base-campaign mode): 5 Kimre installed-base accounts:
  - KA001: Valero Energy Corp — B-GON 36-inch, last order 2021-04-12, 30-month cycle
  - KA002: CF Industries — LIQUI-NOMIX Coalescer, 2020-09-07, 36-month cycle
  - KA003: Nucor Yamato Steel — B-GON 48-inch, 2022-11-15, 24-month cycle
  - KA004: Mosaic Fertilizer — Fiber Bed Filter, 2019-06-22, 48-month cycle
  - KA005: Georgia-Pacific Chemicals — DRIFTOR, 2023-03-01, 18-month cycle
- **KIMRE_PRODUCT_MAP**: 8-key keyword-to-branded-product lookup (HNO3, HCl, H2SO4, NH3, "fiber bed", B-GON, drift, coales).
- **Flags**:
  - `--dry-run`: Always enabled (`dry_run=args.dry_run or True`). No live CRM or data source.
  - `--mode {trade-show-followup|installed-base-campaign}`: Selects operating mode. Default: `trade-show-followup`.

## Outputs

```json
{
  "agent": "kimre-marketing-agent",
  "run_at": "2026-03-14T09:00:00",
  "dry_run": true,
  "mode": "trade-show-followup",
  "client": "Kimre Inc.",
  "contacts_processed": 4,
  "drafts_generated": 4,
  "items": [
    {
      "contact_id": "KC003",
      "contact_name": "David Strickland",
      "company": "Chemours Beaumont",
      "title": "Reliability Engineer",
      "rec_type": "marketing_followup",
      "urgency": "high",
      "subject": "Kimre Inc. — Follow-up: H2SO4 absorber outlet mist — EPA inspection — Fiber Bed Filter (FRP housing) specification",
      "body_draft": "Dear David,\n\nThank you for connecting with us at AIChE Spring 2024...\nAlex Torres\nSales Engineer, Kimre Inc.\nalex.torres@kimre.com | +1 305-233-4249",
      "recommended_action": "Send follow-up email",
      "days_since_contact": 31,
      "application_discussed": "H2SO4 absorber outlet mist — EPA inspection coming Q1",
      "tradeshow": "AIChE Spring 2024",
      "product_recommendation": "Fiber Bed Filter (FRP housing) — sulfuric acid mist elimination"
    }
  ],
  "recommendations": [
    {
      "rec_type": "marketing_followup",
      "item_id": "KC003",
      "item_label": "David Strickland @ Chemours Beaumont",
      "urgency": "high",
      "recommended_action": "Send follow-up email",
      "detail": {
        "subject": "Kimre Inc. — Follow-up: ...",
        "days_since_contact": 31,
        "product_recommendation": "Fiber Bed Filter (FRP housing) — sulfuric acid mist elimination"
      }
    }
  ]
}
```

Kimre version adds `product_recommendation` to the `recommendations[].detail` object (the generic version omits this). Output written to `pilot-agents/kimre/outputs/kimre_marketing_agent_run_YYYYMMDD_HHMMSS.json` (if run from kimre/ directory) or `outputs/` relative to cwd.

## Behavior

**trade-show-followup mode:**

1. Load DRY_RUN_CONTACTS (4 Kimre contacts).
2. Compute urgency per contact: `days_since_contact > 14` = high, 7–14 = medium, < 7 = low. KC003 (31 days, Chemours) and KC001 (18 days, Mosaic) are high urgency.
3. Match `application_discussed` against KIMRE_PRODUCT_MAP keywords. H2SO4 matches "Fiber Bed Filter (FRP housing)", HCl matches "B-GON® (CPVC grade)", HNO3 matches "B-GON® (PP grade) — nitric acid service", NH3 matches "B-GON® (PP mesh)".
4. Draft a Kimre-branded follow-up email signed by Alex Torres with phone and email. Subject truncates application to 45 characters. Body references the trade show, application, and Kimre's 50-year track record.
5. Build `items` and `recommendations` lists (all 4 contacts included — no filtering).
6. Write JSON output and print to stdout.

**installed-base-campaign mode:**

1. Load DRY_RUN_ACCOUNTS (5 accounts).
2. Compute months since last order (days / 30.44).
3. Flag if months >= typical_reorder_months * 0.80 (entering the 20% pre-cycle window).
4. Urgency: "high" if months >= typical_reorder_months (past due), "medium" if 80–100%.
5. Draft a Kimre-branded service check-in email with a 3-point inspection checklist (separation efficiency, media condition, upgrade options). Signed by Alex Torres.
6. Only flagged accounts appear in `items` and `recommendations`.
7. Write JSON output and print to stdout.

## HITL Decision Points

All items are email drafts requiring manual review and send by Alex Torres or another Kimre sales engineer. No automated sending occurs.

- **Urgency = high contacts** (> 14 days since trade show): KC003 Chemours (31 days, EPA inspection context) and KC001 Mosaic (18 days) — should be sent same day.
- **Urgency = medium** (7–14 days): KC002 Nucor (9 days) — send within 2 days.
- **Urgency = low** (< 7 days): KC004 OCI Nitrogen (5 days) — can wait.
- **Installed-base "high" urgency**: Accounts past their reorder cycle are at risk of replacement by a competitor. Alex Torres should call, not just email.
- **EPA compliance signals** (KC003 Chemours: "EPA inspection coming Q1"): These contacts have acute buying pressure and should be escalated to a technical call with Frank Powers (VP Engineering) as a follow-up.

## Limitations

- **No `--client-profile` flag**: The Kimre version has no external configuration mechanism. All contact and account data is hardcoded. Swapping to a different client requires editing the source.
- **Always dry-run**: `dry_run=args.dry_run or True` in the entry point. No live CRM integration.
- **Static contacts**: DRY_RUN_CONTACTS represents a specific set of 2024 conference contacts. New contacts from future shows must be added by editing the Python source.
- **Product map is application-keyword-only**: The KIMRE_PRODUCT_MAP lookup is case-insensitive keyword matching. Multi-acid or complex application strings may not match the intended product.
- **Outputs directory**: The script calls `os.makedirs("outputs", exist_ok=True)` relative to the current working directory. Running from `pilot-agents/kimre/` vs. `pilot-agents/` produces output in different locations.
- **Email signatures are hardcoded**: Alex Torres's contact details are embedded in `draft_followup_email` and `draft_installed_base_email`. There is no templating system.
- **No send log or deduplication**: Running the agent twice drafts duplicate emails for the same contacts.

## Example Run

```bash
python3 "pilot-agents/kimre/marketing_agent.py" --dry-run --mode trade-show-followup
```

Condensed output:

```
[2026-03-14T09:00:00] === kimre-marketing-agent starting (dry_run=True, mode=trade-show-followup) ===
[2026-03-14T09:00:00] Processing 4 Kimre trade show contacts...
[2026-03-14T09:00:00]   KC001 — James Holloway @ Mosaic Fertilizer LLC — urgency=high
[2026-03-14T09:00:00]   KC002 — Priya Nambiar @ Nucor Steel Birmingham — urgency=medium
[2026-03-14T09:00:00]   KC003 — David Strickland @ Chemours Beaumont — urgency=high
[2026-03-14T09:00:00]   KC004 — Maria Santos @ OCI Nitrogen — urgency=low
[2026-03-14T09:00:00] === Run complete ===
[2026-03-14T09:00:00]   Contacts processed: 4
[2026-03-14T09:00:00]   Drafts generated:   4
```

```bash
python3 "pilot-agents/kimre/marketing_agent.py" --dry-run --mode installed-base-campaign
```

Condensed output (as of 2026-03-14, all 5 accounts are well past their reorder windows):

```
[2026-03-14T09:00:00] === kimre-marketing-agent starting (dry_run=True, mode=installed-base-campaign) ===
[2026-03-14T09:00:00] Scanning 5 Kimre installed base accounts...
[2026-03-14T09:00:00]   KA001 — Valero Energy Corp — 58.9mo — FLAGGED (high)
[2026-03-14T09:00:00]   KA002 — CF Industries — 66.4mo — FLAGGED (high)
[2026-03-14T09:00:00]   KA003 — Nucor Yamato Steel — 40.0mo — FLAGGED (high)
[2026-03-14T09:00:00]   KA004 — Mosaic Fertilizer — 80.7mo — FLAGGED (high)
[2026-03-14T09:00:00]   KA005 — Georgia-Pacific Chemicals — 36.4mo — FLAGGED (high)
[2026-03-14T09:00:00]   Accounts scanned: 5
[2026-03-14T09:00:00]   Outreach flagged: 5
```
