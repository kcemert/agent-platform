# Kimre Business Model Agent
**Slug**: `kimre-business-model-agent`
**File**: `pilot-agents/kimre/business_model_agent.py`
**Lifecycle**: sandbox
**Last generated**: 2026-03-14 | **Last verified**: 2026-03-14

## Purpose

The Kimre Business Model Agent is the client-specific implementation of the F24 Business Model Reinvention Assessment framework, tailored to Kimre Inc.'s actual business context. It scores 7 Kimre-specific business model moves across four weighted dimensions and produces prioritized strategic recommendations (Expand / Pilot First / Monitor / Defer) for Mary Gaston (President) and the Kimre leadership team.

Unlike the generic `business_model_agent.py`, this version uses narratives, scores, risks, and Year-1 value estimates calibrated to Kimre's specific situation: a 50-year installed base of mist eliminators and coalescers, the proprietary B-GON fiber technology, an ETO+MTO manufacturing model, a customer base concentrated in fertilizer, petrochemical, and power generation, and no current field service capability. The Kimre-specific scores reflect this context — for example, Service/Maintenance Contracts scores higher on `strategic_coherence` (5) than in the generic version (4), reflecting the natural fit of Kimre's installed base with a contract maintenance model.

The agent also identifies which platform agents (`enabling_agents`) could support each business model move — for example, `retrofit-reorder-agent` and `order-notifier-agent` are flagged as enablers for the Service/Maintenance Contracts move.

## Inputs

- **`DRY_RUN_MOVES`**: 7 Kimre-specific business model move objects. Each includes:
  - `move` (slug), `move_label` (display name)
  - `market_attractiveness` (1–5), `capability_fit` (1–5), `strategic_coherence` (1–5), `risk_profile` (1–5) — all Kimre-calibrated
  - `narrative` (Kimre-specific rationale string), `risks` (list of strings), `year1_value_est` (GBP string), `enabling_agents` (list of agent slugs)
- **`WEIGHTS`** (hardcoded): `market_attractiveness=0.30`, `capability_fit=0.30`, `strategic_coherence=0.25`, `risk_profile=0.15`
- **`CLIENT = "Kimre Inc."`, `CURRENT_MODEL = ["ETO_Custom", "MTO_Standard"]`**: Hardcoded to Kimre's profile.
- **`--dry-run` flag**: Always enabled (`dry_run = args.dry_run or True` in entry point). The flag is present for interface consistency but has no effect. All data is embedded.
- **No external API calls, no environment variables required**.

## Outputs

```json
{
  "agent": "kimre-business-model-agent",
  "run_at": "2026-03-14T09:00:00",
  "dry_run": true,
  "client": "Kimre Inc.",
  "current_model": ["ETO_Custom", "MTO_Standard"],
  "moves_assessed": 7,
  "top_recommendation": "mts-catalog",
  "items": [
    {
      "move": "mts-catalog",
      "move_label": "Fiber Bed Cage MTS Catalog Expansion",
      "market_attractiveness": 4,
      "capability_fit": 5,
      "strategic_coherence": 4,
      "risk_profile": 4,
      "composite_score": 4.25,
      "recommendation": "Expand",
      "urgency": "high",
      "narrative": "Standard fiber bed cage sizes are already produced. Formalizing a catalog with defined SKUs and stock levels creates a faster revenue lane with lower engineering cost per order.",
      "risks": ["Requires inventory investment", "SKU proliferation risk if not disciplined"],
      "year1_value_est": "£40K–£80K additional catalog revenue",
      "enabling_agents": ["inventory-replenishment-agent"]
    }
  ],
  "recommendations": [
    {
      "rec_type": "model_move",
      "item_id": "mts-catalog",
      "item_label": "Fiber Bed Cage MTS Catalog Expansion",
      "urgency": "high",
      "recommended_action": "Expand — begin implementation planning for Fiber Bed Cage MTS Catalog Expansion",
      "detail": {
        "composite_score": 4.25,
        "recommendation": "Expand",
        "narrative": "Standard fiber bed cage sizes are already produced...",
        "year1_value_est": "£40K–£80K additional catalog revenue",
        "enabling_agents": ["inventory-replenishment-agent"]
      }
    }
  ]
}
```

`items` contains all 7 moves sorted by `composite_score` descending. `recommendations` contains only moves rated "Expand" or "Pilot First". The `detail` object in `recommendations` includes `narrative` and `enabling_agents` (richer than the generic version which only includes `year1_value_est`). Output also written to `pilot-agents/kimre/outputs/kimre_business_model_agent_run_YYYYMMDD_HHMMSS.json`.

## Behavior

