# Kimre Inc. — Platform User Guide

*AI Agent Platform — Client Edition*
*Last updated: March 2026*

---

This guide is written for Kimre Inc. staff. No technical background is needed. If you can read a spreadsheet and send an email, you can use these dashboards.

---

## Who Uses Which Dashboard?

| Person | Role | Their Dashboard | Agents They Run |
|---|---|---|---|
| Alex Torres | Sales / Applications Engineer | Sales | RFQ-to-Quote Agent |
| Sam Rivera | Engineering Lead | Engineering | Material Requisition Agent (live), Quality Compliance Checker |
| Jordan Kim | Customer Service | Customer Service | Order Milestone Notifier |
| Mary Gaston | President / Owner | Executive | (receives escalations from all agents) |
| Pat Chen | QA / Compliance | Quality | Quality Compliance Checker |
| — | Strategy review | Strategy | Business Model Agent |
| — | Marketing / outreach | Marketing | Marketing Agent, Research Agent |

---

## 1. Getting Started

### What Is This Platform?

The Kimre Agent Platform is a set of web dashboards that help each person on the team do their job faster. Each dashboard is designed for one role, shows the information that person needs most, and connects to AI agents that can draft scope letters, flag material shortages, write customer notifications, and more.

Think of the agents like a very attentive assistant: they scan through data, spot things that need attention, and bring a recommendation to you. **You always have the final say.** The platform is built around a "human in the loop" model — nothing happens automatically without your approval.

### How to Access the Dashboards

Make sure someone has started the server, then open any of these links in a web browser:

| Dashboard | URL |
|---|---|
| Platform home | http://localhost:8500/clients/kimre/ |
| Sales (Alex) | http://localhost:8500/clients/kimre/sales.html |
| Engineering (Sam) | http://localhost:8500/clients/kimre/engineering.html |
| Customer Service (Jordan) | http://localhost:8500/clients/kimre/customer-service.html |
| Executive (Mary) | http://localhost:8500/clients/kimre/executive.html |
| Quality (Pat) | http://localhost:8500/clients/kimre/quality.html |
| Strategy | http://localhost:8500/clients/kimre/strategy.html |
| Marketing | http://localhost:8500/clients/kimre/marketing.html |

### Navigating Between Pages

Every dashboard has the same orange navigation bar at the top. It shows "Kimre Inc." on the left and links to all eight pages. The page you are currently on is highlighted in orange. Click any link to switch dashboards.

---

## 2. Alex Torres — Sales Dashboard

**The Sales dashboard is Alex's primary view** for managing the RFQ pipeline, running the quote drafting agent, and tracking follow-ups.

### Reading the Quote Pipeline Table

When you open the Sales dashboard, the main table shows all open RFQs and quotes. Each row is one opportunity. Here is what each column means:

- **Quote #** — the internal reference number (e.g., Q-2024-041)
- **Customer** — the company that sent the RFQ
- **Application** — what the customer is trying to do (e.g., sulfuric acid mist elimination)
- **Product Family** — which Kimre product applies (B-GON, DRIFTOR, LIQUI-NOMIX, etc.)
- **Value** — estimated deal size in pounds sterling
- **Stage** — where the quote is in the process (see badge colors below)
- **Days Open** — how many days since the RFQ arrived

**Stage badge colors:**

| Color | Stage | What it means |
|---|---|---|
| Gray | New RFQ | Just arrived, not yet scoped |
| Blue | Scoping | Alex is working on the product recommendation |
| Amber | Quote Sent | Sent to customer, waiting for response |
| Green | Won | Customer confirmed, converting to order |
| Red | Stale | No activity in more than 5 days — needs a follow-up |

Click any row to expand it and see the full detail panel: customer contact, application description, product notes, and the follow-up log.

**Sorting:** Click any column header to sort the table. Click again to reverse the order. Sorting by "Days Open" descending shows the oldest quotes at the top — a good way to start the day.

### Running the RFQ-to-Quote Agent

The RFQ-to-Quote Agent reads the application description from each new RFQ and drafts a product recommendation and scope paragraph. This typically takes 2–3 hours to do manually; the agent does it in seconds.

**Steps:**

1. Click the **"Run RFQ-to-Quote Agent"** button near the top of the Sales dashboard.
2. A run theater panel slides open showing the agent working through each RFQ.
3. When it finishes, the panel shows a summary: "X scope drafts generated."
4. Scroll down to the **Agent Recommendations** section to review each draft.

