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

---

## Backlog: Next 20 Epics (90–109)
*Sequenced to move all 9 platform buckets forward in parallel. Grouped by bucket but ordered by dependency.*
*Modification log: Added 2026-03-14 — cross-bucket sprint design.*

---

### ── FOUNDATIONS ──

#### Epic 90: API Authentication Layer
**Bucket:** Foundations | **Moves:** 35% → ~45%
**Objective:** API key authentication for all /api/ routes; simple token-based login for dashboards; per-client key scoping
**Output:** `dashboards/auth.py` (middleware), `/api/auth/token` endpoint, login modal in all dashboards (localStorage token), API key management table in DB
**Status:** 🔴 Not Started
**Guidance:** Start minimal: static API keys per client in DB, Authorization header check in Flask before_request. Dashboard: if no token in localStorage → show login modal (username/client_key) → fetch token → store. Avoids the "anyone with the URL sees client data" problem. Auth can be OAuth2 later; this unblocks sharing the platform with real clients.

#### Epic 91: GitHub Actions CI/CD Pipeline
**Bucket:** Foundations | **Moves:** 35% → ~50%
**Objective:** On every push: HTML validation (html.parser), Python syntax (py_compile), server smoke test (import server, check routes), auto-deploy to GitHub Pages
**Output:** `.github/workflows/ci.yml`, `.github/workflows/deploy.yml`, status badge in README
**Status:** 🔴 Not Started
**Guidance:** Python: `py_compile.compile()` on all .py files. HTML: parse all *.html with `html.parser`, report unclosed tags. Server smoke test: `python3 -c "import dashboards.server; print('ok')"`. GH Pages deploy: rsync to /tmp/build/, strip nested .git dirs, push to gh-pages branch. This closes the manual deploy step entirely.

#### Epic 92: Database Migration Framework
**Bucket:** Foundations | **Moves:** 35% → ~55%
**Objective:** Versioned SQL migration files, migration runner, schema changelog — any schema change goes through a migration file, never manual ALTER TABLE
**Output:** `business-agents/migrations/` directory, `migrate.py` runner (reads version from DB meta table, applies pending migrations in order), first 3 migrations (backfill existing schema state)
**Status:** 🔴 Not Started
**Guidance:** Pattern: `001_initial_schema.sql`, `002_add_lifecycle_stage.sql`, `003_add_size_fit.sql` etc. Meta table: `schema_migrations (version TEXT, applied_at TEXT)`. Runner: compare applied vs. available, run pending in order, log each. This prevents the current "ALTER TABLE IF NOT EXISTS" scatter pattern across seeders.

---

### ── AGENTS ──

#### Epic 93: CG Agents — Pilot-Ready Gate
**Bucket:** Agents | **Moves:** 20% → ~28%
**Objective:** All 3 CG agents promoted from sandbox to pilot_ready via formal validation: schema tests, HITL path end-to-end, F25 rule classification, F18 gate criteria passed
**Output:** `docs/agents/validation/cg-replenishment-pr-agent.md` (validation report), same for demand-forecast + quality-capa; lifecycle_stage updated to pilot_ready in DB; F25 rule table added to each agent spec
**Status:** 🔴 Not Started
**Guidance:** F18 pilot_ready criteria: (1) correct output schema on 5 test inputs, (2) HITL approval path tested end-to-end in dashboard, (3) error handling tested (bad API response, missing fields), (4) value_tracking integration confirmed, (5) F25 classification complete. Also: add `--client-profile` flag to all 3 CG agents (currently hardcoded to CG01 plant).

#### Epic 94: HITL Enforcement Hardening
**Bucket:** Agents | **Moves:** 20% → ~30%
**Objective:** Server enforces HITL — no agent output can be marked "executed" without a recorded approval; expired recommendations auto-archive; full audit chain per decision
**Output:** `dashboards/server.py` updated: `/api/recommendations/<id>/decide` sets executed_at only after approval; `expired` status for recs >48h without decision; new GET `/api/audit-log` endpoint; audit panel added to action-queue.html
**Status:** 🔴 Not Started
**Guidance:** Currently: dashboards show approve/reject UI but server doesn't block execution. Fix: add `requires_approval` flag to AGENT_PATHS dict; POST /api/run/<slug> returns status=pending not status=executed; only changes to executed when approval recorded. This makes the HITL guarantee real, not cosmetic.

