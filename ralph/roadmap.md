# Business Agents Platform — Epic Roadmap
Updated: 2026-03-14

---

## Completed

| Epic | Title | Status | Key Outputs |
|---|---|---|---|
| 1 | Foundation | ✅ Done | DB schema, ralph loop, multi-agent coordination, APQC taxonomy |
| 2 | Partner Pitch Deck | ✅ Done | 15-slide reveal.js deck (value chain, feature library, dashboard mockup, dev sequence) |
| 3 | Process Repository | ✅ Done | Process browser, 177 processes (CG + Pharma + FS), Excel export |
| 4 | Agent Blueprint Framework | ✅ Done | agent_blueprints table, 10 blueprints, blueprint viewer |
| 5 | Communication Framework | ✅ Done | exec-summary.html, roi-calculator.html, technical-overview.html |
| 6 | Enterprise Dashboard | ✅ Done | Static web app: blueprint cards, value chain heatmap, opportunity table |
| 7 | First Pilot Agents | ✅ Done | 3 Python agents (replenishment, demand forecast, quality CAPA) against sandbox + live dashboard |
| 8 | Client Onboarding Framework | ✅ Done | questionnaire.html, score_client.py, onboarding-checklist.html |
| 9 | Sandbox Environments | ✅ Done | Mock SAP (port 3001) + Mock MES (port 3002), 20 CG SKUs, 5 lines |
| 10 | Client Engagement Portal | ✅ Done | 131KB SPA, 5 tabs, ?client= URL param, GitHub Pages compatible |
| 11 | Agent Runtime Framework | ✅ Done | scheduler.py, notification stubs, retry/circuit-breaker, agent registry, health check :8080 |
| 12 | Financial Services Sector | ✅ Done | 71 FS processes, 36 FS capabilities, 3 FS blueprints (AML, credit, regulatory) |
| 16 | Blueprint Expansion | ✅ Done | 4 new blueprints: AP Invoice, Employee Onboarding, Sales Forecast, Regulatory Deviation |
| 17 | Pricing & Engagement Model | ✅ Done | Engagement model HTML: 3 tiers, 4 phases, time-to-value chart, FAQ |
| Feature Library | Feature Layer | ✅ Done | features table (18), blueprint_features (23 links), feature-matrix query, pitch slide |
| Viz Suite | Analytics & Visualizations | ✅ Done | 7 views: matrix, quadrant, treemap, feature-network, authority, blueprint-flow, systems-map |
| Registry | Platform Index | ✅ Done | index.html (21 tools, 4 categories) + registry.json (21 entries) |
| Sales Content | Value Narrative | ✅ Done | productivity-multiplier.html (5×), benefits-realization.html (KPI framework) |

---

## In Progress

