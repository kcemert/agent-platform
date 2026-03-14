# Marketing Agent
**Slug**: `marketing-agent`
**File**: `pilot-agents/marketing_agent.py`
**Lifecycle**: blueprint (generic — no DB blueprint entry; Kimre-specific version is in `pilot-agents/kimre/`)
**Last generated**: 2026-03-14 | **Last verified**: 2026-03-14

## Purpose

The Marketing Agent automates two outbound marketing workflows for industrial product companies: following up on trade show contacts and running installed-base reorder campaigns. Without automation, sales engineers manually track who they met at conferences, decide which contacts to prioritize, draft individual emails, and separately scan customer records for reorder windows — a process that typically takes hours per week and produces inconsistent follow-through.

The generic version ships with simulated contacts and accounts representing a chemical-process equipment company (mist eliminators, coalescers, drift eliminators). When `--client-profile` is supplied, it loads the client name from the JSON and tags output accordingly. The Kimre-specific variant (`pilot-agents/kimre/marketing_agent.py`) replaces the generic data with hardcoded Kimre contacts, named accounts, and product-branded email templates. In both variants, all data is static — no live CRM or MAP integration exists yet.

## Inputs

- **DRY_RUN_CONTACTS** (trade-show-followup mode): 3 hardcoded trade show contacts (Pacific Chem Inc, Atlantic Steel Partners, Gulf Fertilizer Corp) with `contact_id`, `name`, `company`, `title`, `application_discussed`, `tradeshow`, `days_since_contact`.
- **DRY_RUN_ACCOUNTS** (installed-base-campaign mode): 5 hardcoded installed-base accounts with `account_id`, `name`, `product_purchased`, `last_order_date`, `typical_reorder_months`.
- **PRODUCT_MAP**: Internal keyword-to-product lookup (H2SO4, HCl, NH3, HNO3, acid, drift, coales) used to select the correct product recommendation per application.
- **Flags**:
  - `--dry-run`: Always enabled in practice (`dry_run=args.dry_run or True` in entry point). Disabling it does not connect to a live CRM — the variable is passed through to output metadata only.
  - `--mode {trade-show-followup|installed-base-campaign}`: Selects operating mode. Default: `trade-show-followup`.
  - `--client-profile <path>`: Optional path to a client profile JSON. Loads `name` field for output tagging; does not change data sources.

## Outputs

```json
{
  "agent": "marketing-agent",
  "run_at": "2026-03-14T09:00:00",
  "dry_run": true,
  "mode": "trade-show-followup",
  "client": "generic",
  "contacts_processed": 3,
  "drafts_generated": 3,
  "items": [
    {
      "contact_id": "C001",
      "contact_name": "Dr. Sarah Chen",
      "company": "Pacific Chem Inc",
      "title": "Process Engineer",
      "rec_type": "marketing_followup",
      "urgency": "high",
      "subject": "Following up: H2SO4 absorption tower mist control — B-GON Mist Eliminator specification",
      "body_draft": "Dear Sarah,\n\nIt was great connecting with you at AIChE Spring 2024...",
      "recommended_action": "Send follow-up email",
      "days_since_contact": 12,
      "application_discussed": "H2SO4 absorption tower mist control",
      "tradeshow": "AIChE Spring 2024",
      "product_recommendation": "B-GON Mist Eliminator"
    }
  ],
  "recommendations": [
    {
      "rec_type": "marketing_followup",
      "item_id": "C001",
      "item_label": "Dr. Sarah Chen @ Pacific Chem Inc",
      "urgency": "high",
      "recommended_action": "Send follow-up email",
      "detail": {
        "subject": "Following up: H2SO4 absorption tower mist control — B-GON Mist Eliminator specification",
        "days_since_contact": 12
      }
    }
  ]
}
```

In installed-base-campaign mode, the top-level fields change to `accounts_scanned` and `outreach_flagged`, and `items` contain `account_id`, `account_name`, `product_purchased`, `last_order_date`, `months_since_last_order`, `typical_reorder_months`, `urgency`, `subject`, `body_draft`, `recommended_action`.

Output is also written to `pilot-agents/outputs/marketing_agent_run_YYYYMMDD_HHMMSS.json`.

## Behavior

**trade-show-followup mode:**

