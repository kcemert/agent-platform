# Business Agents Platform — Implementation Plan

**Project**: AI Agent Deployment Platform for Mid-Market Industrial Manufacturers
**Vision**: A commercial platform where autonomous agents monitor operations, generate recommendations, and execute approved actions — with human-in-the-loop oversight — deployed across 10+ active clients generating measurable ROI.
**Current Stage**: Foundation + first client (Kimre) at ~1-2% of full commercial scale

**Progress Tracking**: See `dashboards/progress.html` (live) and `docs/status.json` (doc coverage)
**Architecture Reference**: `docs/architecture.html`
**Client Intelligence**: `memory/kimre.md`

---

## Modification Log
| Date | Change | By |
|------|--------|----|
| 2026-03-14 | Initial plan created from 72-epic history | Orchestrator |

---

## Phase 1: Foundations
*Infrastructure that everything else depends on. Target: production-grade, monitored, multi-tenant.*

### Task 1.1 – Database Schema Stabilization
**Objective:** Finalize and formally document all DB tables, views, and indexes as production-ready
**Output:** Schema documentation in `docs/`, all seeders idempotent, migration strategy defined
**Status:** 🟡 In Progress (schema stable, documentation partial)
**Guidance:** Schema in `business-agents/business_agents.db`. Views: v_process_full, v_opportunity_matrix, v_capability_matrix, v_blueprint_summary, v_run_history. Key gap: no formal migration strategy for schema changes.

### Task 1.2 – Framework Registry Completion
**Objective:** All 24 frameworks (F1–F24) fully documented with purpose, key dimensions, worked examples, and linked artifacts
**Output:** `ralph/frameworks.md` complete — every framework has ≥1 worked example from a real client scenario
**Status:** 🟡 In Progress (26 frameworks exist (F25/F26 added 2026-03-14), examples sparse)
**Guidance:** Current file at `ralph/frameworks.md`. F22/F23/F24 added most recently. Kimre is the primary worked example source.

### Task 1.3 – Sandbox API Coverage Expansion
**Objective:** SAP (3001) and MES (3002) mocks cover all endpoints actually called by Kimre and MFG agents — not just CG agents
**Output:** All Kimre agents can run against live sandbox (not dry-run only), test suite passes
**Status:** 🔴 Not Started
**Guidance:** Current mocks in `sandbox-systems/`. Kimre agents use DRY_RUN_* data exclusively. Depends on Task 3.2 (Kimre agent specs finalized).

### Task 1.4 – Agent Runtime Production Hardening
**Objective:** Scheduler, retry, circuit-breaker, health check running in production with monitoring and alerting
**Output:** Runtime runs 24/7, restarts on failure, sends alerts on circuit break, health endpoint monitored externally
**Status:** 🔴 Not Started (components built, not production-deployed)
**Guidance:** Components in `agent-runtime/`. All 5 built in Epic 11. Need: process supervision (supervisord or systemd), external health monitoring, alert integration.

### Task 1.5 – Server & Deployment Hardening
**Objective:** Flask server production-grade: authentication, HTTPS, CI/CD pipeline, all routes stable
**Output:** Server deployed with auth layer, CI/CD auto-deploys on push, zero manual deploy steps
**Status:** 🔴 Not Started
**Guidance:** Current: Flask on :8500, manual GitHub Pages deploy, no auth. clients/ route fixed 2026-03-14. docs/ route added 2026-03-14.

---

## Phase 2: Intelligence
*The knowledge layer — process taxonomy, blueprints, scoring. Target: validated against real outcomes.*

### Task 2.1 – Blueprint Quality Validation
**Objective:** All 40 blueprints have real-world financial parameters, case evidence, and validated ROI estimates
**Output:** Each blueprint enriched with: typical implementation cost, year-1 value estimate, 1 real case reference
**Status:** 🔴 Not Started
**Guidance:** 40 blueprints in `agent_blueprints` table. Currently placeholder values. Kimre blueprints (rfq-quote, quality-compliance etc.) are most mature — use as template for enriching others.

### Task 2.2 – Feature Links Completion
**Objective:** All 40 blueprints linked to relevant features (currently only 23/40 have links)
**Output:** `blueprint_features` table complete — every blueprint has ≥1 feature link
**Status:** 🔴 Not Started
**Guidance:** Run `python3 business-agents/query.py feature-matrix` to see current coverage. `seed_features.py` has 23 existing links to extend.