| Epic | Title | Status | Key Outputs |
|---|---|---|---|
| 18 | Industrial Manufacturing Sector | ✅ Done | 61 MFG processes, 78 agent actions, 3 blueprints (predictive maint, quality monitor, OEE), 10 systems |
| 19 | Retail Sector | ✅ Done | 57 Retail processes, 144 agent actions, 3 blueprints (replenishment, markdown, churn), 10 systems |
| 20 | Agent Actions Coverage | ✅ Done | 800 total agent actions, 100% coverage across all 12 APQC functions |
| 21 | CG Process Expansion | ✅ Done | CG expanded from 26 → 64 processes across all 12 functions, +125 agent actions |
| 22 | Healthcare Sector | ✅ Done | 53 processes, 132 agent actions, 3 blueprints (prior auth, claims denial, nurse staffing), 10 systems |
| 23 | Energy & Utilities Sector | ✅ Done | 55 processes, 118 agent actions, 3 blueprints (grid anomaly, demand forecast, outage response), 10 systems |
| 24 | Logistics & Transportation Sector | ✅ Done | 54 processes, 106 agent actions, 3 blueprints (route optimization, freight audit, carrier performance), 10 systems |
| 25 | Telecommunications Sector | ✅ Done | 53 processes, 124 agent actions, 3 blueprints (network anomaly, churn risk, revenue assurance), 10 systems |
| 26 | Automotive Sector | ✅ Done | 55 processes, 131 agent actions, 3 blueprints (warranty triage, parts replenishment, fleet maintenance), 10 systems |
| 27 | Technology / SaaS Sector | ✅ Done | 57 processes, 118 agent actions, 3 blueprints (customer health, support triage, license optimization), 10 systems |
| 28 | Construction & Engineering Sector | ✅ Done | 55 processes, 119 agent actions, 3 blueprints (project risk, subcontractor compliance, cost variance), 10 systems |
| 29 | Public Sector / Government | ✅ Done | 45 processes, 107 agent actions, 3 blueprints (grant eligibility, permit monitor, procurement compliance), 10 systems |
| 30 | Company Size Tier Dimension | ⏳ Queued | size_fit tags on blueprints, SMB system layer, engagement model mapping, filtered views |
| 34 | Pilot Lifecycle Tracking | ✅ Done | lifecycle_stage on blueprints (blueprint→scaffolded→sandbox→validated→pilot_ready→production), blueprint viewer badges + filter, Framework 18 |
| 35 | Persona Dashboards | ✅ Done | operations.html (19KB), finance.html (25KB), compliance.html (25KB) — agent tiles, KPI bars, approval queue, click-through to agent-view.html |
| 36 | Agent-Specific View | ✅ Done | dashboards/agent-view.html (35KB, 1061 lines) — URL-param driven, SVG sparklines, run history, JSON output viewer, CAPA approval queue, lifecycle gate checklist |
| 37 | Enterprise Portfolio Dashboard | ✅ Done | dashboards/enterprise.html (43KB, generated from DB) — lifecycle funnel, 13-industry coverage table, $14.5K value realized, 12×13 function/industry heatmap, RAI pillar coverage |

---

## Queued — Near Term

### Epic 41: Persona-Driven Feature Depth
**Goal:** Transform each dashboard from a status display into a real workflow tool. Each persona has 3–5 defined jobs-to-be-done; every feature below directly serves a job. Target: all 5 core dashboards scoring ≥15/20 on the eval rubric.

**Design principle:** Don't add features — close the gap between what the persona needs to do in 30 minutes and what the dashboard currently lets them do.

---

#### Persona 1: Operations Manager — Sarah Chen
**Dashboard:** `operations.html`
**Eval score:** 12/20 → target 17/20

**Jobs-to-be-done:**
1. **Triage** (< 2 min): Know what happened overnight and what needs a decision today
2. **SKU Review** (5–15 min): Understand which SKUs are at risk, why, and what the agent recommends
3. **Informed Approval** (core workflow): Approve/reject PRs with full context, not blind
4. **Demand Signal Review** (5 min): Understand forecast trends, override if there's a promotion or known event
5. **Escalation**: Send unresolvable items to manager with auto-drafted rationale

**Features → Stories:**

- **S41-1A: Impact Narrative Header** — Replace generic KPI bar with a context-aware summary card: *"Replenishment agent ran at 6:02am — 3 SKUs below reorder point, 2 PRs pending your approval, 1 critical (Olive Oil 5L, 1.8 days cover)."* Computed from last `pilot_run` + pending recommendations. *(D1: 2→4)*

- **S41-1B: SKU Status Table** — Live table: SKU Name | Current Stock | Days Cover | Reorder Point | Status (Critical/Low/OK) | Agent Action | Decision. Sortable by days cover. Fetched from `recommendations` table + mock SAP inventory endpoint. *(D2: 3→4, D4: 2→3)*

- **S41-1C: SKU Detail Side Panel** — Click any SKU row → slide-in panel showing: 12-week demand sparkline, SMA trend line, confidence level, pending PR details (quantity, unit cost, total value, supplier, lead time, expected arrival), last CAPA if any. *(D2: 4, D5: 3→4)*

