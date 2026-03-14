# Kimre RFQ Quote Agent
**Slug**: `kimre-rfq-quote-agent`
**File**: `pilot-agents/kimre/rfq_quote_agent.py`
**Lifecycle**: sandbox
**Last generated**: 2026-03-14 | **Last verified**: 2026-03-14

## Purpose

The Kimre RFQ Quote Agent automates the first-pass processing of incoming Request for Quotation (RFQ) documents for Kimre Inc., a specialty manufacturer of mist eliminators, coalescers, and scrubber packing. Without the agent, an applications engineer (Alex Torres) reads each RFQ manually, selects the appropriate product family, writes a scope paragraph from memory, identifies missing specs, and scores the quote opportunity — a process that takes 30–60 minutes per RFQ and is prone to inconsistency.

The agent fits into Kimre's sales and quoting workflow. On each run it processes all open RFQs in the queue, maps each application/chemical combination to the correct product family and model number using a rules table, detects missing specifications required for accurate sizing, scores quote confidence (0.5–0.99) based on data completeness and RFQ age, assigns urgency based on how long the RFQ has been waiting, and drafts a scope paragraph ready for Alex to review and send. The output is consumed by the Kimre sales dashboard (agent-view for `kimre-rfq-quote-agent`).

## Inputs

- **`DRY_RUN_RFQS`**: Hardcoded list of 8 open RFQs representing the current queue. Each entry includes `rfq_id`, `customer`, `contact`, `application`, `application_chemical`, `description`, `received_days_ago`, `flow_rate_m3h` (nullable), `pressure_drop_max_mbar` (nullable), `temperature_c`, and `diameter_in`.
- **`--dry-run` flag**: This agent is always dry-run only. The code forces `dry_run=True` at the entry point (`dry_run_mode = "--dry-run" in sys.argv or True`). There is no live RFQ API.
- **No external API calls**: All data is embedded in `DRY_RUN_RFQS`. No SAP or MES connections.
- **No environment variables required**.

## Outputs

Writes `pilot-agents/kimre/outputs/rfq_quote_agent_run_{YYYYMMDD_HHMMSS}.json` and prints the full JSON to stdout.

```json
{
  "run_at": "2026-03-14T09:10:00",
  "agent": "kimre-rfq-quote-agent",
  "dry_run": true,
  "rfqs_processed": 8,
  "scope_drafts_generated": 3,
  "clarification_needed": 5,
  "items": [
    {
      "rfq_id": "RFQ-2026-020",
      "customer": "Gulf Fertilizers Co.",
      "contact": "Ahmed Al-Rashid",
      "application": "Fertilizer",
      "application_chemical": "HNO3",
      "product_family": "B-GON® Mist Eliminator",
      "model_recommendation": "ME-48-PP-99",
      "scope_draft": "Based on your Fertilizer application involving HNO3, we recommend our B-GON® Mist Eliminator (Model: ME-48-PP-99). Polypropylene mesh recommended for HNO3 service — excellent chemical resistance and cost-effective for fertilizer applications. For a 48-inch unit operating at 48-inch diameter, 12,000 m³/h flow, 40°C operating temperature, our standard configuration provides the required 99% separation efficiency. We will provide a detailed technical proposal including dimensional drawings and material specifications upon confirmation of your requirements as stated.",
      "confidence": 0.95,
      "gaps": [],
      "urgency": "low",
      "received_days_ago": 2,
      "rec_type": "quote_draft"
    },
    {
      "rfq_id": "RFQ-2026-019",
      "customer": "Petrochem Solutions Ltd",
      "contact": "David Park",
      "application": "Petrochemical",
      "application_chemical": "H2SO4",
      "product_family": "LIQUI-NOMIX® Coalescer",
      "model_recommendation": "CO-36-CPVC-98",
      "scope_draft": "Based on your Petrochemical application involving H2SO4, we recommend our LIQUI-NOMIX® Coalescer (Model: CO-36-CPVC-98)...",
      "confidence": 0.65,
      "gaps": [
        "flow rate not specified — required for sizing",
        "maximum pressure drop not specified"
      ],
      "urgency": "high",
      "received_days_ago": 7,
      "rec_type": "quote_draft"
    }
  ]
}
```

## Behavior

