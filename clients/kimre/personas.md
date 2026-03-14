# Kimre Inc. — Persona Briefs & Agent Mapping
*F21 Dashboard Specification Artifact Set — completed March 2026*

---

## Agent Roster

| Rank | Agent Name | Slug | Persona Served | Demo Mode | File |
|---|---|---|---|---|---|
| 1 | Material Requisition Agent | kimre-material-requisition-agent | Engineering Lead (Sam Rivera) | Live pilot | pilot-agents/replenishment_agent.py |
| 2 | RFQ-to-Quote Agent | kimre-rfq-quote-agent | Sales/Apps Eng (Alex Torres) | Mock (dry-run only) | pilot-agents/kimre/rfq_quote_agent.py |
| 3 | Quality Compliance Checker | kimre-quality-compliance-agent | Engineering Lead + QA (Sam Rivera / Pat Chen) | Mock (dry-run only) | pilot-agents/kimre/quality_compliance_agent.py |
| 4 | Order Milestone Notifier | kimre-order-notifier-agent | Customer Service (Jordan Kim) | Mock (dry-run only) | pilot-agents/kimre/order_notifier_agent.py |
| 5 | Retrofit Reorder Agent | kimre-retrofit-reorder-agent | President + Sales (Mary Gaston / Alex Torres) | Mock (dry-run only) | pilot-agents/kimre/retrofit_reorder_agent.py |

**Note:** Agents 2–5 are mock scripts (dry-run data only, no live sandbox API calls). They demonstrate the workflow pattern and feed the run theater but do not modify real systems. Agent 1 (Material Requisition) is the live pilot.

---

## Kimre Product Reference

| Product Family | Brand Name | Application | Materials |
|---|---|---|---|
| Mist Eliminators | B-GON® | Gas-liquid separation in columns, vessels | Polypropylene mesh, stainless wire mesh, FRP framing |
| Drift Eliminators | DRIFTOR® | Cooling tower drift control | Polypropylene profiles |
| Coalescers | LIQUI-NOMIX® | Liquid-liquid separation, fog collection | Polypropylene fiber, CPVC sheeting |
| Fiber Bed Filters | — | Sub-micron mist collection | PP fiber, FRP housing |
| Scrubber Packing | KON-TANE® | Chemical scrubbing, mass transfer | Polypropylene, PVC, CPVC, ceramic |

**Customer application sectors:** Fertilizer / Petrochemical / Power Generation / Steel Pickling / Sulfuric Acid Processing

---

## P1 — Alex Torres | Sales / Applications Engineer

**Role:** Sales Engineer — handles inbound RFQs, sizes and configures products, writes scope letters, manages quote pipeline, converts approved quotes to production orders.
**Reports to:** Mary Gaston (President)
**Team:** Solo (1 sales engineer for all of North America)

### Daily Routine
| Time | Activity |
|---|---|
| 8:00–9:00 | Check email — new RFQs and customer follow-ups overnight |
| 9:00–11:30 | Work through RFQ queue — read specs, match product family, size/configure, pull technical data sheets |
| 11:30–12:00 | Respond to stale quote follow-ups (sticky note reminders) |
| 13:00–15:00 | Draft scope letters and pricing ($5K–$500K range) |
| 15:00–16:00 | Calls with customers on active quotes |
| 16:00–17:00 | Log follow-up notes, update spreadsheet pipeline |

### Top 5 Jobs-to-be-Done