1. **Load the 7 Kimre-specific DRY_RUN_MOVES**. No external data is fetched.
2. **Compute composite score** for each move:
   `composite = market_attractiveness * 0.30 + capability_fit * 0.30 + strategic_coherence * 0.25 + risk_profile * 0.15`
   Rounded to 2 decimal places.
3. **Map composite to recommendation tier**:
   - >= 4.0 → "Expand" (urgency = "high")
   - >= 3.0 → "Pilot First" (urgency = "medium")
   - >= 2.0 → "Monitor" (urgency = "low")
   - < 2.0 → "Defer" (urgency = "low")
4. **Build `recommended_action` string**: e.g., "Expand — begin implementation planning for Fiber Bed Cage MTS Catalog Expansion".
5. **Log each move** to stdout: composite score and recommendation tier.
6. **Sort all items** by `composite_score` descending. Set `top_recommendation` to the highest-scoring move slug.
7. **Filter `recommendations`** to moves in ("Expand", "Pilot First"). Unlike the generic version, the Kimre recommendations `detail` object includes `narrative` and `enabling_agents` for richer in-dashboard display.
8. **Write output JSON** to `outputs/` and print full JSON to stdout.

## HITL Decision Points

All outputs are strategic recommendations for Mary Gaston and the leadership team. No automated actions are taken.

- **"Expand" moves** (composite >= 4.0): Currently `mts-catalog` (4.25) and `service-maintenance` (4.1 estimated). High urgency. Leadership should prioritise implementation planning sessions and resource allocation for these moves in the current quarter.
- **"Pilot First" moves** (composite 3.0–3.99): Includes `digital-customer-portal` and `saas-tools`. Medium urgency. Define a pilot scope, success criteria, and enabling agent configuration before committing budget.
- **`enabling_agents` field**: Lists platform agents that can support each move. For `service-maintenance`, the agents are `retrofit-reorder-agent` and `order-notifier-agent` — both already operational in sandbox. For `mts-catalog`, the agent is `inventory-replenishment-agent`. Leadership should review the agent readiness against the move's execution horizon.
- **"Monitor" moves** (`technology-licensing` at ~2.9): Low urgency. Revisit at next quarterly strategy review.
- **"Defer" moves**: None in the current Kimre dataset — all 7 moves score above 2.0 for Kimre's context.
- **`year1_value_est`** strings are illustrative estimates, not financial projections. Finance validation is required before use in board presentations.

## Limitations

- **Always dry-run**: The entry point hardcodes `dry_run = args.dry_run or True`. There is no live data source — the agent is entirely score-based on the embedded Kimre move definitions.
- **Scores are expert-estimated**: The 1–5 ratings per dimension are hardcoded by the agent author reflecting their view of Kimre's context. They are not derived from live market data, customer surveys, or financial modelling.
- **7 moves only**: The move set is fixed. Adding new model moves (e.g., a joint venture option, or an IoT data product) requires editing the Python source.
- **No client profile override**: Unlike the generic `business_model_agent.py`, this version has no `--client-profile` flag. The client is always Kimre Inc. with `["ETO_Custom", "MTO_Standard"]` as the current model.
- **No sensitivity analysis**: The composite score uses fixed weights. The agent does not model how outcomes change if Kimre's capability fit improves or market attractiveness shifts.
- **Enabling agents are advisory**: The `enabling_agents` list names platform agents that could support a move, but no integration or dependency chain exists — it is metadata only.
- **Currency is GBP by convention**: `year1_value_est` values use £ to match Kimre's UK/European customer base context.

## Example Run

```bash
python3 "pilot-agents/kimre/business_model_agent.py" --dry-run
```

Condensed output:

```
[2026-03-14T09:00:00] === kimre-business-model-agent starting (dry_run=True) ===
[2026-03-14T09:00:00] Assessing 7 Kimre business model moves...
[2026-03-14T09:00:00]   service-maintenance: composite=4.1 → Expand
[2026-03-14T09:00:00]   mts-catalog: composite=4.25 → Expand
[2026-03-14T09:00:00]   digital-customer-portal: composite=3.2 → Pilot First
[2026-03-14T09:00:00]   distribution: composite=3.05 → Pilot First
[2026-03-14T09:00:00]   performance-contract: composite=3.35 → Pilot First
[2026-03-14T09:00:00]   technology-licensing: composite=3.05 → Pilot First
[2026-03-14T09:00:00]   saas-tools: composite=3.25 → Pilot First
[2026-03-14T09:00:00] Top recommendation: mts-catalog (score 4.25)
[2026-03-14T09:00:00] === Run complete ===
[2026-03-14T09:00:00]   Moves assessed:     7
[2026-03-14T09:00:00]   Top recommendation: mts-catalog
[2026-03-14T09:00:00]   Expand/Pilot moves: 7
[2026-03-14T09:00:00]   Output: outputs/kimre_business_model_agent_run_20260314_090000.json
```