### Task 2.3 – Opportunity Scoring Calibration
**Objective:** v_opportunity_matrix scores calibrated against real client outcomes, not just additive action counts
**Output:** Scoring methodology documented, scores validated against Kimre use cases
**Status:** 🔴 Not Started
**Guidance:** Current scoring: sum of feasibility + value from process_agent_actions. Needs: weighting by industry/company-size, validation against actual agent value delivered.

---

## Phase 3: Agents
*The automation layer. Target: 3 CG agents at production, Kimre agents at pilot_ready, 10+ generic agents.*

### Task 3.1 – CG Agents: sandbox → pilot_ready
**Objective:** cg-replenishment-pr-agent, cg-demand-forecast-agent, cg-quality-capa-agent promoted from sandbox to pilot_ready
**Output:** All 3 agents pass validation criteria: correct output schema, HITL path tested, error handling verified, lifecycle_stage updated in DB
**Status:** 🔴 Not Started (3 agents at sandbox, zero at pilot_ready)
**Guidance:** Validation criteria from Framework 18 (Pilot Lifecycle). Agents in `pilot-agents/`. Update lifecycle_stage via `business-agents/query.py`.

### Task 3.2 – Kimre Agents: dry-run → validated
**Objective:** All 7 Kimre agents (rfq-quote, quality-compliance, order-notifier, retrofit-reorder, marketing, research, business-model) running against live Kimre data scenarios, not just DRY_RUN
**Output:** Each agent produces correct output against realistic Kimre test data, HITL path confirmed, lifecycle_stage = validated
**Status:** 🔴 Not Started
**Guidance:** Agents in `pilot-agents/kimre/`. All currently use hardcoded DRY_RUN_* data. Depends on Task 1.3 (sandbox coverage).

### Task 3.3 – Generic Agent Library Expansion
**Objective:** 10+ generic agents covering all major use cases, each with --client-profile flag, dry-run, server-wired, documented
**Output:** Additional agents added for: inventory/MTS management, customer service notification, compliance reporting
**Status:** 🟡 In Progress (9 of target 10+ built)
**Guidance:** Existing: replenishment, demand-forecast, quality-capa, marketing, research, business-model, mfg-maintenance, ap-invoice, orchestrator. Pattern: each agent reads `--client-profile <path>`.

### Task 3.4 – HITL Coverage Hardening
**Objective:** Every agent output enforces HITL at the code level — no agent can execute without going through approval path
**Output:** HITL enforced programmatically in server.py, audit log complete for every decision
**Status:** 🟡 In Progress (HITL in dashboards, not enforced in server)
**Guidance:** `approvals` and `recommendations` tables exist. Need: server.py to block execution status update until approval recorded.

---

## Phase 4: Interfaces
*Dashboards and persona views. Target: used daily by client staff, real-time, role-based access.*

### Task 4.1 – Platform Dashboard F19 Scoring
**Objective:** All 8 platform dashboards formally scored against F19 rubric (target ≥16/20 each)
**Output:** Score table in `docs/`, dashboard improvements logged per low-scoring dimension
**Status:** 🔴 Not Started
**Guidance:** F19 rubric in `ralph/frameworks.md` — 5 dimensions: Narrative, Interactivity, HITL, Data, Persona Fit (1–4 each). 8 dashboards: operations, finance, compliance, it-health, enterprise, pipeline, action-queue, eval.

### Task 4.2 – Kimre Dashboards Client-Ready
**Objective:** All 9 Kimre persona dashboards (including strategy+marketing) scoring ≥16/20, nav consistent across all pages
**Output:** F19 scores documented, nav verified on all 9 pages, client can use independently
**Status:** 🟡 In Progress (9 dashboards built, F19 not formally scored)
**Guidance:** Nav updated 2026-03-14 to include Strategy + Marketing on all pages. Pages: index, strategy, marketing, sales, engineering, customer-service, executive, quality, tools/index.

### Task 4.3 – Component Library Completion
**Objective:** COMPONENTS.md documents every reusable component used across all platform + Kimre dashboards
**Output:** All components (including newer ones from strategy/marketing dashboards) documented with HTML+JS recipes
**Status:** 🟡 In Progress (13 components documented, newer components missing)
**Guidance:** `dashboards/COMPONENTS.md`. Gap: components introduced in strategy.html, marketing.html not yet added.