### Reviewing Agent Recommendations

Each recommendation from the RFQ-to-Quote Agent appears as a card showing:

- The customer name and application description
- The recommended product family
- A draft scope paragraph (ready to paste into a scope letter)

**For each recommendation, you have three options:**

- **Accept** — you agree with the recommendation. It is logged as approved and added to the quote record.
- **Edit** — you want to tweak the wording before accepting. A text box opens with the draft; edit it and click Save.
- **Reject** — the recommendation is wrong or not needed. It is removed from the queue.

You do not need to act on all recommendations at once. Any that you leave pending will still be there the next time you open the dashboard.

### Logging Follow-Ups

To log a follow-up for an open quote:

1. Click the quote row to open the detail panel.
2. Click **"Log Follow-Up"** at the bottom of the panel.
3. Type a short note (e.g., "Left voicemail, expecting callback Thursday").
4. Click Save.

The note is timestamped and appended to the follow-up log inside that quote's record. This replaces the sticky-note system and makes it easy to see what was said and when.

---

## 3. Sam Rivera — Engineering Dashboard

**The Engineering dashboard is Sam's production floor view.** It shows the fabrication queue, material shortage alerts, engineering change requests (ECRs), and the pre-ship QC checklist.

### Fabrication Queue

The top section shows all open production orders in a table:

- **Order #** — internal Kimre order number (e.g., KIM-047)
- **Customer** — who placed the order
- **Product** — what is being built
- **Milestone** — where fabrication is today (BOM Review, Material Check, Fabrication, QC, Packed)
- **Due Date** — promised ship date
- **Status** — on track (green), at risk (amber), or delayed (red)

Click any order row to open the milestone timeline panel, which shows each stage and whether it has been completed.

### Material Shortage Alerts

Below the fabrication queue is the **Material Shortage Widget**. This shows any materials where current stock will not cover the open order demand. Each alert row shows:

- The material name
- How many days of stock remain
- Which order is at risk
- How many days until that order ships

A red alert means the stock runs out before the order ships. An amber alert means it is close. Green means you are covered.

### Running the Material Requisition Agent (Live Pilot)

The Material Requisition Agent is the live pilot — it actually reads inventory data and creates real purchase requisition recommendations. This is the most powerful tool in the Engineering dashboard.

**Steps:**

1. Click **"Run Material Requisition Agent"** in the Engineering dashboard.
2. The run theater shows the agent scanning all open orders against stock levels.
3. When it finishes, recommendations appear for any materials that need ordering.
4. Each recommendation shows: material, quantity to order, suggested supplier, and estimated cost.

**To act on a recommendation:**

- **Approve** — sends the PR to the purchasing queue.
- **Modify** — change the quantity or supplier before approving.
- **Hold** — you want to check something first; the recommendation stays in the queue.

### Running the Quality Compliance Checker (Mock)

The Quality Compliance Checker scans open orders for cert expiry issues and spec validation concerns. It is currently running on demonstration data (not live inventory), but the workflow is fully functional.

1. Click **"Run Quality Compliance Checker"** in the Engineering dashboard.
2. Review any flags it raises (e.g., "Material batch PP-2024-12 cert expires in 8 days").
3. Accept the flag (acknowledges it) or reject it (dismisses it as not applicable).

### Interpreting the ECR Workflow

Engineering Change Requests (ECRs) are captured in the ECR section of the Engineering dashboard. Each row shows:

- **ECR #** — reference number
- **Order** — which production order it affects
- **Type** — what changed (dimension, material, connection type, delivery date)
- **Status** — Open / Pending Customer Approval / Closed
- **Days Open** — how long since the ECR was raised

Click an ECR row to open the ECR modal where you can update the status, add a note, and mark customer approval received.

### Pre-Ship QC Checklist

When an order reaches the "Packed" milestone, a QC checklist is generated automatically. The checklist lists every dimensional check, weight verification, and cert confirmation required for that specific order. Check off items as you complete them. The "Ready to Ship" button activates only when all checklist items are complete.

---

## 4. Jordan Kim — Customer Service Dashboard

**The Customer Service dashboard is Jordan's order management center.** It shows all open orders, flags delays, and provides tools for proactive customer communication.

### Reading the Order Status Table

The main table shows every open order with:

- **Order #** — Kimre order number
- **Customer** — the customer company
- **Product** — what was ordered
- **Milestone** — current fabrication stage
- **Due Date** — promised ship date
- **Delay Flag** — whether the order is behind schedule
- **Notification Sent** — whether a delay notification has been sent to the customer

Any row with a red delay flag and "No" in the Notification Sent column needs immediate attention. These are delayed orders where the customer has not yet been told.

### Delay Notification Drawer — Step-by-Step Walkthrough

The delay notification drawer is designed so that Jordan can send a professional notification to a customer in under two minutes, without drafting from scratch.

**Steps:**

1. Click a row that has a delay flag.
2. The **Delay Notification Drawer** slides open from the right side of the screen.
3. The drawer shows a pre-filled notification message including: the order number, the expected delay, the new estimated ship date, and an apology note.
4. Review the message. If it looks right, click **"Send Notification"**.
5. If the delay is serious or the customer is a key account, click **"Escalate to Mary"** instead. This forwards the situation to the Executive dashboard for Mary's review.
6. You cannot close the drawer without taking one of these two actions. This ensures every delay gets a response.
7. Once sent, the Notification Sent column updates to "Yes" and the timestamp is recorded.

**Important:** You cannot dismiss the drawer without either sending the notification or escalating. This is intentional — the goal is that every delay gets communicated before the customer calls.

### Change Request Workflow

When a customer calls or emails with a change request:

1. Click **"New Change Request"** in the Change Request section.
2. Fill in: Order #, customer name, type of change (date / address / spec / quantity), and a brief description.
3. If the change affects a specification (e.g., a dimension or material), the form automatically routes a copy to Sam's Engineering dashboard for technical review.
4. Click Submit to log the change request. The customer will see a status of "Acknowledged" until Sam or Alex reviews the impact.

### Shipping Tracker

The shipping tracker widget shows all orders in "Shipped" status with carrier, tracking number, and last scan status. Click any row to see the full tracking history. When a delivery is confirmed:

1. Find the order in the shipping tracker.
2. Click **"Confirm Delivery"**.
3. The order status updates to Closed and the delivery date is recorded.

### Generating the OTD Report

OTD stands for On-Time Delivery — the key metric Mary reviews weekly.

1. Click **"Generate OTD Report"** in the top right of the Customer Service dashboard.
2. The dashboard calculates: on-time %, number of delayed orders, average cycle time (order to ship), and lists any orders that shipped late.
3. A download button appears to save the report as a CSV file.
4. The whole process takes under a minute — compared to 45 minutes of manual Excel work.

### Running the Order Milestone Notifier

The Order Milestone Notifier agent scans all open orders and drafts proactive notifications for milestone completions (e.g., "Your order KIM-051 has entered final QC and is on track to ship Friday").

1. Click **"Run Order Milestone Notifier"**.
2. Review the drafted notifications in the Agent Recommendations section.
3. Accept each one to send it, or reject it if the milestone is not yet confirmed.

---

## 5. Mary Gaston — Executive Dashboard

**The Executive dashboard gives Mary a full business picture in under five minutes.** It is designed so she does not need to call Alex, Sam, or Jordan to know what is happening.

### Reading the KPI Strip

The top of the Executive dashboard shows five key numbers:

- **Pipeline Value** — total value of all active quotes
- **Active Orders** — how many orders are in production right now
- **OTD This Month** — on-time delivery rate as a percentage
- **Agent Hours Saved** — estimated staff hours recovered this week through agent automation
- **Decisions Pending** — how many items in the escalation queue need Mary's sign-off

If "Decisions Pending" is greater than zero, it is shown in amber as a prompt to act.

### Quote-to-Cash Funnel

Below the KPI strip is the quote-to-cash funnel. This shows how many opportunities are at each stage: RFQ Received, Scoping, Quote Sent, Negotiation, Won, and Lost. Hover over any stage bar to see the individual quotes at that stage. Click a stage to drill into the underlying quotes.

### Project Margin Table

The margin table shows all active production orders with their estimated margin. Orders are color-coded:

- Green = healthy margin (above target)
- Amber = margin at risk
- No color = margin not yet calculated

Click any order row to see the cost breakdown.

### Escalation Approval Queue

This is where Mary makes the decisions that only she can make: quotes above £100,000 and any customer escalations flagged by Jordan.

Each item in the queue shows:

- What the decision is (e.g., "Quote Q-2024-041 — £145,000 — Petrochemical application")
- Who flagged it and when
- Any relevant context (e.g., the scope letter, the delay details)