#### Epic 95: AA Mock Agents — IROPS + Crew + AOG
**Bucket:** Agents | **Moves:** 20% → ~32%
**Objective:** 3 American Airlines mock agents written and wired: aa-irops-reaccommodation-agent, aa-crew-irops-recovery-agent, aa-aog-parts-agent
**Output:** `pilot-agents/americanairlines/` (new dir), 3 Python agent files (dry-run, standard output schema), server.py additions (3 new slugs + recommendations mappings), docs/agents/ specs for all 3
**Status:** 🔴 Not Started
**Guidance:** Follow pilot-agents/kimre/ pattern exactly. IROPS agent: 500 dry-run PAX across 5 cancelled flights, ranked by loyalty tier (EP→PP→Plat→Gold→member→basic). Crew agent: 12 open trips, reserve pool at DFW/CLT/MIA, FAR Part 117 math encoded as deterministic rules. AOG agent: 3 grounded aircraft, parts inventory at 8 hubs. All slugs: `aa-*`.

---

### ── CLIENTS ──

#### Epic 96: AA Foundation — Profile, Portal, Personas, Strategy
**Bucket:** Clients | **Moves:** 20% → ~26%
**Objective:** Complete AA foundation: profile.json, portal index, 7 full persona briefs (with JTBDs), strategy dashboard
**Output:** `clients/americanairlines/profile.json`, `clients/americanairlines/index.html`, `clients/americanairlines/personas.md`, `clients/americanairlines/strategy.html`; updated `clients/index.html` + `clients/seed_clients.py`
**Status:** 🔴 Not Started
**Guidance:** Follow Kimre template. Profile: ENT, LOGISTICS, Service, reg=5, T3. Personas: 7 defined in memory/aa.md. Strategy: market position (Delta/United/Southwest/Spirit competitive), network map (static SVG hub-spoke DFW/CLT/MIA/ORD/LAX/PHL/PHX/JFK), F24 scoring (7 airline business model moves), agent roadmap. Nav for all AA pages: Home|Strategy|OCC|Crew|MRO|Revenue|CX|Executive

#### Epic 97: AA OCC + Crew Scheduling Dashboards
**Bucket:** Clients | **Moves:** 20% → ~30%
**Objective:** Two most architecturally distinctive AA dashboards — the real-time IROPS command center and the crew dispatch tool
**Output:** `clients/americanairlines/operations-control.html`, `clients/americanairlines/crew-scheduling.html`
**Status:** 🔴 Not Started
**Guidance:** OCC (Monica): delay board, IROPS reaccommodation queue (loyalty-ranked), delay cascade tree, run theater for aa-irops-reaccommodation-agent. Crew (Carlos): open time board (departure urgency), legal reserve panel (FAR Part 117 — green/amber/red per candidate), cascade tree, contact tracker (called/confirmed/declined/no-answer), sick call heatmap (7-day by base), duty time proximity bars. Both dashboards share IROPS event context but are separate pages. Crew dashboard is a dispatch TOOL not a reporting view.

#### Epic 98: PrecisionParts Depth — Dashboards + Agent
**Bucket:** Clients | **Moves:** 20% → ~28%
**Objective:** PrecisionParts portal from shell → meaningful depth: 2 dashboards, 1 mock agent, persona briefs
**Output:** `clients/precisionparts/personas.md` (3 personas), `clients/precisionparts/operations.html`, `clients/precisionparts/executive.html`, `pilot-agents/precisionparts/inventory_replenishment_agent.py`; server.py wired (slug: `pp-inventory-replenishment-agent`)
**Status:** 🔴 Not Started
**Guidance:** PrecisionParts: CNC machining MFG/MTS, 75 employees, ISO 9001 + AS9100, Tulsa OK. Personas: (1) Production Scheduler — daily: scheduling CNC capacity, managing job queue, material availability; (2) Quality Manager — AS9100 compliance, NCR tracking, customer audits; (3) Owner — business health KPIs. Operations dashboard: CNC job queue (by machine), setup time tracking, material stock vs. open jobs. Agent: adapted from retail-inventory-replenishment-agent (MTS catalog parts). Accent: steel blue `#2563eb`.