| # | Job | Trigger | Current Friction | Desired Outcome | Agent Opportunity |
|---|---|---|---|---|---|
| J1 | Draft initial product recommendation + scope from raw RFQ | New RFQ arrives by email | Must manually cross-reference PDF technical manual, past similar quotes, and application notes | Product family + model recommended in < 2h with draft scope paragraph | RFQ-to-Quote Agent reads application description → recommends product → drafts scope |
| J2 | See which open quotes are stale or hot at a glance | Start of each day | Pipeline lives in Excel + email; no view of aging or urgency | One view sorted by days-in-stage showing which to act on today | Sales dashboard quote pipeline table sorted by age |
| J3 | Log follow-up touchpoints without leaving context | After customer call or email | Has to switch to spreadsheet, find row, type note | Click "Log Follow-Up" from quote row; timestamped note saved | Detail panel with follow-up log |
| J4 | Convert approved quote to production order in one click | Customer says "go ahead" | Has to re-key all quote data into ERP as a new order — 30–45 min | "Create Order" button pre-fills order form from quote data | Dashboard decision button → POST to order creation |
| J5 | Pull relevant technical data sheet or drawing for a product | During scoping or customer call | PDF manual search — 5–10 min to find right spec sheet | Per-quote "📋 Data Sheet" link opens correct product document | Static PDF links per product family in quote detail panel |

### Pain Points
1. **RFQ backlog grows faster than capacity** — 8 RFQs/day average, scoping each takes 2–3h; backlog builds up and oldest quotes stall
2. **No pipeline view** — quote status lives in email threads and a personal Excel sheet; no way to see pipeline value, win rate, or follow-up cadence at a glance
3. **Spec lookup is manual PDF search** — product selection and sizing requires hunting through PDF technical manuals; same lookup done repeatedly for similar applications

### Success Metrics
- RFQ → first quote sent < 24h
- Win rate > 30% on quoted RFQs
- Zero missed follow-ups > 5 days
- Quote → order conversion < 30 min
- Agent scope draft accepted (no major edits) > 70% of runs

### F21 Data Contract

| Endpoint | Method | Purpose | Fallback |
|---|---|---|---|
| /api/run/kimre-rfq-quote-agent | POST | Run RFQ-to-Quote Agent | 8 hardcoded RFQ results |
| /api/recommendations/pending | GET | Pending quote draft recommendations | 3 mock pending quote_draft recs |

### F21 Quality Gates
| Dimension | Target | Key requirement |
|---|---|---|
| D1 Narrative | 4 | "Alex has N RFQs awaiting scope. N quotes stale > 5 days. Agent ran: N scope drafts generated." |
| D2 Interactivity | 4 | Sort by stage/age + quote detail panel + run theater + accept/edit/reject recommendations |
| D3 HITL | 3 | Accept/reject scope draft with feedback; log follow-up action |
| D4 Data | 3 | 8–10 realistic RFQs with customer names, application descriptions, product families, £ values |
| D5 Persona | 4 | Exactly the quote pipeline view Alex would open first; no operations/compliance language |

---

## P2 — Sam Rivera | Engineering Lead / Fabrication Manager

**Role:** Receives production orders from Alex → translates into BOMs → schedules fabrication → manages material availability → handles engineering changes → signs off on pre-ship QC.
**Reports to:** Mary Gaston (President)
**Team:** 2 work cells (approximately 8–12 fabricators)

### Daily Routine
| Time | Activity |
|---|---|
| 7:30–8:00 | Walk the floor — check yesterday's WIP, morning briefing with cell leads |
| 8:00–9:30 | Review new production orders — create or review BOMs |
| 9:30–11:00 | Check material availability against open order BOM requirements |
| 11:00–12:00 | Handle engineering change requests (email threads with customers/Alex) |
| 13:00–14:30 | Update fabrication schedule — sequence orders by due date and capacity |
| 14:30–16:00 | Pre-ship QC checks (dimensional, weight, cert confirmation) |
| 16:00–17:00 | Address material shortages — contact suppliers or flag to Mary |

### Top 5 Jobs-to-be-Done