- **S41-1D: Decision Context Cards** — Replace bare Accept/Reject buttons with context-rich decision cards: "Approve PR for 500 units Olive Oil 5L @ £18.40 = £9,200. Supplier: Bonfiglio (8-day lead time). Without this: stockout in 1.8 days." + quantity modify field before approving. *(D3: 3→4)*

- **S41-1E: Forecast Override** — On demand chart, right-click a data point → "Flag as promo period / anomaly" with note field. Stored in `pilot_runs.output_json` override array. Shown as annotation marker on chart. *(D2: 4, D5: 4)*

---

#### Persona 2: Finance Controller — Michael Torres
**Dashboard:** `finance.html`
**Eval score:** 7/20 → target 15/20

**Jobs-to-be-done:**
1. **Cost Control**: See what the agents are committing spend on and approve/reject before POs are raised
2. **Cash Flow View**: Understand the timing and size of agent-recommended commitments vs. available budget
3. **ROI Tracking**: See actual vs. projected savings from agent deployment
4. **Exception Review**: Flag anomalies (unusually large POs, duplicate invoices, margin erosion)
5. **Budget Gate**: Block commitments above threshold until reviewed

**Features → Stories:**

- **S41-2A: Wire Finance to Run Theater** — Copy the `openRunDrawer` + `animateSteps` + `showRecommendations` + `decideRec` pattern from `operations.html`. Finance agents: AP Invoice (mock), Forecast Accuracy. Remove "Demo items shown for layout illustration" disclaimer. *(D2: 1→3, D3: 1→3, D4: 1→3)*

- **S41-2B: Commitment Calendar** — A 4-week mini calendar heatmap showing agent-recommended spend by day: darker = larger commitment. Clicking a day shows the PRs/POs due. Sourced from `recommendations.detail_json` + delivery lead times. *(D5: 2→4)*

- **S41-2C: Budget Gate Modal** — When a recommendation total exceeds £50K, show a gate modal before approval: "This approval commits £62,400 — 18% of remaining Q1 budget. Confirm?" with budget remaining indicator. *(D3: 1→4)*

- **S41-2D: ROI Actuals vs. Projection** — Replace static ROI card with a live chart: projected savings per agent (seeded) vs. actual hours saved from `value_tracking` table. Shows whether agents are hitting their business case. *(D1: 2→4, D4: 1→3)*

- **S41-2E: Exception Flags** — Agent automatically surfaces anomalies in the recommendation list with a red flag badge: "This PO is 40% above average for this supplier" or "Duplicate invoice pattern detected." Detail from `recommendations.detail_json.flags[]`. *(D5: 2→4)*

---

#### Persona 3: Compliance Officer — Dr. Aisha Patel
**Dashboard:** `compliance.html`
**Eval score:** 14/20 → target 18/20

**Jobs-to-be-done:**
1. **CAPA Triage**: Know which quality events need sign-off today, ranked by severity
2. **Evidence Review**: Before signing off, see the full event record, affected line, OEE impact
3. **Audit Trail**: Generate a printable/exportable record of all decisions with timestamps
4. **RAI Monitoring**: Confirm agents are operating within approved authority bounds
5. **Regulatory Calendar**: Track upcoming audit dates and agent-assisted prep status

**Features → Stories:**

- **S41-3A: Fix Button Cursor + Click Handler** — Compliance approve/review buttons currently have `cursor: default`. Fix to `cursor: pointer` + ensure `handleApproval()` POST fires correctly on click. *(D2: 2→3)*

- **S41-3B: CAPA Evidence Panel** — Click any CAPA item → side panel showing: full quality event record (line, issue type, OEE impact %, time detected), agent reasoning (what triggered this CAPA), MR number, authority level, regulatory reference (ISO clause or internal SOP). *(D5: 3→4)*

- **S41-3C: Before/After Narrative Card** — Above the CAPA queue: *"This week: 4 quality events detected. Agent auto-triaged 2 (LOW authority). 2 await your sign-off. Before agents: avg 6.2h per event. Current: 1.8h."* *(D1: 3→4)*