**To act on an escalation:**

- **Approve** — confirms the action (sends the quote, allows the delay exception, etc.)
- **Delegate** — assigns it back to Alex or Jordan with a note
- **Hold** — keeps it in the queue for later review

Every decision is logged with a timestamp. The audit trail is always available.

### Agent Program ROI Scorecard

The ROI scorecard shows the business case for the agent program at a glance. For each agent:

- Investment to date (setup and pilot costs)
- Hours recovered per week
- Projected annual value
- Payback progress bar (how close the agent is to earning back its cost)

This section updates as the pilot generates more data. By month three, the payback bar should show a positive return.

---

## 6. Pat Chen — Quality Dashboard

**The Quality dashboard is Pat's compliance and documentation center.** It tracks material certifications, NCRs, ship-with documentation, and the compliance calendar.

### Material Cert Tracker

The material cert tracker shows all material batches currently in use or pending for open orders:

- **Material** — name of the material (e.g., Polypropylene Mesh PP-2024-12)
- **Batch** — batch ID from the supplier
- **Cert Status** — Valid / Expiring Soon / Expired
- **Expiry Date** — when the certificate expires
- **Orders at Risk** — which open orders use this batch

Rows highlighted in red mean the cert has expired or expires before the order ships. These need action before fabrication starts.

### NCR Queue

Non-Conformance Reports (NCRs) are tracked here. Each row shows:

- **NCR #** — reference number (e.g., NCR-2024-003)
- **Order** — which production order triggered it
- **Issue** — a brief description of the non-conformance
- **Severity** — Critical / Medium / Low (shown with a colored left border)
- **Status** — Open / Corrective Action Assigned / Closed
- **Days Open** — how long since it was raised

Click any NCR row to open the detail view where you can update the status, assign a corrective action, and close it when resolved. NCRs marked Critical with more than 5 days open are shown in red as a priority.

### Ship-With Document Checklist

For each order approaching shipment, a ship-with checklist is shown. Each checklist lists all the documents required for that order:

- Certificate of Compliance
- Material Certifications (one per material batch)
- Test Reports (if applicable)
- MSDS / Safety Data Sheets

Check off each document as you collect it. The **"Ready to Ship"** button at the bottom of each checklist becomes active only when every item is checked. This prevents orders from shipping with missing documentation.

### Running the Quality Compliance Checker

The Quality Compliance Checker scans open orders for cert issues before fabrication starts.

1. Click **"Run Quality Compliance Checker"**.
2. Review the flags it raises — typically cert expiry alerts tied to specific orders.
3. **Accept** a flag to acknowledge it and add it to your follow-up list.
4. **Reject** a flag if it does not apply (e.g., the material was already replaced with a fresh batch).

Running this agent daily means you catch cert issues before Sam starts fabrication, not after.

### Compliance Calendar

The compliance calendar shows upcoming EPA and OSHA deadlines, permit renewals, and staff training due dates. Items are color-coded:

- Red — due within 7 days
- Amber — due within 30 days
- Green — more than 30 days away

Click any item to see the full details and mark it as complete when done.

---

## 7. Strategy and Marketing Dashboards

These two dashboards are used for business planning and outreach activities. They are not tied to a single named persona but are available to Mary or Alex for strategic and commercial work.

### Strategy Dashboard

The Strategy dashboard provides a view of Kimre's business model positioning using the F24 Business Model Scoring framework. Key sections:

**Business Model Scoring Panel** — shows Kimre's current position across dimensions like revenue concentration, customer dependency, and product line breadth. Each dimension has a score and a target. Click any dimension to see the detail.

**Strategic Opportunities** — a ranked list of growth opportunities with effort estimates and potential impact. These are pre-populated based on the business model assessment.

**Running the Business Model Agent:**

1. Click **"Run Business Model Agent"**.
2. The agent analyzes the scoring data and generates a list of strategic recommendations (e.g., "Expand into Power Generation applications — high fit, low competitive overlap").
3. Review each recommendation and Accept, Edit, or Reject as you would in any other dashboard.

### Marketing Dashboard

The Marketing dashboard supports trade show follow-up, installed base tracking, and prospect pipeline management.

**Trade Show Follow-Up** — after a trade show, the agent can process a contact list and draft personalized follow-up emails for each lead. Upload the contact list, run the Marketing Agent, and review the drafts before sending.