| # | Job | Trigger | Current Friction | Desired Outcome | Agent Opportunity |
|---|---|---|---|---|---|
| J1 | Create accurate BOM from customer drawing | New production order received | Customer specs often non-standard (IPS/metric mix, non-standard connection sizes); BOM built manually in Excel | BOM created in < 2h with standard items auto-populated and non-standard items flagged | Material Requisition Agent identifies BOM gaps → flags material needs |
| J2 | See fabrication capacity vs. load this week and next | Every morning | Fabrication schedule is whiteboard + spreadsheet; no capacity view vs. order demand | 2-week capacity heatmap showing orders vs. capacity per day | Engineering dashboard capacity heatmap |
| J3 | Know if any material will stock out before an order ships | Before starting fabrication | Material shortage found during fabrication = production delay + emergency supplier call | Alert: "Material X has 1.8 days cover vs. Order KIM-047 ships in 5 days" | Material Requisition Agent → shortage widget with PR recommendations |
| J4 | Log and track engineering change requests through resolution | Customer or Alex sends change request | Change requests tracked in email threads; no structured status or history | Structured ECR form with status, revision date, customer notified Y/N, sign-off | ECR modal in engineering dashboard |
| J5 | Generate a pre-ship QC checklist from the order spec | Order reaches "Packed" milestone | QC is a paper form filled out from memory; spec-specific requirements missed | Auto-generated checklist per order: dimensional tolerances, cert confirmed, customer requirements | Quality Compliance Checker → QC checklist output |

### Pain Points
1. **Material shortages found during fabrication** — BOM-to-material check happens mentally or not at all; shortages discovered at fabrication start, causing delays and emergency orders
2. **Engineering changes tracked in email threads** — no structured status; changes get lost; customer approval not formally captured; revision history is "search my email"
3. **Non-standard customer specs** — many orders use non-standard dimensions (customer uses IPS when Kimre works in metric, or specifies a non-standard connection type); each requires manual translation and a spec interpretation decision

### Success Metrics
- BOM accuracy > 98% (no fabrication errors from BOM mistakes)
- Zero stockout-caused fabrication delays
- Engineering change closed < 48h from receipt
- Pre-ship QC pass rate > 95% first attempt
- Material Requisition Agent: 0 manual PRs needed (agent catches all shortages)

### F21 Data Contract

| Endpoint | Method | Purpose | Fallback |
|---|---|---|---|
| /api/run/kimre-material-requisition-agent | POST | Run Material Requisition Agent (live pilot) | 3 hardcoded PR recommendations |
| /api/run/kimre-quality-compliance-agent | POST | Run Quality Compliance Checker (mock) | 2 hardcoded compliance flags |
| /api/recommendations/pending | GET | Pending material/QC recommendations | 4 mock pending recs |

### F21 Quality Gates
| Dimension | Target | Key requirement |
|---|---|---|
| D1 Narrative | 4 | "Sam has N orders pending BOM. N material shortages vs. open orders. Agent recommends N PRs." |
| D2 Interactivity | 4 | Fabrication queue + milestone panel + material shortage widget + 2 run theaters + ECR modal + QC checklist |
| D3 HITL | 4 | Dual run theater (both agents), approve/modify/hold PRs, ECR sign-off, QC item checkboxes |
| D4 Data | 3 | 8–12 realistic production orders with customers, products, milestones, material status |
| D5 Persona | 4 | Engineering/fabrication language throughout; ETO project-order model; no SKU/replenishment language |

---

## P3 — Jordan Kim | Customer Service / Project Coordinator

**Role:** Monitors all open orders for milestone progress → sends proactive delay notifications → processes change requests → confirms deliveries → generates weekly OTD report for Mary.
**Reports to:** Mary Gaston (President)
**Team:** Solo

### Daily Routine
| Time | Activity |
|---|---|
| 8:00–8:30 | Check order dashboard — identify any new delays or milestones reached overnight |
| 8:30–9:30 | Draft and send delay notifications (reactive today, goal is proactive) |
| 9:30–10:30 | Process change requests received yesterday — route spec changes to Sam |
| 10:30–11:30 | FedEx/UPS tracking check for shipped orders — confirm delivery, close order |
| 13:00–14:30 | Customer calls — status updates, escalations, new change requests |
| 14:30–16:00 | Log communication notes per order |
| 16:00–17:00 | Escalate stuck orders to Mary; update weekly OTD tracking sheet |