- **S41-3D: Export Audit Trail** — "Export Decisions" button generates a printable HTML table of all CAPA decisions: event ID, decision, decided by, timestamp, notes. Fetched from `approvals` table filtered by slug. *(D3: 4, D5: 4)*

- **S41-3E: RAI Authority Monitor** — Small panel showing: for each agent, its authority level + a count of actions taken in the last 30 days vs. the limit in the blueprint. Green if within bounds, amber if approaching, red if exceeded. *(D5: 3→4)*

---

#### Persona 4: IT Technical Lead
**Dashboard:** `it-health.html`
**Eval score:** 12/20 → target 16/20

**Jobs-to-be-done:**
1. **System Health Check**: Confirm SAP/MES integrations are live before agent runs
2. **Error Investigation**: Drill into a failed agent run to see the exact error and payload
3. **Performance Monitoring**: Track latency trends, error rates, and capacity usage over time
4. **Audit Compliance**: Confirm all agent decisions are logged and attributable
5. **Incident Response**: When an agent fails, understand blast radius and escalate

**Features → Stories:**

- **S41-4A: Auto-Refresh (30s)** — `setInterval(loadAll, 30000)` with a visible "Last refreshed: Xs ago" counter in the header. Eliminates need for manual refresh. *(D2: 2→3)*

- **S41-4B: Payload Inspector** — Expandable row in the Activity Log: click any run → shows raw JSON input sent to agent + output received, truncated at 500 chars with "Show full" toggle. *(D2: 2→4, D5: 3→4)*

- **S41-4C: Latency Trend Chart** — SVG sparkline per agent showing avg response time over last 10 runs. Red if above 5s threshold. Computed from `pilot_runs.duration_ms`. *(D4: 2→3)*

- **S41-4D: Failed Run Drilldown** — Click a failed run row → modal showing: error message, stack trace stub (mocked), which external system call failed (SAP/MES/DB), suggested fix. *(D3: 2→3)*

---

#### Persona 5: C-Suite / Enterprise Viewer
**Dashboard:** `enterprise.html`
**Eval score:** 6/20 → target 13/20

**Jobs-to-be-done:**
1. **Portfolio Pulse**: How many agents are active, what value is being realized this quarter?
2. **Decision Oversight**: How many agent recommendations have been made, approved, rejected?
3. **Expansion Signal**: Which agent categories are ready to scale? Where is the biggest untapped opportunity?
4. **Risk View**: Are any agents operating outside approved authority? Any compliance flags?

**Features → Stories:**

- **S41-5A: Live Portfolio Fetch** — Replace all hardcoded KPI values with live fetch from `/api/portfolio`. Show real lifecycle_dist counts. *(D4: 1→3)*

- **S41-5B: Decision Oversight Panel** — New section: "Agent Decisions This Month" — total recommendations made / approved / rejected / pending. Fetched from `recommendations` table aggregate. Links to Action Queue. *(D2: 1→2, D3: 1→3)*

- **S41-5C: Value Realized Live Card** — Replace static "$14.5K realized" with live fetch from `value_tracking` aggregate via `/api/portfolio`. Show trend arrow (up/down vs. last month). *(D1: 2→3, D4: 1→3)*

- **S41-5D: Expansion Readiness Flags** — For agents at `sandbox` or `validated` stage, show a "Ready to advance" flag with estimated value unlock. Click → goes to Pipeline kanban at that agent's card. *(D2: 1→3, D5: 1→3)*

---

#### Cross-Functional (Action Queue + Pipeline)

- **S41-6A: Role-Aware Action Queue** — Add "Viewing as: Operations | Compliance | Finance" filter at top of `action-queue.html`. Filters queue to show only items relevant to that persona's agents. *(Action Queue D5: 2→4)*

- **S41-6B: Pipeline Stage Gate Modal** — Add confirmation modal on Advance button: "Advancing {name} from Sandbox to Validated requires: integration test passed + compliance clearance + oversight SOP documented. Confirm?" with checklist. *(Pipeline D3: 1→3)*