1. Load DRY_RUN_CONTACTS (3 contacts). If `--client-profile` is provided, read name for output tagging.
2. For each contact, compute urgency from `days_since_contact`: >14 days = high, 7–14 = medium, <7 = low.
3. Match `application_discussed` against PRODUCT_MAP keyword list (case-insensitive) to select a product recommendation. Default fallback: "B-GON Mist Eliminator".
4. Draft a personalized follow-up email: subject includes truncated application and product name; body references the trade show, application, company, and requests a 30-minute technical review.
5. Build `items` list and flatten into `recommendations` list (one entry per contact).
6. Write JSON to `outputs/` directory and print to stdout.

**installed-base-campaign mode:**

1. Load DRY_RUN_ACCOUNTS (5 accounts).
2. For each account, compute months since last order (days / 30.44).
3. Flag for outreach if months >= typical_reorder_months * 0.80 (i.e., within 20% of reorder window).
4. Set urgency = "high" if months >= typical_reorder_months (past due); "medium" if 80–100% of cycle.
5. Draft a service check-in email referencing the product name, elapsed months, and recommended replacement cycle.
6. Only flagged accounts appear in `items` and `recommendations`; OK accounts are logged but omitted from output.
7. Write JSON to `outputs/` directory and print to stdout.

## HITL Decision Points

All items are recommendations only — no emails are sent automatically. The human review workflow is:

- **All drafted emails** require a sales engineer or account manager to review and send manually. The `body_draft` field contains the full draft for copy/edit/send.
- **Urgency = high** items should be prioritized for same-day review (contacts >14 days since meeting; accounts past their reorder cycle).
- **Urgency = medium** items should be reviewed within 2–3 business days.
- No auto-execution path exists. The agent produces drafts and recommendations only.

## Limitations

- **Always dry-run**: The entry point hardcodes `dry_run=args.dry_run or True`, meaning `--dry-run` is always effectively true. No live CRM, MAP, or email system is connected.
- **Static data**: DRY_RUN_CONTACTS and DRY_RUN_ACCOUNTS are hardcoded in the script. There is no mechanism to pull live contacts from a CRM or database without code changes.
- **`--client-profile` has minimal effect**: Loading a profile JSON only changes the `client` field in output metadata. It does not swap contact lists or product catalogs.
- **Product matching is keyword-only**: PRODUCT_MAP uses simple string matching; complex or multi-application queries may default to the generic "B-GON Mist Eliminator" fallback.
- **Email drafts are templates**: The body_draft is a structured template. Personalization is limited to name, company, trade show, and application fields extracted from the contact record.
- **No deduplication**: Running the agent multiple times will produce duplicate drafts for the same contacts.

## Example Run

```bash
python3 "pilot-agents/marketing_agent.py" --dry-run --mode trade-show-followup
```

Condensed output:

```
[2026-03-14T09:00:00] === marketing-agent starting (dry_run=True, mode=trade-show-followup) ===
[2026-03-14T09:00:00] Processing 3 trade show contacts...
[2026-03-14T09:00:00]   C001 — Dr. Sarah Chen @ Pacific Chem Inc — urgency=high
[2026-03-14T09:00:00]   C002 — Marcus Webb @ Atlantic Steel Partners — urgency=medium
[2026-03-14T09:00:00]   C003 — Anita Patel @ Gulf Fertilizer Corp — urgency=high
[2026-03-14T09:00:00] === Run complete ===
[2026-03-14T09:00:00]   Contacts processed: 3
[2026-03-14T09:00:00]   Drafts generated:   3
[2026-03-14T09:00:00]   Output: outputs/marketing_agent_run_20260314_090000.json
```

```bash
python3 "pilot-agents/marketing_agent.py" --dry-run --mode installed-base-campaign
```

Condensed output:

```
[2026-03-14T09:01:00] === marketing-agent starting (dry_run=True, mode=installed-base-campaign) ===
[2026-03-14T09:01:00] Scanning 5 installed base accounts...
[2026-03-14T09:01:00]   A001 — Cascade Chemicals — 43.1mo since last order — FLAGGED
[2026-03-14T09:01:00]   A002 — Northern Pickling Co — 52.0mo since last order — FLAGGED
[2026-03-14T09:01:00]   A003 — Keystone Power — 36.8mo — OK
[2026-03-14T09:01:00]   A004 — Prairie Ag Solutions — 70.1mo — FLAGGED
[2026-03-14T09:01:00]   A005 — Gulf Coast Refining — 39.5mo — FLAGGED
[2026-03-14T09:01:00] === Run complete ===
[2026-03-14T09:01:00]   Accounts scanned: 5
[2026-03-14T09:01:00]   Outreach flagged: 4
```