### Top 5 Jobs-to-be-Done

| # | Job | Trigger | Current Friction | Desired Outcome | Agent Opportunity |
|---|---|---|---|---|---|
| J1 | Know every open order's current fabrication milestone and expected ship date | Start of each day | Order status spread across ERP + whiteboard + email; no single view | One table: all open orders, current milestone, days until due, any delay flag | Customer service dashboard order status table |
| J2 | Send delay notifications before customers call — proactively | When a delay is detected | Delays communicated reactively; customers call first | Agent flags delay → pre-fills notification → Jordan reviews/sends → logged | Delay notification drawer: pre-filled, mandatory send/escalate, auto-logged |
| J3 | Process change requests cleanly | Customer sends change request | Email chains; no structured capture of type, impact, or acknowledgement | Structured form: type (date/address/spec/qty), impact assessment, ack tracking | Change request panel with routing to Sam for spec changes |
| J4 | Confirm delivery and formally close order | Carrier marks "Delivered" | Manual FedEx/UPS lookup per order; no consolidated view | Shipping widget shows carrier + tracking + status per shipped order | Shipping tracker widget per order in shipped status |
| J5 | Generate weekly OTD report for Mary in < 15 min | Every Friday | Takes 45 min: pull ERP data, build Excel, calculate metrics manually | "Generate Report" button → on-time %, delayed count, avg cycle time, downloadable CSV | OTD report generator in customer service dashboard |

### Pain Points
1. **Reactive delay communications** — delays discovered when customers call, not when delay first occurs; puts Jordan on the defensive and damages customer trust
2. **No consolidated order view** — order status requires checking ERP screen, whiteboard in the shop, and email; no way to see all 11 orders and their status in one place
3. **OTD report is 45 minutes of manual Excel work** — every Friday: pull ERP extract, calculate metrics, format for Mary; a pure administrative task with no value added

### Success Metrics
- 100% proactive delay notification rate (customer never calls first about a delay)
- OTD > 90%
- Change request acknowledged to customer < 4h
- Weekly OTD report generated in < 15 min
- Zero delivered orders without formal close confirmation

### F21 Data Contract

| Endpoint | Method | Purpose | Fallback |
|---|---|---|---|
| /api/run/kimre-order-notifier-agent | POST | Run Order Milestone Notifier | 4 hardcoded notification drafts |
| /api/recommendations/pending | GET | Pending customer notification recs | 2 mock pending notifications |

### F21 Quality Gates
| Dimension | Target | Key requirement |
|---|---|---|
| D1 Narrative | 4 | "Jordan: N open orders. N delayed with no notification sent — act now. OTD this month: N%. Agent ran: N notifications generated." |
| D2 Interactivity | 4 | Order table + timeline panel + delay notification drawer + change request form + shipping widget + OTD report |
| D3 HITL | 4 | Delay notification: mandatory Send/Escalate (cannot dismiss without action); change request routing; accept/reject agent notifications |
| D4 Data | 3 | 11 realistic orders with customers, products, milestones, notification status, shipping details |
| D5 Persona | 4 | Customer-facing language; ETO project-order model; "Jordan" named in narrative |

---

## P4 — Mary Gaston | President / Owner

**Role:** Runs the business — sees the full picture, approves high-value decisions, tracks agent program ROI, monitors key accounts.
**Reports to:** Board / herself (privately held)
**Team:** All of Kimre (21–50 employees)

### Daily Routine
| Time | Activity |
|---|---|
| 8:00–8:30 | Quick business health check — pipeline, backlog, any red flags |
| 8:30–9:30 | Review decisions needing her sign-off (quotes > £100K, escalated delays, agent program decisions) |
| 10:00–11:30 | Customer relationship calls (key accounts, large opportunities) |
| 13:00–14:00 | Operations review with Sam or Jordan as needed |
| 14:00–16:00 | Sales discussions / business development |
| 16:00–17:00 | Review agent program status — weekly metrics, next decisions |