- **S41-6C: Pipeline Business Impact** — Each kanban card shows estimated value unlock on advancement: "Moving to Pilot Ready unlocks est. £42K/yr savings." From `agent_blueprints.estimated_value_usd`. *(Pipeline D1: 3→4)*

---

**Story order (prioritized by eval impact):**
1. S41-1A, S41-1B, S41-1C, S41-1D (Operations SKU workflow — biggest gap to close)
2. S41-2A (Finance run theater wire — copy-paste, high impact)
3. S41-3A, S41-3B, S41-3C (Compliance evidence + narrative — almost there)
4. S41-5A, S41-5B, S41-5C (Enterprise live data — easy lifts)
5. S41-6A, S41-6B (Action Queue role filter + Pipeline gate modal)
6. S41-1E, S41-2B, S41-2C, S41-2D, S41-2E (deeper Finance + Ops)
7. S41-4A–D, S41-3D, S41-3E, S41-5D (IT depth + Compliance audit export)

---

### Epic 42: Client Profile Framework + Kimre Portal

**Goal:** Operationalise the F20 Client Profile Schema (Framework 20) by building a `clients` database table, seeding Kimre's profile as the first entry, generating a personalized client engagement portal for Kimre, and wiring the portal generator to pull from the `clients` table by slug. This creates the end-to-end pipeline from client profile → tailored deliverable.

**Frameworks it operationalises:** F20 (Client Profile Schema), F5 (Company Size Tiers), F11 (Data Readiness), F14 (Integration Complexity), F15 (Regulatory Complexity), F8 (Engagement Model Tiers).

**Stories:**

- **S42-1:** Add `clients` table to `business_agents.db` with schema: `id INTEGER PK`, `name TEXT`, `slug TEXT UNIQUE`, `size_tier TEXT` (SMB/MID/ENT), `industry_code TEXT`, `business_model_type TEXT` (ETO/MTO/MTS/Distribution/Service/SaaS), `regulatory_score INTEGER`, `integration_tier TEXT` (T1/T2/T3/T4), `data_readiness_score INTEGER`, `engagement_tier TEXT` (Discovery/Pilot/Platform), `primary_contact TEXT`, `website TEXT`, `notes_json TEXT`

- **S42-2:** Seed Kimre profile into `clients` table — slug=`kimre`, size_tier=`MID`, industry_code=`MFG`, business_model_type=`ETO`, regulatory_score=`4`, integration_tier=`T2`, data_readiness_score=`14`, engagement_tier=`Pilot`, primary_contact=`Mary Gaston`, website=`https://www.kimre.com`

- **S42-3:** Build `clients/kimre/index.html` — personalized client engagement portal for Kimre. 8-section self-contained HTML: header, executive summary (5 agents, 34 hrs/week, £190K/yr, 6-week pilot), company profile scorecard (F20 dimensions with CSS bars), ETO business model explainer, 5-agent opportunity shortlist with rank/blueprint/value/tier/authority/priority cards, recommended pilot deep-dive (Material Requisition Agent, before/after table, 6-week timeline, success metrics), persona impact (Mary Gaston + 3 other roles), engagement model tier comparison (Discovery/Pilot/Platform). ✅ Done

- **S42-4:** Build `clients/kimre/profile.json` — machine-readable F20 client profile with all 8 dimensions, full agent opportunity list with priority/blueprint/value fields, pilot recommendation, and persona roster. ✅ Done

- **S42-5:** Update `clients/portal/generate.py` (or create if not exists) to accept a `--client <slug>` argument, read the matching row from the `clients` table + the `clients/{slug}/profile.json`, and regenerate the `clients/{slug}/index.html` from a Jinja2 template. Replaces hardcoded HTML generation with data-driven pipeline.

- **S42-6:** Add client profiles to the `business-agents/browser` sales view — new "Clients" tab in the browser lists all rows from the `clients` table with name, size tier, industry, engagement tier, and a link to the client's portal HTML. Enables the sales team to access all client profiles from one place.