**Installed Base** — a table of existing Kimre customers with the products they use, the installation date, and the last contact date. This is the starting point for retrofit and reorder conversations.

**Prospect Pipeline** — similar to Alex's sales pipeline but focused on earlier-stage leads that have not yet submitted an RFQ.

**Running the Marketing Agent:**

1. Click **"Run Marketing Agent"**.
2. The agent scans the installed base for retrofit opportunities (products nearing end of life or where a newer product is a better fit).
3. Review the outreach recommendations and accept the ones you want to act on.

**Running the Research Agent:**

1. Click **"Run Research Agent"**.
2. Enter a company name or industry application in the prompt box.
3. The agent returns a briefing note: company size, application type, likely product fit, and suggested talking points.
4. Use the briefing note to prepare for a sales call or trade show conversation.

---

## 8. Understanding Agent Recommendations

Every agent in the Kimre platform produces recommendations that you review before anything happens. Here is how the system works.

### Urgency Colors

Each recommendation card has a colored indicator on the left edge:

| Color | Urgency | What it means |
|---|---|---|
| Red | Critical | Needs action today — a delay or stockout is imminent |
| Amber | High | Should be addressed within 24–48 hours |
| Green | Medium | No immediate risk, but worth acting on this week |
| Gray | Low | Informational — no action strictly required |

### How to Accept, Edit, or Reject

**Accept** — you agree with the agent's recommendation. The action is logged as approved. Depending on the recommendation type, this may:
- Add a note to a quote record
- Approve a purchase requisition
- Queue a customer notification to be sent

**Edit** — you want to change something before accepting. Click Edit, modify the text or quantity, and click Save. The edited version is accepted.

**Reject** — the recommendation does not apply or is wrong. It is removed from the queue. You can optionally add a note explaining why (this helps improve the agent over time).

### What Happens After You Approve

After you approve a recommendation, the platform:

1. Records the decision in the audit log with your name (or role) and a timestamp
2. Updates the recommendation status from "Pending" to "Approved"
3. Triggers any downstream actions (for example, a Material Requisition approval routes to the purchasing queue)

**Every decision is logged and cannot be un-done** — this is by design. If you approve something by mistake, flag it to Sam or Mary so they can handle it manually in the underlying system.

---

## 9. FAQ and Troubleshooting

**The dashboard says "Offline Mode" or shows sample data only.**

This means the server is not running. Ask your IT contact or the person who manages the platform to start the server. The command is:

```
cd "/Users/keith_ai/Documents/Agentic Projects/dashboards"
python3 server.py
```

Once the server is running, refresh the page and the live data will load.

---

**An agent run shows "Mock Data" or "Dry Run" in the run theater.**

All agents except the Material Requisition Agent are currently running on demonstration data, not live company data. This is intentional during the pilot phase. The recommendations are realistic but based on pre-loaded example records. The Material Requisition Agent is the only one reading live data.

---

**I accidentally accepted a recommendation I did not mean to approve.**

Contact Sam Rivera (for material or engineering recommendations) or Mary Gaston (for quotes or escalations). The decision is logged in the system, but the downstream action can still be cancelled manually in the purchasing or ERP system before it is acted upon.

---

**The delay notification drawer will not close.**

The drawer requires you to either send the notification or escalate to Mary. This is by design — the goal is to make sure every delay is communicated. If the delay is not actually a delay (e.g., the data is wrong), click Escalate and add a note explaining that the flag is incorrect. Mary or Jordan can then close it.

---

**How do I export data from a dashboard?**

- The Customer Service dashboard has a "Download CSV" button after generating the OTD report.
- The Quality dashboard allows you to export the NCR list and the ship-with checklist.
- Other dashboards do not currently have export buttons. If you need data from another section, contact the platform team.

---

**I do not see my name in the navigation bar — which dashboard should I use?**

Use the dashboard that matches your role:

- Sales / Applications Engineering → Sales dashboard (Alex's dashboard)
- Engineering / Fabrication → Engineering dashboard (Sam's dashboard)
- Customer Service / Project Coordination → Customer Service dashboard (Jordan's dashboard)
- President / Owner → Executive dashboard (Mary's dashboard)
- QA / Compliance → Quality dashboard (Pat's dashboard)
- Strategy or marketing work → Strategy or Marketing dashboards

---

*Questions or issues? Contact the platform team. This guide reflects the platform as of March 2026.*
