# CG Replenishment PR Agent
**Slug**: `cg-replenishment-pr-agent`
**File**: `pilot-agents/replenishment_agent.py`
**Lifecycle**: sandbox
**Last generated**: 2026-03-14 | **Last verified**: 2026-03-14

## Purpose

The CG Replenishment PR Agent automates inventory-triggered purchase requisition (PR) creation for Consumer Goods SKUs. It solves the manual, error-prone process of monitoring 20+ oil SKUs against reorder points and creating PRs in SAP — a task that typically requires a supply chain planner to check inventory daily and manually key PRs for each triggered item.

The primary user is the operations planner persona (Sam). The agent fits into the daily replenishment workflow: it runs on a scheduled trigger, evaluates each SKU's stock versus its reorder point, calculates the correct order quantity, POSTs PRs directly to SAP, and flags any critically low items for urgent follow-up. Each PR created saves approximately 0.5 hours of manual planner work.

## Inputs

- **SAP Inventory API** (`GET http://localhost:3001/api/inventory`): Returns all CG SKUs with `material_id`, `description`, `unrestricted_stock`, `reorder_point`, `on_order`, `unit`, and optional `plant` fields. Accepts list or dict response shapes with keys `items`, `inventory`, `data`, or `results`.
- **`--dry-run` flag**: When passed, bypasses all API calls and uses hardcoded `DRY_RUN_INVENTORY` (10 oil SKUs: Canola Oil, Soybean Oil, Olive Oil, Sunflower Oil, Corn Oil, Vegetable Shortening, Coconut Oil, Palm Oil, Flaxseed Oil, Avocado Oil).
- **Hardcoded configuration**: `SAP_BASE = "http://localhost:3001"`, `PLANT = "CG01"`, `REQUESTER = "replenishment-agent-v1"`.
- **No environment variables required**.

## Outputs

The agent writes a JSON file to `pilot-agents/outputs/replenishment_run_{YYYYMMDD_HHMMSS}.json` and logs a run record to the `agent_runs` table in `business_agents.db`. It also inserts two rows into `value_tracking` per run (metric types: `prs_created` and `hours_saved`).

```json
{
  "run_at": "2026-03-14T09:15:00.000000",
  "trigger": "below_reorder_point",
  "authority": "low",
  "dry_run": true,
  "items_checked": 10,
  "items_triggered": 4,
  "prs_created": [
    {
      "pr_number": "PR-DRY-001",
      "material_id": "CG-SKU-001",
      "quantity": 280,
      "priority": "NORMAL",
      "status": "simulated"
    },
    {
      "pr_number": "PR-DRY-003",
      "material_id": "CG-SKU-003",
      "quantity": 315,
      "priority": "HIGH_PRIORITY",
      "status": "simulated"
    },
    {
      "pr_number": "PR-DRY-006",
      "material_id": "CG-SKU-006",
      "quantity": 170,
      "priority": "HIGH_PRIORITY",
      "status": "simulated"
    },
    {
      "pr_number": "PR-DRY-009",
      "material_id": "CG-SKU-009",
      "quantity": 135,
      "priority": "HIGH_PRIORITY",
      "status": "simulated"
    }
  ],
  "high_priority_flags": [
    {
      "material_id": "CG-SKU-003",
      "description": "Olive Oil Extra Virgin",
      "stock": 45,
      "reorder_point": 180,
      "pct_below": 75.0
    }
  ],
  "escalations": []
}
```

## Behavior

1. **Fetch inventory**: Calls `GET /api/inventory` on the mock SAP server. Falls back to `DRY_RUN_INVENTORY` if the API is unavailable or returns a non-200 status.
2. **Evaluate each SKU**: For every item, checks whether `unrestricted_stock < reorder_point` AND `on_order == 0`. SKUs with an existing open order are skipped to prevent duplicate PRs.
3. **Calculate order quantity**: For triggered SKUs, computes `order_qty = (reorder_point * 2) - unrestricted_stock`, ensuring a minimum of 1 unit.
4. **Determine priority**: Calculates `pct_below = (reorder_point - stock) / reorder_point`. Items more than 50% below their reorder point are flagged `HIGH_PRIORITY`; all others are `NORMAL`.
5. **Create purchase requisition**: POSTs a PR body to `POST /api/purchase-requisitions` including `material_id`, `quantity`, `unit`, `plant`, `requester`, `required_date` (4 weeks out), and a human-readable `reason` string. In dry-run, simulates a PR number as `PR-DRY-{last-3-of-material-id}`.
6. **Build output**: Assembles the final output dict with `prs_created`, `high_priority_flags` (detailed list of critically low SKUs), and an empty `escalations` list reserved for future paging logic.
7. **Write outputs**: Saves the JSON to `outputs/`, logs the run to DB (`agent_runs` table), and records `prs_created` count and `hours_saved` (0.5 hrs per PR) to `value_tracking`.