### Top 5 Jobs-to-be-Done

| # | Job | Trigger | Current Friction | Desired Outcome | Agent Opportunity |
|---|---|---|---|---|---|
| J1 | Know business health at a glance (pipeline, backlog, OTD) | Every morning | No single dashboard; requires calling Alex, Sam, and Jordan for updates | One KPI strip + narrative covering pipeline value, active orders, OTD rate, and agent hours saved | Executive dashboard KPI strip + impact narrative |
| J2 | Approve high-value or high-risk agent decisions | Alert from Alex/Jordan | Email or in-person escalation; no structured decision record | Escalation queue showing context + decision buttons + audit trail | Executive dashboard escalation queue (quotes > £100K, delay > 5 days) |
| J3 | Track agent program ROI vs. pilot investment | Monthly or before board meeting | No tracking; investment was ~£8K; unclear what value is being generated | Agent program scorecard: investment vs. hours recovered vs. projected annual value | Agent ROI scorecard per agent with payback progress bar |
| J4 | Identify which customers are growing vs. at-risk | Quarterly account reviews | Requires pulling ERP data, calling Jordan for open orders, checking Alex's pipeline | Key account cards with YTD revenue, open orders, delayed flag, growth trend | Key account heat map (10 cards, colored by health) |
| J5 | Prioritize which agent to expand next | After each agent pilot phase | No framework for this decision; goes on gut + what team asks for | Agent roadmap with value estimate per agent + readiness criteria | Agent roadmap cards with "Advance to Next Phase" buttons |

### Pain Points
1. **No real-time business view** — business health requires asking three people; by the time Mary has the picture, the day is half over
2. **No agent program tracking** — the pilot investment (~£8K) has been made but there's no formal tracking of hours saved, errors avoided, or value realized vs. the business case
3. **Escalations come by email or in person** — high-value decisions (quotes > £100K, customer escalations) arrive ad hoc; no structured queue with context attached

### Success Metrics
- Full business review < 5 min on executive dashboard
- No surprise late orders (100% proactive notification before Mary hears from a customer)
- Agent program positive ROI by month 3
- All > £100K quotes reviewed before sending
- Know which agent to advance next based on data, not gut

### F21 Data Contract

| Endpoint | Method | Purpose | Fallback |
|---|---|---|---|
| /api/recommendations/pending | GET | Escalation queue items | 2 hardcoded escalation items |
| /api/runs/kimre-rfq-quote-agent | GET | Recent agent run history | Hardcoded last 5 runs |

### F21 Quality Gates
| Dimension | Target | Key requirement |
|---|---|---|
| D1 Narrative | 4 | "This week: N new RFQs (£Xk), N quotes sent, N order won (£Xk). Agent saved Xh. N decisions awaiting approval." |
| D2 Interactivity | 4 | Quote-to-cash funnel + margin table + key account cards + agent scorecard + escalation queue + agent roadmap |
| D3 HITL | 3 | Escalation approve/delegate/hold; agent "Advance to Next Phase" button |
| D4 Data | 3 | 10 realistic key accounts; 5 agent scorecards with realistic ROI numbers |
| D5 Persona | 4 | Executive/owner language; business-level KPIs not operations detail; "Mary" named in narrative |

---

## P5 — Pat Chen | QA / Compliance (Fictional)