1. **Iterate RFQ queue**: Loops over all 8 entries in `DRY_RUN_RFQS`.
2. **Product family lookup**: Matches `application` + `application_chemical` against a two-level `PRODUCT_RULES` dict. Supported combinations include: Fertilizer/HNO3 and Fertilizer/NH3 → B-GON Mist Eliminator (PP); Petrochemical/H2SO4 → LIQUI-NOMIX Coalescer (CPVC); Petrochemical/NaOH → KON-TANE Scrubber Packing (PP); Petrochemical/Amines → B-GON Mist Eliminator (SS); Power Gen/H2SO4 and Sulfuric Acid/H2SO4 → Fiber Bed Filter (FRP); Steel Pickling/HCl → B-GON Mist Eliminator (CPVC). Unmatched combinations fall back to `DEFAULT_RULE` (PP mesh, with a note to review).
3. **Gap detection**: Flags missing fields that are required for accurate sizing: `flow_rate_m3h is None`, `pressure_drop_max_mbar is None`, or `diameter_in` absent. Returns a plain-English list of gap descriptions.
4. **Confidence scoring**: Starts at 0.95. Deducts 0.15 per detected gap. Adds 0.02 if `received_days_ago > 5` (older RFQs typically have supplemental information available). Clamps to the range [0.50, 0.99].
5. **Urgency assignment**: `received_days_ago > 5` → `"high"`; `3–5 days` → `"medium"`; `< 3 days` → `"low"`.
6. **Scope paragraph generation**: Builds a structured English scope paragraph incorporating product family, model number (with `{dia}` substituted), material rationale, operating conditions, efficiency target (extracted from model code: `99.9`, `99`, or `98`), and a gap resolution clause. If gaps exist, the clause requests confirmation of those specifics; otherwise references "your requirements as stated."
7. **Accumulate results**: Appends each processed RFQ to `items` as a `quote_draft` record.
8. **Write output**: Saves JSON to `outputs/`, prints to stdout. Counts `scope_drafts_generated` (no gaps) and `clarification_needed` (gaps present).

## HITL Decision Points

- **All items require human review before sending**: The agent drafts scope paragraphs but does not email or submit quotes. Alex Torres reviews each draft in the sales dashboard.
- **`gaps` present (`clarification_needed`)**: Alex must follow up with the customer to obtain missing specifications (flow rate, pressure drop) before a compliant quote can be issued. The draft scope includes a placeholder clause requesting these.
- **Low confidence scores (< 0.65)**: Indicate multiple missing specs. Alex should prioritize clarification calls for these RFQs before investing in detailed technical proposals.
- **`urgency: high` (received > 5 days ago)**: Flags RFQs that have been waiting longest. Alex should action these first to protect the customer relationship.
- **Product family fallback**: If the `DEFAULT_RULE` was applied (unrecognised application/chemical combination), the scope draft will note "application-specific material review recommended" — requiring applications engineering sign-off before sending.

## Limitations

- **Always dry-run**: The entry point forces `dry_run=True` regardless of the `--dry-run` flag. No live RFQ system integration exists.
- **Hardcoded 8-RFQ queue**: The queue is a static list embedded in code. There is no CRM, ERP, or email integration to populate it dynamically.
- **Rules table is not exhaustive**: The `PRODUCT_RULES` dict covers 8 application/chemical combinations. Novel combinations (e.g., `HF`, `Chlorine`, `Methanol`) fall back to the generic PP mesh default, which may be incorrect.
- **Scope paragraph is templated**: The draft is a structured fill-in, not an LLM-generated narrative. Technical nuances (e.g., special alloy requirements, custom efficiency targets, non-standard vessel geometries) are not captured.
- **No pricing**: The agent produces model recommendations and scope text only. No pricing or lead-time estimate is included.
- **No CRM write-back**: Quote drafts are written to a local JSON file only; no Salesforce, HubSpot, or Kimre internal system is updated.

## Example Run

```bash
python3 pilot-agents/kimre/rfq_quote_agent.py --dry-run
```

Condensed output (2 of 8 items shown):

```
[2026-03-14T09:10:00] === kimre-rfq-quote-agent starting (dry_run=True) ===
[2026-03-14T09:10:00] Processing 8 incoming RFQs...
[2026-03-14T09:10:00]   Processing RFQ-2026-020 — Gulf Fertilizers Co. (HNO3)
[2026-03-14T09:10:00]     Scope draft generated — confidence 95%
[2026-03-14T09:10:00]   Processing RFQ-2026-019 — Petrochem Solutions Ltd (H2SO4)
[2026-03-14T09:10:00]     GAPS detected: flow rate not specified — required for sizing; maximum pressure drop not specified
[2026-03-14T09:10:00]   Processing RFQ-2026-018 — Southern Power Generation (H2SO4)
[2026-03-14T09:10:00]     Scope draft generated — confidence 95%
[2026-03-14T09:10:00]   Processing RFQ-2026-015 — Atlas Fertilizer Corp (NH3)
[2026-03-14T09:10:00]     Scope draft generated — confidence 97%
[2026-03-14T09:10:00] === Run complete ===
[2026-03-14T09:10:00]   RFQs processed:         8
[2026-03-14T09:10:00]   Scope drafts generated: 3
[2026-03-14T09:10:00]   Clarification needed:   5
[2026-03-14T09:10:00]   Output written to:      outputs/rfq_quote_agent_run_20260314_091000.json
```