### Task 4.4 – Real-Time Dashboard Updates
**Objective:** Dashboard data refreshes without manual page reload — WebSocket or SSE for live agent run status
**Output:** Run theater shows live agent progress, KPI strips auto-refresh every 60s
**Status:** 🔴 Not Started
**Guidance:** Currently: all data fetched on page load. server.py would need SSE endpoint. Operations.html is primary candidate for first real-time update.

---

## Phase 5: Tools
*Client-facing interactive artifacts. Target: clients use tools independently, output feeds agent workflows.*

### Task 5.1 – Tools Live Data Integration
**Objective:** Spec-gen, RFQ intake, business-case calculator connected to live data — not static demo data
**Output:** Tools pull from server API where relevant, output can be saved and fed into agent workflows
**Status:** 🔴 Not Started
**Guidance:** Tools in `clients/kimre/tools/`. Currently all demo data. Target: spec-gen output → triggers rfq-quote-agent. Business case → saves to value_tracking table.

### Task 5.2 – Intro Deck Template Extraction
**Objective:** Generic intro deck template created so any client gets a branded deck without building from scratch
**Output:** `office-skills/templates/intro-deck-template.html` with placeholder variables, generator script
**Status:** 🔴 Not Started
**Guidance:** Kimre intro deck at `clients/kimre/intro-deck.html`. Fixed blank-screen bug 2026-03-14 (missing html/body height, pixel dimensions for reveal.js).

---

## Phase 6: Data Hydration
*Making the data real. Target: production run history, validated financials, live client records.*

### Task 6.1 – Agent Run History Population
**Objective:** pilot_runs table has ≥3 months of realistic run history (backfilled or live), enabling trend charts
**Output:** Run history visible in dashboards, sparklines show real trends not empty states
**Status:** 🔴 Not Started
**Guidance:** `pilot_runs` table exists. Currently ~0 rows from real runs. Option: backfill realistic history OR run agents on schedule for 1 month before launch.

### Task 6.2 – Value Tracking Baseline
**Objective:** value_tracking table has before/after metrics for each Kimre agent use case
**Output:** Executive dashboard ROI section shows real data, not hardcoded estimates
**Status:** 🔴 Not Started
**Guidance:** `value_tracking` table + `v_value_realized` view from Epic 14. `value-dashboard/` exists. Need: Kimre-specific baseline measurements.

### Task 6.3 – Client Records Completion
**Objective:** All Kimre contacts, products, installed base accounts, and order history in DB — not just profile.json
**Output:** DB-driven client records enable agent personalization without hardcoded DRY_RUN data
**Status:** 🟡 In Progress (4 Kimre contacts in DB, no products/orders/installed base)
**Guidance:** `contacts` table has 4 Kimre stakeholders. Need: products table, installed_base table, order_history table — or extend existing schema.

---

## Phase 7: Clients
*Active engagements. Target: 10+ clients at platform tier, daily active use, documented case studies.*

### Task 7.1 – Kimre: Full Production Deployment
**Objective:** Kimre using platform daily — agents running on schedule, recommendations reviewed in dashboards, ROI tracked
**Output:** Kimre staff using dashboards independently, agents running 2× weekly minimum, value tracked
**Status:** 🔴 Not Started (all infrastructure built, no live deployment)
**Guidance:** All Kimre infrastructure built (9 dashboards, 7 agents, 9-tab portal, tools). Gap: agents in dry-run only, no scheduled runs, no live Kimre data integration.

### Task 7.2 – PrecisionParts: Portal Depth
**Objective:** PrecisionParts portal reaches Kimre-equivalent depth (persona dashboards, tools, agents)
**Output:** ≥3 persona dashboards, ≥1 pilot agent, tools deployed, value chain tabs in portal
**Status:** 🔴 Not Started (portal shell only)
**Guidance:** Portal at `clients/precisionparts/`. profile.json complete. Use 8-step replication playbook from `memory/kimre.md`. MFG/MTS model — different agent set than Kimre.

