# Kimre Order Notifier Agent
**Slug**: `kimre-order-notifier-agent`
**File**: `pilot-agents/kimre/order_notifier_agent.py`
**Lifecycle**: sandbox
**Last generated**: 2026-03-14 | **Last verified**: 2026-03-14

## Purpose

The Kimre Order Notifier Agent automates proactive customer communications across Kimre Inc.'s active order portfolio. Without the agent, Jordan Lee (Customer Service) must manually check each order's production milestone status, draft bespoke update emails for milestone completions, and identify and write delay notifications — a time-consuming process that, when delayed, erodes customer trust on high-value equipment orders.

The agent monitors 11 active production orders spanning 8 pipeline stages (Order Confirmed through Shipped). On each run it identifies orders that have recently reached a new milestone and drafts proactive update emails, then separately identifies delayed orders and drafts delay alert notifications with an estimated revised ship date. Milestone notifications are flagged `action: send` (auto-send eligible); delay notifications are flagged `action: review` (require Jordan or a manager to approve before sending). All drafted notifications are surfaced in the Kimre customer service dashboard.

## Inputs

- **`DRY_RUN_ORDERS`**: Hardcoded list of 11 active production orders. Each entry includes `order_id`, `customer`, `customer_email`, `product`, `order_value_gbp`, `current_milestone_idx` (0–7), `last_milestone_date`, `due_date`, `delay_status` (`on_track`, `delayed`, or `watch`), and `delay_reason` (nullable).
- **`MILESTONES`**: Fixed 8-stage list: `["Order Confirmed", "Engineering Review", "Material Procurement", "Fabrication Started", "QC Inspection", "Packing", "Ready to Ship", "Shipped"]`.
- **`--dry-run` flag**: Always dry-run only (`dry_run_mode = "--dry-run" in sys.argv or True`). No live ERP or email integration.
- **`REFERENCE_DATE`**: Hardcoded to `date(2026, 3, 13)` for deterministic delay and milestone calculations.
- **No environment variables required**.

## Outputs

Writes `pilot-agents/kimre/outputs/order_notifier_agent_run_{YYYYMMDD_HHMMSS}.json` and prints the full JSON to stdout.

```json
{
  "run_at": "2026-03-14T10:00:00",
  "agent": "kimre-order-notifier-agent",
  "dry_run": true,
  "reference_date": "2026-03-13",
  "orders_checked": 11,
  "notifications_drafted": 4,
  "delay_alerts": 2,
  "items": [
    {
      "order_id": "KIM-051",
      "customer": "Pacific Chemicals Inc",
      "customer_email": "d.park@pchem.com",
      "product": "DRIFTOR® DE-48-PP",
      "current_milestone": "QC Inspection",
      "notification_type": "milestone_reached",
      "subject": "Order KIM-051 Update — QC Inspection Reached",
      "body_draft": "Dear Pacific Chemicals Inc team,\n\nWe're pleased to update you on the status of your order KIM-051 (DRIFTOR® DE-48-PP).\n\nYour order has reached the 'QC Inspection' milestone today. Production is progressing on schedule — shipment is scheduled for 2026-03-20 (7 days).\n\nYou will receive another update when the next milestone is reached. If you have any questions, please don't hesitate to contact us.\n\nBest regards,\nJordan Lee\nCustomer Service — Kimre Inc.",
      "action": "send",
      "urgency": "low",
      "rec_type": "customer_notification"
    },
    {
      "order_id": "KIM-052",
      "customer": "Gulf Fertilizers Co.",
      "customer_email": "a.alrashid@gulfert.com",
      "product": "B-GON® ME-48-PP",
      "current_milestone": "Fabrication Started",
      "notification_type": "delay_alert",
      "subject": "Order KIM-052 — Schedule Update Required",
      "body_draft": "Dear Gulf Fertilizers Co. team,\n\nWe're writing to proactively inform you of a schedule update on your order KIM-052 (B-GON® ME-48-PP).\n\nDue to PP mesh material batch certification delayed by supplier, we are forecasting a brief delay to the original ship date of 2026-03-18...",
      "action": "review",
      "urgency": "high",
      "rec_type": "customer_notification"
    }
  ]
}
```

## Behavior

1. **Iterate active orders**: Loops over all 11 entries in `DRY_RUN_ORDERS`.
2. **Apply specific notification rules**: Certain order IDs have hardcoded notification triggers matching the dashboard spec:
   - `KIM-051` at milestone index 4 (QC Inspection) → `milestone_reached`, `action: send`
   - `KIM-052` with `delay_status: delayed` → `delay_alert`, `action: review`
   - `KIM-050` with `delay_status: delayed` → `delay_alert`, `action: review`
   - `KIM-046` at milestone index 5 (Packing) → `milestone_reached`, `action: send`
