# CG Demand Forecast Agent
**Slug**: `cg-demand-forecast-agent`
**File**: `pilot-agents/demand_forecast_agent.py`
**Lifecycle**: sandbox
**Last generated**: 2026-03-14 | **Last verified**: 2026-03-14

## Purpose

The CG Demand Forecast Agent automates weekly demand forecasting for Consumer Goods SKUs. Without this agent, a supply chain analyst must manually pull 12 weeks of sales history from SAP for each SKU, apply a forecast model in a spreadsheet, and flag anomalies by hand — a process that takes roughly 15 minutes per SKU across a portfolio of 20+ items.

The agent serves the operations planner and supply chain analyst personas. It fits into the weekly planning cycle: on each run it retrieves demand history for up to 8 SKUs, computes a blended forecast using a simple moving average (SMA) and linear trend projection, assesses confidence, flags demand cliffs, and produces both a machine-readable JSON output and a visual HTML report. The outputs feed directly into purchasing decisions and inventory targets.

## Inputs

- **SAP Inventory API** (`GET http://localhost:3001/api/inventory`): Provides the list of SKU IDs and descriptions to iterate over. Accepts list or dict responses.
- **SAP Demand History API** (`GET http://localhost:3001/api/demand-history/{sku_id}`): Returns 12+ weeks of weekly demand data per SKU. Live API uses `{"period":…, "actual_demand":…}`; dry-run uses `{"week":…, "demand":…}`. The agent normalises both shapes.
- **`--dry-run` flag**: Bypasses all API calls. Uses `DRY_RUN_SKUS` (8 CG oil SKUs) and pre-generated `DRY_RUN_HISTORY` with deterministic synthetic demand (12 weeks each, slopes ranging from -6.0 to +8.0 units/week to simulate growth, decline, and cliff scenarios).
- **`MAX_SKUS = 8`**: Hard cap on SKUs processed per run to keep runtime bounded.
- **Hardcoded configuration**: `SAP_BASE = "http://localhost:3001"`.
- **No environment variables required**.

## Outputs

The agent writes two files per run into `pilot-agents/outputs/`:
- `demand_forecast_{YYYYMMDD_HHMMSS}.json` — machine-readable forecast data
- `demand_forecast_{YYYYMMDD_HHMMSS}.html` — styled HTML report with forecast table, top-growing SKUs section, and demand cliff alerts

It also logs to `agent_runs` in `business_agents.db` and inserts two rows to `value_tracking` (metric types: `items_processed` and `hours_saved` at 0.25 hrs per SKU).

```json
{
  "run_at": "2026-03-14T09:20:00.000000",
  "dry_run": true,
  "items_analysed": 8,
  "demand_cliffs": [
    {
      "material_id": "CG-SKU-005",
      "description": "Corn Oil 3L",
      "weeks_of_history": 12,
      "sparkline": "█▇▆▆▅▄▃▃▂▂▁ ",
      "sma_last4": 214.5,
      "slope_per_week": -6.0,
      "trend_projection": 166.0,
      "forecast_next4wk_avg": 195.1,
      "confidence": "MEDIUM",
      "cv_pct": 18.3,
      "growth_rate_pct": -9.1,
      "demand_cliff": false
    }
  ],
  "top_growing": [
    {
      "material_id": "CG-SKU-003",
      "description": "Olive Oil Extra Virgin",
      "forecast_next4wk_avg": 242.8,
      "growth_rate_pct": 12.4
    }
  ],
  "forecasts": [
    {
      "material_id": "CG-SKU-001",
      "description": "Canola Oil 5L",
      "weeks_of_history": 12,
      "sparkline": "▁▂▃▃▄▄▅▅▆▇▇█",
      "sma_last4": 228.5,
      "slope_per_week": 3.0,
      "trend_projection": 240.5,
      "forecast_next4wk_avg": 233.3,
      "confidence": "HIGH",
      "cv_pct": 8.2,
      "growth_rate_pct": 2.1,
      "demand_cliff": false
    }
  ]
}
```

## Behavior