### Task 7.3 – MeridianBank: Portal Depth
**Objective:** MeridianBank portal reaches Kimre-equivalent depth
**Output:** ≥3 persona dashboards, ≥1 pilot agent (AML Alert Triage candidate), tools deployed
**Status:** 🔴 Not Started (portal shell only)
**Guidance:** Portal at `clients/meridianbank/`. FS industry, regulatory score 5/5. AML Alert Triage agent (fs-aml-alert-triage blueprint) is the natural pilot candidate.

### Task 7.4 – Replication Playbook Validation
**Objective:** 8-step client onboarding playbook tested and validated against ≥1 new client (not Kimre)
**Output:** Playbook refined from real use, documented time per step, new client onboarded in <4h
**Status:** 🔴 Not Started
**Guidance:** 8-step playbook in `memory/kimre.md`. Steps 5–6 most automated. Steps 1–4 require ~4h analyst time per client.

### Task 7.5 – Third New Client Acquisition
**Objective:** Identify and onboard a 4th client using the validated replication playbook
**Output:** New client profile.json, portal created, engagement tier agreed
**Status:** 🔴 Not Started
**Guidance:** Depends on Task 7.4. Target profile: MID tier, MFG or FS industry, regulatory score 2–4, data readiness ≥3.

---

## Phase 8: Go-to-Market
*Commercial readiness. Target: repeatable sales motion, self-serve onboarding, published references.*

### Task 8.1 – Sales Playbook Formalization
**Objective:** Discovery → Pilot → Platform flow documented as a step-by-step playbook with scripts, objection handling, and timing
**Output:** `office-skills/outputs/sales-playbook/` — discovery call guide, proposal template, objection responses
**Status:** 🔴 Not Started
**Guidance:** Commercial framework in `office-skills/outputs/engagement-model/`. Missing: sales scripts, discovery question bank, objection handling guide.

### Task 8.2 – Case Study: Kimre
**Objective:** Kimre engagement documented as a publishable case study (with permission)
**Output:** `clients/kimre/case-study.html` — problem, solution, results, testimonial
**Status:** 🔴 Not Started (depends on live deployment and measurable results)
**Guidance:** Depends on Task 7.1. Without real ROI data, case study will be theoretical.

### Task 8.3 – RAI Governance Checklist
**Objective:** 6-pillar RAI framework expanded into an audit checklist clients can complete pre-deployment
**Output:** `office-skills/outputs/responsible-ai/checklist.html` — interactive checklist, score, recommendations
**Status:** 🔴 Not Started
**Guidance:** One-pager exists at `office-skills/outputs/responsible-ai/`. Expand to per-pillar checklist with evidence requirements.

---

## Phase 9: Documentation
*Making the platform understandable and transferable. Target: new developer contributes in first week.*

### Task 9.1 – Architecture Documentation (DONE)
**Objective:** System architecture documented with Mermaid diagrams for new developers
**Output:** `docs/architecture.html` — 8 sections, Mermaid diagrams, quick-start guide
**Status:** ✅ Complete (2026-03-14)

### Task 9.2 – Documentation Generator (generate.py)
**Objective:** Auto-generation script that pulls from DB + code to keep docs current
**Output:** `docs/generate.py` — creates agent catalog, API reference, status.json; runnable on demand or scheduled
**Status:** 🟡 In Progress (agent launched 2026-03-14)

### Task 9.3 – Per-Agent Specification Files
**Objective:** Every agent (generic + Kimre-specific) has a spec file: purpose, inputs, outputs, HITL points, limitations
**Output:** `docs/agents/[slug].md` for all 16 agents (9 generic + 7 Kimre)
**Status:** 🔴 Not Started (stubs to be created by generate.py)

### Task 9.4 – Developer Guide
**Objective:** Step-by-step guide for adding new agent / industry / dashboard / client
**Output:** `docs/guides/developer.md` — 4 how-to sections, each with working example
**Status:** 🔴 Not Started
**Guidance:** COMPONENTS.md is a partial start. scaffold_agent.py covers agent scaffolding. 8-step client playbook covers client onboarding.

### Task 9.5 – Client User Guides
**Objective:** Per-persona user guides for Kimre dashboards — client can use independently without hand-holding
**Output:** `docs/guides/client-kimre.md` — one section per persona (Alex, Sam, Jordan, Mary, Pat + Strategy + Marketing)
**Status:** 🔴 Not Started