**Story order:** S42-1 → S42-2 → S42-4 → S42-3 (done) → S42-5 → S42-6

---

### ~~Epic 34: Pilot Lifecycle Tracking~~ ✅ Done
`lifecycle_stage` + `lifecycle_notes` on `agent_blueprints`. 3 CG pilots → sandbox, 37 others → blueprint. Blueprint viewer updated with colored stage badges + filter chips. Framework 18 (Pilot Lifecycle) added to `ralph/frameworks.md`.

---

### ~~Epic 35: Persona Dashboards~~ ✅ Done
`dashboards/operations.html` (19KB), `dashboards/finance.html` (25KB), `dashboards/compliance.html` (25KB). Shared nav bar across all 3. Operations: Sarah Chen, 2 live sandbox agents + KPI bar (23 PRs, 18.5h saved, 91.2% accuracy). Finance: Michael Torres, 3 blueprint pipeline + $420K/yr projection + demo approval queue. Compliance: Dr. Aisha Patel, live CAPA agent + 2 pending CAPA sign-offs + audit trail + RAI coverage badge. Registry: 27 entries. Index: "27 tools across 5 categories".

---

### ~~Epic 36: Agent-Specific View~~ ✅ Done
`dashboards/agent-view.html` (35KB, 1061 lines). URL-param driven (`?agent=<slug>`), all 3 sandbox agents embedded. Features: lifecycle notes info box, SVG sparklines (improving 72%→91.2% accuracy curve), run history table (success/partial/failed badges), collapsible JSON output viewer, CAPA approval queue panel (2 pending for quality-capa agent, empty for LOW authority agents), lifecycle gate checklist (green ✅ for met requirements), persona-aware back button. Registry: 28 entries. Badge: "28 tools".

---

### ~~Epic 37: Enterprise Portfolio Dashboard~~ ✅ Done
`dashboards/enterprise.html` (43KB, generated by `generate_enterprise.py`). KPI strip: 40 blueprints / 13 industries / 12 functions / 1755 actions. SVG lifecycle funnel: 37 blueprint + 3 sandbox. Industry coverage table: 13 rows, CG=sandbox all others=blueprint. Value realized: 170.6h saved, 76 PRs, 36 exceptions, $14.5K realized ($193K projected at scale). 12×13 function×industry heatmap from live DB. RAI coverage: 6 pillar cards. Registry: 29 entries. Badge: "29 tools".

---

### ~~Epic 33: Client-Facing Opportunity Prioritization Tool~~ ✅ Done
`prioritization/index.html` — 47KB, 1,227 lines. 8-slider scoring (4 value + 4 effort), live SVG 2×2 bubble plot, ranked table, JSON export, print CSS, Load Example, `?mode=internal` for epic prioritization. Added to registry + index.

---

### ~~Epic 32: Responsible AI & Governance Package~~ ✅ Done
`office-skills/outputs/responsible-ai/index.html` — 24KB, 6-pillar one-pager (Transparency, Oversight, Fairness, Privacy, Accountability, Robustness). Each pillar maps to specific platform capabilities (agent_runs, authority levels, circuit breaker, blueprint specs). Coverage summary table. Added to registry (entry 23) + index.html (Sales section, 9 tools).

---

### Epic 31: Pre-Sales Assessment Toolkit
**Goal:** Build a structured pre-sales assessment toolkit that helps consultants quickly score and qualify a prospect across all key dimensions before proposing an engagement.

**Frameworks it operationalises:** Data Readiness (F11), Integration Complexity (F14), Agent Maturity (F10), Company Size Tier (F5), Regulatory Complexity (F15), Stakeholder Personas (F12), ROI Categories (F13).