#### Epic 99: MeridianBank Depth — AML Dashboard + Agent
**Bucket:** Clients | **Moves:** 20% → ~28%
**Objective:** MeridianBank portal from shell → meaningful depth: AML triage dashboard, executive view, AML alert triage mock agent
**Output:** `clients/meridianbank/personas.md` (3 personas), `clients/meridianbank/aml-triage.html`, `clients/meridianbank/executive.html`, `pilot-agents/meridianbank/aml_alert_triage_agent.py`; server.py wired (slug: `mb-aml-alert-triage-agent`)
**Status:** 🔴 Not Started
**Guidance:** MeridianBank: regional bank, 200 employees, 12 branches, Charlotte NC, BSA/AML+FDIC+OCC (reg 5/5). Personas: (1) BSA Officer — AML alert queue, SAR filing decisions (F25: SAR filing = Mandatory Checkpoint), CIP compliance; (2) Credit Officer — loan file review, credit limit changes; (3) CEO — regulatory risk, portfolio health. AML dashboard: alert queue (rule-triggered vs. ML-scored), risk tier (high/medium/low), SAR decision workflow (hard HITL — cannot auto-file), case management timeline. Agent: reads DRY_RUN_ALERTS (25 alerts), classifies by rule type, scores by customer risk tier, recommends dismiss/investigate/file-SAR. Accent: bank green `#16a34a`.

---

### ── INTELLIGENCE ──

#### Epic 100: Blueprint Financial Enrichment
**Bucket:** Intelligence | **Moves:** 55% → ~65%
**Objective:** All 40 agent blueprints enriched with real financial parameters: implementation cost, year-1 value, payback weeks, complexity notes
**Output:** New DB columns on `agent_blueprints`: `typical_cost_usd INT`, `year1_value_usd INT`, `payback_weeks INT`, `complexity_notes TEXT`; `seed_blueprint_financials.py` populates all 40; blueprint viewer updated to show financial cards
**Status:** 🔴 Not Started
**Guidance:** Add migration (Epic 92 dependency — can do manually if 92 not done). Use industry benchmarks: CG replenishment ~$18K implementation, ~$45K year-1 (inventory efficiency + planner time). Kimre agents: derive from value_tracking actual data where available. Blueprint viewer in `business-agents/blueprints/`. This makes the ROI calculator (Epic 105) data-driven.

#### Epic 101: F25/F26 Agent Spec Retrofit
**Bucket:** Intelligence | **Moves:** 55% → ~60%
**Objective:** All 17 agent specs in docs/agents/ updated with F25 rule classification table per decision point; F26 topology noted where multi-agent coordination applies
**Output:** Each agent spec gets a new "## Regulatory & Coordination Profile" section: F25 table (Decision | Rule Type | Agent Handling) + F26 topology if applicable
**Status:** 🔴 Not Started
**Guidance:** Most important to retrofit: cg-quality-capa-agent (EPA rules = deterministic lookup tables), ap-invoice-processing (approval thresholds = policy rules), kimre-quality-compliance-agent (EPA chemical resistance = deterministic), stakeholder-enrichment-agent (GDPR/data use = mandatory checkpoint). F26 applies to: kimre-rfq-quote + kimre-order-notifier (sequential pipeline), all 3 CG agents via orchestrator (supervisory), future AA agents (independent parallel → collaborative).

---

### ── INTERFACES ──