### Task 9.6 – API Reference
**Objective:** All server.py endpoints documented (auto-generated by generate.py)
**Output:** `docs/api/reference.html` — endpoint list, params, response schemas, examples
**Status:** 🔴 Not Started (generate.py will create this)

---

## Phase 10: American Airlines Client Build
*Second gold-standard client after Kimre. ENT-tier, aviation/logistics, demonstrates platform at scale. 12 epics.*

**AA Profile**: ENT, LOGISTICS (Aviation), Service model, 5/5 regulatory (FAA/DOT/TSA/IATA), T3 integration, AA navy accent `#003087`

**Persona set (7)**: Monica Chen (OCC), David Park (MRO), Sarah Kim (Revenue Mgmt), James Torres (CX), Carlos Mendez (Crew Scheduling), Alex Rivera (Network Planning), Sandra Martinez (VP Operations/Executive)

**Agent set (6)**: IROPS Reaccommodation (pilot), AOG Parts Procurement (next), Crew IROPS Recovery (next), Customer Sentiment Monitor (platform), Revenue Integrity (platform), FAA Compliance Monitor (platform)

### Task 10.1 – AA Foundation (Epic 78)
**Objective:** Client profile, portal, and all 7 persona briefs with full JTBD tables
**Output:** `clients/americanairlines/profile.json`, `clients/americanairlines/index.html`, `clients/americanairlines/personas.md` (7 personas), updated `clients/index.html`, updated `clients/seed_clients.py`
**Status:** 🔴 Not Started
**Guidance:** Follow Kimre template exactly. profile.json F20 fields: slug=americanairlines, size_tier=ENT, industry_code=LOGISTICS, business_model=Service, regulatory_score=5, integration_tier=T3. AA accent: `#003087`. 7 personas defined in design session (see MEMORY.md).

### Task 10.2 – AA Strategy Dashboard (Epic 79)
**Objective:** Market position, competitive landscape (Delta/United/Southwest/Spirit), network map, F24 model scoring, agent roadmap
**Output:** `clients/americanairlines/strategy.html`
**Status:** 🔴 Not Started
**Guidance:** F24 moves for airlines: ancillary revenue expansion, cargo growth, MRO-as-a-service, loyalty monetization, regional partnership, tech licensing, sustainability premium. Network map: static SVG hub-spoke (DFW/CLT/MIA/ORD/LAX/PHL/PHX/JFK).

### Task 10.3 – Operations Control Dashboard (Epic 80)
**Objective:** Real-time IROPS command center for Monica Chen (OCC Manager)
**Output:** `clients/americanairlines/operations-control.html`
**Status:** 🔴 Not Started
**Guidance:** KPI strip (Flights Today | Delayed >30min | Cancellations | OTP% rolling 3h | IROPS Passengers Affected). Live delay board (sortable: Flight|Route|Delay|Cause|IROPS pax|Status). Delay cascade tree. IROPS reaccommodation queue with loyalty-tier ranking. Run theater: `aa-irops-reaccommodation-agent`. OTP sparkline (14-day, DOT 80% threshold line).

### Task 10.4 – Crew Scheduling Dashboard (Epic 80B)
**Objective:** Real-time crew dispatch tool for Carlos Mendez (Crew Scheduling Supervisor)
**Output:** `clients/americanairlines/crew-scheduling.html`
**Status:** 🔴 Not Started
**Guidance:** This is a dispatch tool, not a reporting dashboard. Open time board (trips sorted by departure urgency). Legal reserve panel (green/amber/red legality per candidate — FAR Part 117 compliance). Cascade tree view (downstream pairings from a single disruption). Contact tracker (who was called, time, response). Sick call heatmap (7-day by hub). Duty time proximity bars for current crew. Run theater: `aa-crew-irops-recovery-agent`.

### Task 10.5 – MRO Engineering Dashboard (Epic 81)
**Objective:** AOG response and maintenance compliance view for David Park
**Output:** `clients/americanairlines/mro-engineering.html`
**Status:** 🔴 Not Started
**Guidance:** KPI strip (Aircraft Available | AOG Count | Open MELs | Parts Shortages | C-Checks Due 30d). MEL tracker (tail, MEL category A/B/C/D, days remaining). AOG status board. Parts shortage widget (parallel to Kimre material shortage). FAA AD compliance calendar. Run theater: `aa-aog-parts-agent`.