**Stories:**
- S31-1: Build `assessment/index.html` — multi-section scoring wizard: company profile, data readiness (5 dimensions), integration complexity (3 key systems), maturity target, regulatory profile
- S31-2: Auto-generate a scored one-pager output: "Readiness Score: 74/100 — Recommended: Pilot engagement"
- S31-3: Map scores to engagement model tier recommendation (Discovery / Pilot / Platform)
- S31-4: Export assessment as JSON (feeds client onboarding scorer) and PDF-printable HTML
- S31-5: Add assessment link to client onboarding framework and registry/index
- S31-6: Add frameworks.md to registry as a reference document

---

### Epic 30: Company Size Tier Dimension
**Goal:** Add SMB / MID / ENT classification across blueprints, systems, and client-facing views so the platform can be filtered and presented by company size.

**Stories:**
- S30-1: Add `size_fit` column to `agent_blueprints` (values: SMB / MID / ENT / ALL) + migrate existing 16 blueprints
- S30-2: Add `size_fit` column to `systems` table + tag all 41+ systems by typical company size
- S30-3: Add SMB-tier systems (QuickBooks, HubSpot, NetSuite, Gusto, ShipBob, Rippling) to systems table
- S30-4: Update blueprint viewer — add size filter chip (All / SMB / Mid / Enterprise)
- S30-5: Update client portal — add company size selector on Overview tab, filter blueprints and opportunities accordingly
- S30-6: Update client onboarding scorer — add company_size field to JSON profile, factor into scoring
- S30-7: Add size tier to frameworks.md reference table with engagement model mapping

---

### Epic 13: Multi-Agent Orchestration
**Goal:** Demonstrate a supervisor agent that coordinates multiple specialist agents in a pipeline.

**Concept:** Demand Forecast Agent → Replenishment Agent → Finance Approval Agent
- Supervisor reads demand forecast output
- If forecast indicates shortage, triggers replenishment agent
- If PR value > $50K, escalates to Finance Approval Agent (HIGH authority)
- Each step logs to DB with parent_run_id linking the chain

**Stories:**
- S13-1: Add parent_run_id + run_chain_id to agent_runs table
- S13-2: Build supervisor_agent.py — reads output of one agent, conditionally triggers next
- S13-3: Implement finance_approval_agent.py — creates draft approval doc, notifies human
- S13-4: Chain demo: run `python3 supervisor_agent.py --chain demand-replenishment-finance`
- S13-5: Visualize the chain run in the enterprise dashboard (Epic 6 extension)

---

### ~~Epic 14: Value Measurement Framework~~ ✅ Done
`value_tracking` table (90 seeded rows, 3 CG agents × 10 weeks × 3 metrics each). `v_value_realized` view: 170.6 hrs saved, $14.5K realized, $145K at-scale (10 agents). `record_value()` hooks in all 3 pilot agents. `business-agents/value-dashboard/index.html` (19KB, SVG sparklines, ROI estimate). Registry entry 24 added.

---

### Epic 15: RAG Knowledge Layer
**Goal:** Give agents access to process documentation, SOPs, and industry best practices via vector search.

**Concept:** Agents can retrieve context ("what's the standard lead time for CG-BEV-001?") from a local knowledge base built from process docs and historical data.

**Stories:**
- S15-1: Build document ingestor — accepts PDF/text SOPs, chunks, embeds via local embedding model
- S15-2: Vector store (SQLite + sqlite-vss or chromadb) for process documentation
- S15-3: Add `retrieve_context(query, top_k=3)` function to agent_runner.py
- S15-4: Enhance demand_forecast_agent.py to retrieve relevant business rules before forecasting
- S15-5: Demo: agent explains its reasoning including retrieved SOP citations

---

---

## Taxonomy Coverage

### Industries (13 total)