3. **General fallback logic for remaining orders**: For orders not matched by the specific rules: if `delay_status == "delayed"` and `is_schedule_behind()` returns True → `delay_alert`, `action: review`; else if the last milestone change was within 2 days (`days_since <= 2`) and `current_milestone_idx >= 4` → `milestone_reached`, `action: send`.
4. **Schedule-behind heuristic**: `is_schedule_behind()` estimates whether an order is behind pace by assuming each milestone takes ~3 days. If `days_until_due < (7 - milestone_idx) * 3`, the order is behind.
5. **Draft milestone notification**: Generates a customer email with subject `"Order {id} Update — {milestone} Reached"` and a body from Jordan Lee confirming the milestone, current ship date, and a promise to update at the next milestone.
6. **Draft delay notification**: Generates a delay alert email citing the `delay_reason`, the original ship date, and a revised estimate of `original_due + 4 days`. Body is signed by Jordan Lee and commits to a follow-up within 24 hours.
7. **Assign urgency**: Delay alerts are always `"high"`. Milestone notifications are `"medium"` if `days_to_ship <= 3`, otherwise `"low"`.
8. **Write output**: Saves JSON to `outputs/`, prints to stdout. Reports `notifications_drafted` and `delay_alerts` counts.

## HITL Decision Points

- **`action: review` (delay alerts)**: All delay notifications must be reviewed and approved by Jordan Lee or a manager before sending. The draft email includes the delay reason, revised ship date, and an apology — Jordan may need to adjust the tone or revised date estimate before sending.
- **`action: send` (milestone notifications)**: Milestone-reached emails are pre-approved for auto-send in production (no factual risk). In the current implementation they are still draft-only with no real email integration.
- **High-value delays**: `determine_urgency()` returns `"high"` for all delay alerts regardless of order value (the code path treating `order_value_gbp >= 100000` as higher priority was simplified to always return `"high"` for delays). Jordan should prioritise personal outreach for orders over £100K (e.g., KIM-049 at £195K).
- **`watch` status orders** (e.g., KIM-049, SS cert renewal in progress): These do not currently generate a notification unless the general fallback logic triggers them. Jordan should monitor these manually until a firm delay is confirmed.

## Limitations

- **Always dry-run**: The entry point forces `dry_run=True`. No real email, CRM, or ERP integration exists.
- **Hardcoded 11-order dataset**: Order list is embedded in code. No integration with Kimre's production scheduling system.
- **Hardcoded reference date**: `REFERENCE_DATE = date(2026, 3, 13)`. In production, should use `date.today()`.
- **Specific notification rules are hardcoded by order ID**: The primary notification logic for KIM-051, KIM-052, KIM-050, and KIM-046 is by explicit `order_id` matching, not generalised rule evaluation. New orders require code changes to trigger correctly.
- **Revised ship date is fixed +4 days**: The delay notification estimate adds exactly 4 calendar days to the original due date regardless of the actual delay magnitude or cause.
- **Milestone notification threshold of index ≥ 4**: The general fallback only drafts milestone notifications for QC Inspection and later stages. Earlier milestones (Order Confirmed, Engineering Review, Material Procurement) do not generate proactive updates through the fallback path.
- **No send confirmation or email delivery tracking**: The agent drafts emails only. There is no email client integration, sent-mail logging, or delivery status tracking.

## Example Run

```bash
python3 pilot-agents/kimre/order_notifier_agent.py --dry-run
```

Condensed output (4 notifications drafted from 11 orders checked):

```
[2026-03-14T10:00:00] === kimre-order-notifier-agent starting (dry_run=True) ===
[2026-03-14T10:00:00] Reference date: 2026-03-13
[2026-03-14T10:00:00] Checking 11 active orders for notification triggers...
[2026-03-14T10:00:00]   Order KIM-052 — Gulf Fertilizers Co. — milestone 3 (Fabrication Started) — status: delayed
[2026-03-14T10:00:00]     -> Drafting delay_alert (review, urgency=high)
[2026-03-14T10:00:00]   Order KIM-051 — Pacific Chemicals Inc — milestone 4 (QC Inspection) — status: on_track
[2026-03-14T10:00:00]     -> Drafting milestone_reached (send, urgency=low)
[2026-03-14T10:00:00]   Order KIM-050 — Petrochem Solutions Ltd — milestone 3 (Fabrication Started) — status: delayed
[2026-03-14T10:00:00]     -> Drafting delay_alert (review, urgency=high)
[2026-03-14T10:00:00]   Order KIM-046 — Rhine Energy GmbH — milestone 5 (Packing) — status: on_track
[2026-03-14T10:00:00]     -> Drafting milestone_reached (send, urgency=low)
[2026-03-14T10:00:00] === Run complete ===
[2026-03-14T10:00:00]   Orders checked:        11
[2026-03-14T10:00:00]   Notifications drafted: 4
[2026-03-14T10:00:00]   Delay alerts:          2
[2026-03-14T10:00:00]   Output written:        outputs/order_notifier_agent_run_20260314_100000.json
```