#### Epic 102: F19 Scoring Run + Priority Fixes
**Bucket:** Interfaces | **Moves:** 35% → ~45%
**Objective:** Formally score all 17 dashboards (8 platform + 9 Kimre) against F19 rubric; fix the 5 lowest-scoring items
**Output:** Scoring table in `dashboards/eval.html` (updated with all 17 dashboards scored); minimum 5 targeted fixes to lowest-scoring D1/D2/D3 dimension items; documented in `docs/agents/validation/` 
**Status:** 🔴 Not Started
**Guidance:** F19 dimensions: D1 Narrative (persona-specific impact story), D2 Interactivity (sortable tables, panels, filters), D3 HITL Design (approve/reject at point of decision, not batch), D4 Data Density (right amount for persona — exec ≠ ops), D5 Persona Fit (does the UX match how the persona actually works?). eval.html already has scoring infrastructure — extend it. Likely lowest scorers: eval.html itself (meta), it-health.html (D5 — too technical for non-IT persona), enterprise.html (D1 — no narrative).

#### Epic 103: Server-Sent Events — Live Run Theater
**Bucket:** Interfaces | **Moves:** 35% → ~42%
**Objective:** Run theater shows real-time agent step progress via SSE — no more fake animation with hardcoded delays
**Output:** `/api/run/<slug>/stream` SSE endpoint in server.py; agent runner subprocess pipes stdout → SSE stream; run theater drawer reads from SSE instead of AGENT_STEPS array; animated in real-time as agent runs
**Status:** 🔴 Not Started
**Guidance:** Flask SSE: `Response(generate(), mimetype='text/event-stream')`. Agent stdout: each agent prints `STEP: <step_name>` to stdout at each stage. Server parses stdout lines → streams as SSE events. Dashboard: `EventSource('/api/run/<slug>/stream')` → update step bar in real-time. This makes the run theater genuinely real vs. theatrical. Start with cg-replenishment-pr-agent as the prototype.

---

### ── TOOLS ──

#### Epic 104: Kimre Tools Live Backend
**Bucket:** Tools | **Moves:** 45% → ~55%
**Objective:** rfq-intake.html and spec-gen.html connected to server endpoints — not static demos; business-case.html pulls real value_tracking data
**Output:** `/api/rfq` POST endpoint (stores intake, returns agent-style recommendation from rfq-quote-agent); `/api/spec-gen` POST endpoint (returns generated spec HTML downloadable); business-case.html fetches `/api/value-summary?client=kimre`
**Status:** 🔴 Not Started
**Guidance:** rfq-intake.html form currently has no POST target. Add: POST /api/rfq → runs kimre-rfq-quote-agent logic against submitted data (not dry-run) → returns scope draft. spec-gen.html: POST /api/spec-gen → applies standard Kimre spec template to submitted parameters → returns rendered HTML. business-case.html: GET /api/value-summary → queries value_tracking + pilot_runs → returns aggregated ROI. These three make Kimre tools actually useful, not just visually complete.

#### Epic 105: Generic ROI Calculator Tool
**Bucket:** Tools | **Moves:** 45% → ~55%
**Objective:** Platform-level ROI calculator that any prospect can use: industry + company size + process → pulls blueprint data → generates ROI estimate + engagement proposal
**Output:** `/tools/roi-calculator.html` (new, at workspace root level, served from server.py); pulls from blueprint financial data (Epic 100 dependency); outputs: hours/year saved, year-1 value, payback weeks, recommended engagement tier, "Download Proposal" button
**Status:** 🔴 Not Started
**Guidance:** Input: industry dropdown (13 options), company size (SMB/MID/ENT), target process (dropdown filtered by industry, pulls from processes table). Logic: match to top-3 blueprint recommendations (from v_opportunity_matrix), pull financial params (Epic 100), apply size multiplier (SMB=0.4×, MID=1.0×, ENT=2.5×). Output: branded one-pager with agent recommendation + ROI projection. Add to index.html as a top-level tool. This is a sales tool, not just a platform tool.

---

### ── DATA HYDRATION ──

