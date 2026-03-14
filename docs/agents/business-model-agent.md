# Business Model Agent
**Slug**: `business-model-agent`
**File**: `pilot-agents/business_model_agent.py`
**Lifecycle**: blueprint (generic — no DB blueprint entry; Kimre-specific version is in `pilot-agents/kimre/`)
**Last generated**: 2026-03-14 | **Last verified**: 2026-03-14

## Purpose

The Business Model Agent implements the F24 Business Model Reinvention Assessment framework. It scores a set of potential business model moves across four weighted dimensions and produces prioritized recommendations (Expand / Pilot First / Monitor / Defer) for leadership decision-making. The target audience is senior management and strategy teams at industrial manufacturing companies considering revenue diversification beyond their core engineering-to-order (ETO) product business.

The generic version assesses 7 archetypal business model moves (service contracts, MTS catalog, digital portal, distribution, performance contracts, technology licensing, SaaS tools) with narrative rationale, risk lists, and Year-1 value estimates. When `--client-profile` is supplied, the agent loads the client name and `business_model` array from the JSON and tags output accordingly; the move data itself remains the generic DRY_RUN_MOVES set. The Kimre-specific variant (`pilot-agents/kimre/business_model_agent.py`) replaces these moves with Kimre-tailored narratives and scores that reflect Kimre's 50-year installed base, B-GON IP, and ETO+MTO hybrid manufacturing model.

## Inputs

- **DRY_RUN_MOVES**: 7 hardcoded business model move objects, each with:
  - `move` (slug), `move_label` (display name)
  - `market_attractiveness` (1–5), `capability_fit` (1–5), `strategic_coherence` (1–5), `risk_profile` (1–5)
  - `narrative` (string rationale), `risks` (list of strings), `year1_value_est` (string estimate), `enabling_agents` (list of agent slugs)
- **WEIGHTS** (hardcoded): `market_attractiveness=0.30`, `capability_fit=0.30`, `strategic_coherence=0.25`, `risk_profile=0.15`
- **Flags**:
  - `--dry-run`: Always enabled (`dry_run=args.dry_run or True` in entry point). The flag is present for interface consistency but has no effect — the agent always uses DRY_RUN_MOVES.
  - `--client-profile <path>`: Optional path to a client profile JSON. Reads `name` (string) and `business_model` (list) for output metadata. Does not change the move dataset.

## Outputs

```json
{
  "agent": "business-model-agent",
  "run_at": "2026-03-14T09:00:00",
  "dry_run": true,
  "client": "generic",
  "current_model": ["ETO_Custom"],
  "moves_assessed": 7,
  "top_recommendation": "mts-catalog",
  "items": [
    {
      "move": "mts-catalog",
      "move_label": "MTS Product Catalog Expansion",
      "market_attractiveness": 4,
      "capability_fit": 4,
      "strategic_coherence": 4,
      "risk_profile": 4,
      "composite_score": 4.0,
      "recommendation": "Expand",
      "urgency": "high",
      "narrative": "Existing manufacturing capability and product IP position this move as low-risk...",
      "risks": ["Requires SKU management discipline", "May dilute ETO engineering focus"],
      "year1_value_est": "£30K–£60K additional revenue from catalog orders",
      "enabling_agents": ["inventory-replenishment-agent"]
    }
  ],
  "recommendations": [
    {
      "rec_type": "model_move",
      "item_id": "mts-catalog",
      "item_label": "MTS Product Catalog Expansion",
      "urgency": "high",
      "recommended_action": "Expand — begin implementation planning for MTS Product Catalog Expansion",
      "detail": {
        "composite_score": 4.0,
        "recommendation": "Expand",
        "year1_value_est": "£30K–£60K additional revenue from catalog orders"
      }
    }
  ]
}
```

`items` contains all 7 moves sorted by `composite_score` descending. `recommendations` contains only moves with recommendation = "Expand" or "Pilot First". Output is also written to `pilot-agents/outputs/business_model_agent_run_YYYYMMDD_HHMMSS.json`.

## Behavior