**Role:** Manages material certifications, EPA/OSHA documentation, customer quality records, non-conformance reports (NCRs). Ensures every order ships with correct documentation.
**Reports to:** Sam Rivera (Engineering Lead)
**Team:** Solo (shared with Sam's team)

### Daily Routine
| Time | Activity |
|---|---|
| 8:00–9:00 | Process incoming material certs from suppliers — log against batch records |
| 9:00–10:30 | Review open NCRs — update status, assign corrective actions |
| 10:30–12:00 | Prepare ship-with documentation for this week's shipments |
| 13:00–14:30 | Respond to customer quality audit questionnaires / cert requests |
| 14:30–16:00 | Compliance calendar review — upcoming EPA/OSHA deadlines, training due |
| 16:00–17:00 | Pre-fabrication spec validation for upcoming orders (vs. EPA chemical resistance) |

### Top 5 Jobs-to-be-Done

| # | Job | Trigger | Current Friction | Desired Outcome | Agent Opportunity |
|---|---|---|---|---|---|
| J1 | Confirm all materials have valid certs before fabrication starts | Production order received by Sam | Cert lookup is manual — search folder by material + batch; expiry dates tracked in Excel | Alert: "Order KIM-047 uses Polypropylene Batch PP-2024-12 — cert expires in 8 days — action required" | Quality Compliance Checker → cert expiry alert per order |
| J2 | Track NCRs from open to closed | Non-conformance detected in QC or field | NCR tracked in Word document + email thread; no status view; resolution is informal | Structured NCR queue: number, order, issue, severity, status, days open, responsible | NCR queue table in quality dashboard |
| J3 | Prepare ship-with documentation for each shipment | Order reaches "Packed" milestone | Manual checklist: collect cert of compliance, material certs, test reports, MSDS — each from different folders | Per-order ship-with checklist: required docs listed, checkboxes, "Ready to Ship" confirmation | Ship-with document checklist in quality dashboard |
| J4 | Respond to customer quality audit questionnaires | Customer sends quality audit request | Gather answers from Sam, Alex, multiple documents; takes 1–2 days | Standard quality questionnaire template pre-populated from company data | (Future agent) |
| J5 | Monitor EPA/OSHA compliance schedule | Ongoing (dates approach) | Compliance deadlines tracked in personal calendar; risk of missing permit renewal or training | Compliance calendar: upcoming EPA/OSHA reviews, training due, permit renewals — color-coded | Compliance calendar in quality dashboard |

### Pain Points
1. **Material cert tracking is manual and fragmented** — certs stored in folders by supplier; no link to which order or batch they cover; expiry tracking is a separate Excel file not connected to the production schedule
2. **NCRs are informal** — non-conformances discovered in QC or reported by customers are tracked in email; no formal NCR number, no structured status, no escalation path
3. **Ship-with documentation takes 30–45 min per order** — collecting all required documents (cert of compliance, material certs, MSDS) from different folders; risk of missing a required document and having a shipment held at the customer

### Success Metrics
- Zero fabrication starts with expired material certs
- NCR closed < 5 business days (medium severity)
- Ship-with documentation complete for 100% of shipments before pickup
- Zero EPA/OSHA compliance deadline misses
- Quality Compliance Checker: catches cert issues before fabrication starts (not after)

### F21 Data Contract

| Endpoint | Method | Purpose | Fallback |
|---|---|---|---|
| /api/run/kimre-quality-compliance-agent | POST | Run Quality Compliance Checker | 2 hardcoded compliance flags |
| /api/recommendations/pending | GET | Pending compliance recommendation items | 2 mock pending NCR/cert recs |

### F21 Quality Gates
| Dimension | Target | Key requirement |
|---|---|---|
| D1 Narrative | 3 | "Pat: N materials pending certs. N open NCRs. N orders ship this week — N doc checklists complete." |
| D2 Interactivity | 3 | Material cert tracker + NCR queue + ship-with checklist + compliance calendar + run theater |
| D3 HITL | 3 | Accept/flag cert alerts; NCR status updates; ship-with doc confirmation |
| D4 Data | 3 | Realistic material batches with cert status; 3–5 open NCRs; 2–3 shipments this week |
| D5 Persona | 4 | QA/compliance language; cert and NCR terminology; "Pat" named in narrative |