#### Epic 106: 90-Day Synthetic Run History
**Bucket:** Data Hydration | **Moves:** 15% → ~30%
**Objective:** All 12 agents have realistic 90-day run history in pilot_runs + recommendations + value_tracking; dashboards show trends not empty sparklines
**Output:** `dashboards/seed_history.py` (extended version of seed_runs.py) — generates 90 days × 12 agents × 1-3 runs/day; realistic output JSON per agent type; recommendations with realistic approval/reject/pending distribution; value_tracking with weekly ROI accumulation
**Status:** 🔴 Not Started
**Guidance:** For each agent type, simulate realistic run patterns: replenishment fires when stock low (2-3× per week), demand forecast runs weekly, quality CAPA runs after replenishment, IROPS runs on-demand (simulated 4× per day). Output JSON should vary (not all same) — vary quantities, urgency levels, agent step timing. This single epic changes the demo from "empty dashboards with demo data" to "a platform that's been running for 3 months".

#### Epic 107: Live Agent Scheduler + Weekly Digest
**Bucket:** Data Hydration | **Moves:** 15% → ~35%
**Objective:** All 12 agents running automatically on schedule (dry-run) and accumulating history; weekly digest email (mock) shows aggregate value delivered
**Output:** `agent-runtime/agent_schedule.py` (schedule configs per agent slug), cron-compatible runner; weekly digest HTML template at `/api/digest/weekly`; digest shows: runs this week, recommendations actioned, value tracked, trend vs. last week
**Status:** 🔴 Not Started
**Guidance:** Scheduler in `agent-runtime/scheduler.py` already exists. Extend: add per-slug schedule configs (replenishment: daily 6am, demand-forecast: weekly Monday 7am, quality-capa: after replenishment run, AA agents: simulated every 30min). Weekly digest: HTML report generated from pilot_runs + value_tracking, exportable, designed to be sent to client executive. This makes the platform feel live, not dormant.

---

### ── GO-TO-MARKET ──

#### Epic 108: Kimre Reference Case Study Document
**Bucket:** Go-to-Market | **Moves:** 40% → ~50%
**Objective:** Printable, shareable case study for Kimre — the first documented platform case study pulled from real (or realistic) run data
**Output:** `clients/kimre/case-study.html` (print-optimized HTML, 2-page equivalent); sections: Client Background, Challenge, Solution (Material Requisition Agent), Implementation (6 weeks, 3 phases), Results (hours saved, PRs created, data from value_tracking), HITL Design, ROI Waterfall Chart, Next Steps (expand to RFQ-to-Quote Agent)
**Status:** 🔴 Not Started
**Guidance:** Pull data from: value_tracking table (real or seeded from Epic 106), pilot_runs (run counts, recommendation counts). ROI waterfall: SVG bar chart (Investment → Hours Saved → Error Reduction → Stock-out Prevention → Net Value). Include F19 HITL design section (how approval workflow works — this differentiates from black-box AI). Designed to be printed and left with the Kimre team. Also works as a proposal template for next client.

#### Epic 109: Platform Demo Script + Objection Handling
**Bucket:** Go-to-Market | **Moves:** 40% → ~52%
**Objective:** Structured 10-minute demo script for live presentations, with annotated screenshots, talking points per screen, and objection handling section
**Output:** `docs/guides/demo-script.md` — fully scripted walkthrough: (1) AA IROPS scenario → (2) Kimre Materials Agent → (3) Platform intelligence layer → (4) ROI story; objection handling: "it's just a dashboard" / "we have SAP" / "AI is risky" / "too expensive" / "we tried this before"
**Status:** 🔴 Not Started
**Guidance:** Script structure: 30s hook → 2min AA IROPS demo (Monica + Carlos coordination) → 2min Kimre Materials Agent + value_tracking ROI → 2min platform intelligence (40 blueprints, 13 industries, opportunity scoring) → 2min responsible AI + F19 HITL design → 1min ROI model + engagement tiers → 30s next step. Each section has: what to show on screen, what to say, transition to next. Objection section: each objection → acknowledge → reframe → proof point.