1. **Fetch SKU list**: Calls `GET /api/inventory` to retrieve up to `MAX_SKUS` (8) SKU IDs. Falls back to `DRY_RUN_SKUS` if the API is unavailable.
2. **Fetch demand history per SKU**: For each SKU, calls `GET /api/demand-history/{sku_id}`. Normalises the response to `{"week": int, "demand": float}` records. Skips SKUs with no history data.
3. **Compute SMA (last 4 weeks)**: Averages the final 4 weeks of demand. Used as the primary short-term signal.
4. **Compute linear trend projection (last 8 weeks)**: Fits an OLS regression slope to the last 8 weeks using stdlib-only math. Projects the trend 4 weeks forward from the last observation: `trend_projection = last_demand + slope * 4`.
5. **Blend forecast**: Combines SMA and trend projection as `forecast = SMA * 0.6 + trend_projection * 0.4`. Clamps to zero.
6. **Assess confidence**: Computes the coefficient of variation (CV%) of the last 4 weeks' demand. `CV < 15%` → HIGH; `15–30%` → MEDIUM; `≥ 30%` → LOW.
7. **Calculate growth rate**: `growth_rate_pct = (forecast - SMA) / SMA * 100`.
8. **Flag demand cliffs**: Any SKU where `growth_rate_pct < -20.0` is marked `demand_cliff: true`.
9. **Generate ASCII sparkline**: Builds a block-character sparkline from the full demand history for the HTML report.
10. **Rank top 3 growers**: Sorts all forecasts by `growth_rate_pct` descending; takes top 3.
11. **Write outputs**: Saves JSON and HTML to `outputs/`, logs run to DB, records value metrics to `value_tracking`.

## HITL Decision Points

- The agent produces forecasts only — it does not place orders or change inventory targets automatically. All outputs require human review before action.
- **Demand cliff alerts** (growth rate < -20% vs last period) are surfaced prominently in the HTML report and in the `demand_cliffs` array. The supply chain planner should review these SKUs for root cause (seasonal, promotional, distribution change) before reducing reorder points.
- **LOW confidence forecasts** (CV ≥ 30%) indicate high demand variability; planners should apply safety stock uplift manually when acting on these.
- **Top growing SKUs** flag opportunities for proactive stock building or promotional alignment — decision rests with the planner.

## Limitations

- **Dry-run only in demo context**: The mock SAP server at `localhost:3001` is a controlled fixture; no live SAP data is connected.
- **Cap of 8 SKUs per run**: `MAX_SKUS = 8` means a 20-SKU CG portfolio requires multiple runs or a batching wrapper.
- **Stdlib math only, no numpy**: The linear regression is a simple OLS over up to 8 weeks; no seasonal decomposition, no exponential smoothing, no confidence intervals.
- **12-week history assumed**: The algorithm is calibrated for 12 weeks of weekly data. Fewer data points degrade trend accuracy (fewer than 8 weeks for the regression window, fewer than 4 for the SMA window).
- **No promotion or event calendar**: The forecast does not account for known upcoming promotions, holidays, or distribution changes.
- **Demand cliff threshold is hardcoded**: The -20% growth-rate threshold for cliff detection is fixed in code and cannot be configured at runtime.

## Example Run

```bash
python3 pilot-agents/demand_forecast_agent.py --dry-run
```

Condensed output (8 SKUs processed):

```
[2026-03-14T09:20:00] === Demand Forecast Agent starting (dry_run=True) ===
[2026-03-14T09:20:00] Fetched 8 SKUs; will process up to 8
[2026-03-14T09:20:00] Processing CG-SKU-001 …
[2026-03-14T09:20:00]   SMA=228.5  Forecast=233.3  Growth=+2.1%  Confidence=HIGH
[2026-03-14T09:20:00] Processing CG-SKU-002 …
[2026-03-14T09:20:00]   SMA=137.0  Forecast=130.6  Growth=-4.7%  Confidence=HIGH
[2026-03-14T09:20:00] Processing CG-SKU-003 …
[2026-03-14T09:20:00]   SMA=215.8  Forecast=242.8  Growth=+12.4%  Confidence=MEDIUM
[2026-03-14T09:20:00] Processing CG-SKU-005 …
[2026-03-14T09:20:00]   SMA=214.5  Forecast=195.1  Growth=-9.1%  Confidence=MEDIUM
[2026-03-14T09:20:00] Top growing SKUs: ['CG-SKU-003', 'CG-SKU-007', 'CG-SKU-001']
[2026-03-14T09:20:00] === Demand Forecast Agent complete (0.2s) ===

*** DEMAND CLIFF ALERTS ***
  (none in this run — no SKU exceeded the -20% threshold with default dry-run data)
```