1. Load client context from `--client-profile` JSON if provided (name + business_model). Default: `client="generic"`, `current_model=["ETO_Custom"]`.
2. Load all 7 DRY_RUN_MOVES.
3. For each move, compute composite score:
   `composite = market_attractiveness * 0.30 + capability_fit * 0.30 + strategic_coherence * 0.25 + risk_profile * 0.15`
   Rounded to 2 decimal places.
4. Map composite score to recommendation:
   - >= 4.0 → "Expand" (urgency = high)
   - >= 3.0 → "Pilot First" (urgency = medium)
   - >= 2.0 → "Monitor" (urgency = low)
   - < 2.0 → "Defer" (urgency = low)
5. Build `recommended_action` string: e.g., "Expand — begin implementation planning for MTS Product Catalog Expansion".
6. Log each move's composite score and recommendation tier to stdout.
7. Sort all items by `composite_score` descending; set `top_recommendation` to the highest-scoring move slug.
8. Filter `recommendations` list to moves with recommendation in ("Expand", "Pilot First").
9. Write JSON output and print to stdout.

## HITL Decision Points

All outputs are strategic recommendations requiring human deliberation. No automated actions are taken.

- **"Expand" moves** (composite >= 4.0): Flagged as high urgency. Leadership should schedule a planning session to scope resource requirements and assign ownership.
- **"Pilot First" moves** (composite 3.0–3.99): Medium urgency. A pilot design and success criteria should be defined before commitment. The `enabling_agents` field lists platform agents that could support a pilot.
- **"Monitor" moves** (composite 2.0–2.99): Low urgency. Track market conditions and revisit at next quarterly strategy review.
- **"Defer" moves** (composite < 2.0): No immediate action warranted. The `risks` list explains the blocking factors.
- The `year1_value_est` field provides a human-readable financial framing; it is an estimate only and must be validated by finance before use in business cases.

## Limitations

- **Always dry-run**: Entry point hardcodes `dry_run=args.dry_run or True`. There is no live data source for business model moves — the agent is entirely score-based on pre-coded move definitions.
- **Static move set**: The 7 DRY_RUN_MOVES are hardcoded. Adding or modifying moves requires editing the Python source. There is no external move library or configuration file.
- **`--client-profile` has minimal effect**: Only `name` and `business_model` fields are read from the profile. The move scores, narratives, and risks are not customized from the profile data.
- **Scores are expert estimates**: The 1–5 ratings for each dimension on each move are hardcoded by the agent author. They are illustrative, not derived from live market data or client financials.
- **Currency is GBP by convention**: `year1_value_est` strings use £ values appropriate for the generic UK industrial equipment context. The Kimre version also uses £ for consistency.
- **No sensitivity analysis**: The composite score uses fixed weights. The agent does not model how outcomes change under different weight configurations.
- **Enabling agents are advisory**: The `enabling_agents` list names platform agents that could support a move, but no integration or dependency chain exists.

## Example Run

```bash
python3 "pilot-agents/business_model_agent.py" --dry-run
```

Condensed output:

```
[2026-03-14T09:00:00] === business-model-agent starting (dry_run=True) ===
[2026-03-14T09:00:00] Assessing 7 business model moves...
[2026-03-14T09:00:00]   service-maintenance: composite=3.85 → Pilot First
[2026-03-14T09:00:00]   mts-catalog: composite=4.0 → Expand
[2026-03-14T09:00:00]   digital-customer-portal: composite=3.0 → Pilot First
[2026-03-14T09:00:00]   distribution: composite=3.0 → Pilot First
[2026-03-14T09:00:00]   performance-contract: composite=3.25 → Pilot First
[2026-03-14T09:00:00]   technology-licensing: composite=2.9 → Monitor
[2026-03-14T09:00:00]   saas-tools: composite=3.0 → Pilot First
[2026-03-14T09:00:00] Top recommendation: mts-catalog (score 4.0)
[2026-03-14T09:00:00] === Run complete ===
[2026-03-14T09:00:00]   Moves assessed:      7
[2026-03-14T09:00:00]   Top recommendation:  mts-catalog
[2026-03-14T09:00:00]   Expand/Pilot moves:  6
[2026-03-14T09:00:00]   Output: outputs/business_model_agent_run_20260314_090000.json
```