| # | Code | Industry | Processes | Blueprints | Key Systems | Status |
|---|---|---|---|---|---|---|
| 1 | CG | Consumer Goods | 64 | 3 | SAP, MES, WMS | ✅ Done |
| 2 | MFG | Industrial Manufacturing | 61 | 3 | AVEVA PI, Maximo, Opcenter, Plex | ✅ Done |
| 3 | PHARMA | Pharmaceuticals | 52 | 1 | Veeva, TrackWise, SAP | ✅ Done |
| 4 | FS | Financial Services | 71 | 3 | Temenos, Bloomberg, SWIFT | ✅ Done |
| 5 | RETAIL | Retail | 57 | 3 | Shopify, Oracle Retail, Blue Yonder, Aptos | ✅ Done |
| 6 | HEALTH | Healthcare | 53 | 3 | Epic EHR, Cerner, McKesson, Optum | ✅ Done (Epic 22) |
| 7 | ENERGY | Energy & Utilities | 55 | 3 | OSIsoft PI, GE ADMS, SAP IS-U, Itron | ✅ Done (Epic 23) |
| 8 | LOGISTICS | Logistics & Transportation | 54 | 3 | SAP TM, Blue Yonder TMS, project44, Descartes | ✅ Done (Epic 24) |
| 9 | TELECOM | Telecommunications | 53 | 3 | Ericsson OSS/BSS, Amdocs, ServiceNow Telecom | ✅ Done (Epic 25) |
| 10 | AUTO | Automotive | 55 | 3 | SAP Auto, Teamcenter PLM, CDK Global, Solera | ✅ Done (Epic 26) |
| 11 | TECH | Technology / SaaS | 57 | 3 | Salesforce, Gainsight, Zendesk, Snowflake | ✅ Done (Epic 27) |
| 12 | CONST | Construction & Engineering | 55 | 3 | Procore, Primavera, Autodesk Construction Cloud | ✅ Done (Epic 28) |
| 13 | PUBLIC | Public Sector / Government | 45 | 3 | Salesforce Gov, Tyler Technologies, ServiceNow Gov | ✅ Done (Epic 29) |

### APQC Functions (12)

| # | Function | Processes | Agent Actions | Status |
|---|---|---|---|---|
| 1 | Develop Vision and Strategy | 6 | 2 → full | 🔄 Expanding (Epic 20) |
| 2 | Develop and Manage Products and Services | 27 | 4 → full | 🔄 Expanding (Epic 20 + 21) |
| 3 | Market and Sell Products and Services | 20 | 3 → full | 🔄 Expanding (Epic 20) |
| 4 | Deliver Physical Products | 62 | 19 → full | 🔄 Expanding (Epics 18, 19, 20) |
| 5 | Deliver Services | 6 | 0 → full | 🔄 Expanding (Epic 20) |
| 6 | Manage Customer Service | 17 | 2 → full | 🔄 Expanding (Epic 20) |
| 7 | Develop and Manage Human Capital | 3 | 0 → full | 🔄 Expanding (Epics 20, 21) |
| 8 | Manage Information Technology | 4 | 0 → full | 🔄 Expanding (Epics 20, 21) |
| 9 | Manage Financial Resources | 20 | 3 → full | 🔄 Expanding (Epic 20) |
| 10 | Acquire, Construct, and Manage Assets | 0 → 15+ | 0 → full | 🔄 Seeding (Epic 18 — MFG asset mgmt) |
| 11 | Manage Enterprise Risk, Compliance, and Resiliency | 12 | 0 → full | 🔄 Expanding (Epics 20, 21) |
| 12 | Manage External Relationships | 0 → 10+ | 0 → full | 🔄 Expanding (Epic 21 — CG/Retail) |

**Achieved (Epics 18–29):** 760 processes, all 12 functions covered, 13 industries fully seeded, 40 blueprints, 1755 agent actions, 131 systems.
**Next focus:** Platform epics — Epic 30 (Size Tiers), Epic 31 (Pre-Sales Assessment), technical depth (Epics 13, 14, 15).

---

## Principles

1. **No rip and replace** — every agent reads/writes through existing system APIs
2. **Authority-first design** — every capability classified LOW/MEDIUM/HIGH before building
3. **Static-first tooling** — Python → embedded JSON → pure JS; no build toolchain required
4. **Process-grounded** — every agent maps to an APQC process code in the DB
5. **Evidence-based value** — every blueprint has estimated hrs/week saved + measurable KPIs