## HITL Decision Points

- **Authority level is `low`**: The agent creates PRs automatically without human approval. No HITL gate on PR creation itself.
- **`HIGH_PRIORITY` flags** are printed to stdout and included in `high_priority_flags`. These are informational escalations intended to prompt human review — the operations planner should verify that critically low items (>50% below reorder point) are being actioned urgently.
- **`escalations` array** is always empty in the current implementation; a comment in the code marks it as a future hook to page on-call staff when more than 3 HIGH_PRIORITY items are triggered simultaneously.
- After a PR is approved in SAP, no further agent action is taken — downstream PO creation and goods receipt remain manual processes.

## Limitations

- **Dry-run only in demo context**: The mock SAP server at `localhost:3001` is a controlled test fixture; no live SAP system is connected.
- **No duplicate-PR protection against existing PRs in SAP**: The agent skips SKUs where `on_order > 0` in the inventory payload, but this relies entirely on the SAP response accurately reflecting in-flight PRs. If the API data is stale, duplicate PRs can be created.
- **Fixed 10-SKU dry-run dataset**: Only the first 10 of a potential 20 CG SKUs are represented in `DRY_RUN_INVENTORY`. The live API path is designed to handle 20.
- **No multi-plant support**: Plant is hardcoded to `CG01`. The `plant` field in the PR body falls back to `CG01` for any SKU that doesn't carry its own `plant` attribute.
- **No lead-time awareness**: Order quantity formula (`reorder_point * 2 - stock`) targets a fixed 2× reorder-point buffer regardless of actual supplier lead time.
- **`escalations` not implemented**: The paging hook is a stub.

## Example Run

```bash
python3 pilot-agents/replenishment_agent.py --dry-run
```

Condensed output (4 PRs triggered from 10 SKUs checked):

```
[2026-03-14T09:15:00] === Replenishment Agent starting (dry_run=True) ===
[2026-03-14T09:15:00] DRY-RUN: Using simulated inventory data
[2026-03-14T09:15:00] Inventory fetched: 10 SKUs
[2026-03-14T09:15:00] Triggered: CG-SKU-001 stock=120 reorder=200 pct_below=40% order_qty=280 priority=NORMAL
[2026-03-14T09:15:00]   DRY-RUN: Would POST PR for CG-SKU-001 qty=280 [NORMAL]
[2026-03-14T09:15:00] Triggered: CG-SKU-003 stock=45 reorder=180 pct_below=75% order_qty=315 priority=HIGH_PRIORITY
[2026-03-14T09:15:00]   DRY-RUN: Would POST PR for CG-SKU-003 qty=315 [HIGH_PRIORITY]
[2026-03-14T09:15:00] Triggered: CG-SKU-006 stock=30 reorder=100 pct_below=70% order_qty=170 priority=HIGH_PRIORITY
[2026-03-14T09:15:00]   DRY-RUN: Would POST PR for CG-SKU-006 qty=170 [HIGH_PRIORITY]
[2026-03-14T09:15:00] Triggered: CG-SKU-009 stock=15 reorder=75 pct_below=80% order_qty=135 priority=HIGH_PRIORITY
[2026-03-14T09:15:00]   DRY-RUN: Would POST PR for CG-SKU-009 qty=135 [HIGH_PRIORITY]
[2026-03-14T09:15:00] Checked 10 SKUs — triggered 4 PRs, 3 HIGH_PRIORITY flags

*** HIGH PRIORITY ITEMS REQUIRING ATTENTION ***
  CG-SKU-003: 75.0% below reorder point
  CG-SKU-006: 70.0% below reorder point
  CG-SKU-009: 80.0% below reorder point
```