### Task 10.6 – Revenue Management Dashboard (Epic 82)
**Objective:** Demand forecasting and fare class inventory for Sarah Kim
**Output:** `clients/americanairlines/revenue-mgmt.html`
**Status:** 🔴 Not Started
**Guidance:** Demand vs. forecast chart (14-day departure view). Fare class inventory table (Y/B/M/H/Q by flight+cabin). Revenue integrity alert strip. Run theater: `aa-revenue-integrity-agent`.

### Task 10.7 – Customer Experience Dashboard (Epic 83)
**Objective:** IROPS passenger care and sentiment monitoring for James Torres
**Output:** `clients/americanairlines/customer-experience.html`
**Status:** 🔴 Not Started
**Guidance:** IROPS passenger queue with loyalty tier + reaccommodation status. AAdvantage compensation tracker. Sentiment feed (Twitter/App/Survey, classified by type). Complaint resolution HITL queue. Run theater: `aa-customer-sentiment-agent`.

### Task 10.8 – Executive Dashboard (Epic 84)
**Objective:** Operational scorecard and agent program ROI for Sandra Martinez (VP Ops)
**Output:** `clients/americanairlines/executive.html`
**Status:** 🔴 Not Started
**Guidance:** P&L by region (TATL/TPAC/Domestic/LatAm). OTP trend. Agent program ROI per agent. Network health map (route PRASM heatmap, US hub-spoke). Approval queue (escalations from OCC, MRO >$50K PO, Revenue policy exceptions).

### Task 10.9 – IROPS Reaccommodation Agent (Epic 85)
**Objective:** Mock agent covering passenger reaccommodation in IROPS scenarios
**Output:** `pilot-agents/americanairlines/irops_reaccommodation_agent.py`, wired into server.py
**Status:** 🔴 Not Started
**Guidance:** DRY_RUN: 5 cancelled flights, 500 affected PAX with loyalty tier. Logic: rank by EP→PP→Plat→Gold→member→basic → find alternatives → auto-reaccommodate standard → flag complex. Slug: `aa-irops-reaccommodation-agent`. Output: {passengers_affected: 500, auto_reaccommodated: 362, requires_review: 138}.

### Task 10.10 – Crew IROPS Recovery Agent (Epic 85B)
**Objective:** Mock agent for crew legality checking and coverage recommendation in IROPS
**Output:** `pilot-agents/americanairlines/crew_irops_agent.py`, wired into server.py
**Status:** 🔴 Not Started
**Guidance:** DRY_RUN: 12 open trips across DFW/CLT/MIA, reserve pool at each base with hours-flown data. Logic: legality check per candidate (7-day/28-day/rest window) → rank by seniority → draft contact message → flag uncoverable trips. Slug: `aa-crew-irops-recovery-agent`. Key callout: legal ≠ available — must check both. Output: {open_trips: 12, covered: 9, escalation_required: 3, legality_checks_run: 47}.

### Task 10.11 – AOG Parts Procurement Agent (Epic 86)
**Objective:** Mock agent for emergency parts sourcing when aircraft goes on ground
**Output:** `pilot-agents/americanairlines/aog_parts_agent.py`, wired into server.py
**Status:** 🔴 Not Started
**Guidance:** DRY_RUN: 3 AOG events (ORD/MIA/CLT), parts inventory at 8 hub stations. Logic: identify part → check all stations → rank by transfer time+cost vs. vendor procurement → generate emergency PO draft. Slug: `aa-aog-parts-agent`. Output: {aog_events: 3, parts_located: 2, emergency_pos_generated: 1, estimated_savings: 85000}.

### Task 10.12 – AA Engagement Deck + Tools (Epics 88–89)
**Objective:** Pitch deck and business-case calculator for AA engagement
**Output:** `clients/americanairlines/intro-deck.html`, `clients/americanairlines/tools/business-case.html`, `clients/americanairlines/tools/irops-simulator.html`
**Status:** 🔴 Not Started
**Guidance:** 10-slide reveal.js deck. Tools: IROPS ROI calculator (PAX/yr × manual time × cost per hour), IROPS scenario simulator (input: delay type + affected flights → see agent recommendations).
