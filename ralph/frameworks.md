# Business Agents Platform — Frameworks Registry
Updated: 2026-03-14

This document is the canonical reference for all analytical frameworks, classification schemes, and structural dimensions used across the platform. Every DB table, blueprint, view, and client deliverable maps back to one or more of these frameworks.

---

## 1. APQC Process Classification Framework (PCF)

**What it is:** Industry-neutral process taxonomy maintained by the American Productivity & Quality Center. The backbone of our process repository.

**How we use it:** Every process in our DB maps to an APQC function (Level 1) and process (Level 2/3). All agent blueprints reference a specific APQC process code.

**12 Functions:**

| # | Function | Scope |
|---|---|---|
| 1 | Develop Vision and Strategy | Strategic planning, portfolio, M&A |
| 2 | Develop and Manage Products and Services | R&D, innovation, product lifecycle |
| 3 | Market and Sell Products and Services | Marketing, sales, pricing, forecasting |
| 4 | Deliver Physical Products | Supply chain, manufacturing, logistics, quality |
| 5 | Deliver Services | Service delivery, SLA management, field service |
| 6 | Manage Customer Service | Support, complaints, knowledge, satisfaction |
| 7 | Develop and Manage Human Capital | HR, recruiting, training, performance |
| 8 | Manage Information Technology | IT ops, security, data, systems |
| 9 | Manage Financial Resources | AP/AR, treasury, reporting, compliance |
| 10 | Acquire, Construct, and Manage Assets | Capex, facilities, maintenance, asset lifecycle |
| 11 | Manage Enterprise Risk, Compliance, and Resiliency | Risk, audit, regulatory, BCM |
| 12 | Manage External Relationships | Government, community, PR, trade bodies |

**DB table:** `functions` (12 rows), `processes` (177+ rows), `industry_processes`

---

## 2. Industry Verticals

**What it is:** The 13 industry sectors we cover. Each industry has its own process set, system landscape, and agent blueprints.

**How we use it:** Every process links to one or more industries via `industry_processes`. Blueprints target a specific industry. All views filter by industry.

| # | Code | Industry | Status |
|---|---|---|---|
| 1 | CG | Consumer Goods | ✅ Active |
| 2 | MFG | Industrial Manufacturing | 🔄 In progress |
| 3 | PHARMA | Pharmaceuticals | ✅ Active |
| 4 | FS | Financial Services | ✅ Active |
| 5 | RETAIL | Retail | 🔄 In progress |
| 6 | HEALTH | Healthcare | ⏳ Queued |
| 7 | ENERGY | Energy & Utilities | ⏳ Queued |
| 8 | LOGISTICS | Logistics & Transportation | ⏳ Queued |
| 9 | TELECOM | Telecommunications | ⏳ Queued |
| 10 | AUTO | Automotive | ⏳ Queued |
| 11 | TECH | Technology / SaaS | ⏳ Queued |
| 12 | CONST | Construction & Engineering | ⏳ Queued |
| 13 | PUBLIC | Public Sector / Government | ⏳ Queued |

**DB table:** `industries`

---

## 3. Capability Types

**What it is:** The 6 types of cognitive work an agent can perform. Every agent action and blueprint capability is classified into one of these types.

**How we use it:** Capability matrix, feature library, opportunity scoring, blueprint design. The 6 types ensure coverage across the full decision-support spectrum.

| ID | Type | What the agent does | Typical authority |
|---|---|---|---|
| 1 | Monitor & Detect | Watches data streams for anomalies, thresholds, or patterns | LOW |
| 2 | Root Cause Analysis | Diagnoses why something happened by correlating signals | LOW |
| 3 | Idea & Option Generation | Generates recommendations, alternatives, or next-best-actions | LOW |
| 4 | Evaluate & Score | Ranks or scores options against criteria | LOW–MEDIUM |
| 5 | Execute & Act | Takes an action in a downstream system (create, update, submit) | MEDIUM–HIGH |
| 6 | Manage & Track | Monitors ongoing tasks, deadlines, and progress | LOW |

**DB table:** `capability_types` (6 rows), `agent_capabilities`, `process_agent_actions`

---

## 4. Authority Levels

**What it is:** A three-tier governance classification for every agent action. Determines how much human oversight is required before an action takes effect.

**How we use it:** Every capability and blueprint is classified before being built. The authority level drives escalation logic, notification behaviour, and audit trail requirements.

| Level | Colour | Meaning | Human role | Examples |
|---|---|---|---|---|
| LOW | Green | Fully automated, reversible | None required | Monitoring alerts, read-only reports, draft documents for filing |
| MEDIUM | Yellow | Auto + notify; action taken but human can intervene | Notified, can override | Work orders, purchase recommendations, non-conformance reports |
| HIGH | Orange/Red | Draft for human approval; nothing commits without sign-off | Must approve | Regulatory submissions, supplier delistings, large PO execution, safety shutdowns |

**DB table:** `agent_blueprints.authority_level`, `agent_capabilities.authority_level`, `process_agent_actions.authority_level`

---

## 5. Company Size Tiers

**What it is:** Three commercial segments that shape which agents, systems, and engagement models apply to a given client.

**How we use it:** Tag blueprints with `size_fit`, filter the client portal and blueprint viewer by tier, map engagement model pricing to tier, and select relevant systems.

| Tier | Code | Revenue | Employees | Buying motion | Key traits |
|---|---|---|---|---|---|
| Small & Medium Business | SMB | < $50M | < 250 | Owner decides fast, low IT sophistication | Excel, QuickBooks, HubSpot, NetSuite; wants simple out-of-box agents |
| Mid-Market | MID | $50M–$1B | 250–5,000 | IT + Ops committee, 2-6 month cycle | SAP B1, Sage X3, Salesforce; configurable, some integrations |
| Enterprise | ENT | $1B+ | 5,000+ | 6-18 month procurement | SAP S/4HANA, Oracle, Workday, ServiceNow; governance, audit, multi-system |

**Authority comfort by tier:**
- SMB: comfortable with HIGH automation (small team, fast decisions)
- Mid-Market: MEDIUM authority preferred (some oversight)
- Enterprise: LOW authority often required (governance gates, SOX, segregation of duties)

**ROI framing by tier:**
- SMB: "One person does the work of five" — headcount leverage
- Mid-Market: Cost reduction + headcount avoidance + speed
- Enterprise: Risk reduction, compliance, operational scale

**Engagement model mapping:**
- Discovery Sprint ($25K–$40K, 2 weeks) → SMB / MID
- Pilot ($75K–$150K, 6–10 weeks) → MID / ENT
- Platform ($250K–$750K+, 6–18 months) → ENT

**Systems by tier:**

| Tier | ERP | CRM | WMS | Finance | HR |
|---|---|---|---|---|---|
| SMB | QuickBooks / NetSuite | HubSpot | ShipBob / Linnworks | QuickBooks | Gusto / Rippling |
| MID | SAP Business One / Sage X3 | Salesforce | Manhattan (SMB tier) | Sage Intacct | ADP / Paycom |
| ENT | SAP S/4HANA / Oracle ERP | Salesforce / MS Dynamics | Manhattan / Blue Yonder | Oracle Financials | Workday / SuccessFactors |

**DB field (planned):** `agent_blueprints.size_fit` (SMB / MID / ENT / ALL)

---

## 6. Feature Library

**What it is:** 18 reusable platform capabilities that appear across multiple agent blueprints. Represents our reusable IP layer — the building blocks that reduce time-to-deploy for new agents.

**How we use it:** Every blueprint links to the features it uses via `blueprint_features`. The feature network visualisation shows reuse patterns. Sales uses this to demonstrate platform depth.

**5 Feature Categories:**

| Category | Examples |
|---|---|
| Data | Real-time data ingestion, historical trend analysis, anomaly detection |
| Integration | ERP read/write, REST API connector, EDI adapter |
| Output | Structured report generation, email notification, dashboard update |
| Control | Rule engine, threshold configuration, schedule management |
| Governance | Audit logging, approval workflow, authority enforcement |

**DB table:** `features` (18 rows), `blueprint_features` (23+ links)

---

## 7. Agent Blueprint Framework

**What it is:** The standardised 6-section spec for every agent. Ensures consistency across all blueprints and enables automated tooling (scaffold, viewer, flow diagram).

**How we use it:** Every blueprint follows this structure. The scaffold tool generates skeleton code from it. The blueprint flow visualisation renders it as a swimlane.

**6 Sections:**

| Section | Content |
|---|---|
| Trigger | What initiates the agent run (schedule, event, threshold) |
| Inputs | Source systems and data the agent reads |
| Processing Steps | The decision logic — detect, analyse, evaluate, decide |
| Outputs | What the agent produces (report, record, notification, action) |
| Escalation | When and how the agent hands off to a human |
| KPIs | Measurable outcomes used to track agent value |

**DB table:** `agent_blueprints` (16 rows), `agent_capabilities`

---

## 8. Engagement Model Tiers

**What it is:** Three commercial packages for deploying agents with clients. Maps to company size tier and maturity level.

**How we use it:** Engagement model HTML, client portal, pricing conversations.

| Tier | Price | Duration | Deliverable |
|---|---|---|---|
| Discovery Sprint | $25K–$40K | 2 weeks | Process map, opportunity assessment, 1 blueprint proof |
| Pilot | $75K–$150K | 6–10 weeks | 2–3 live agents, dashboard, value measurement baseline |
| Platform | $250K–$750K+ | 6–18 months | Full deployment, multi-agent orchestration, ongoing optimisation |

---

## 9. Value Measurement Framework

**What it is:** The before/after KPI structure used to measure and communicate agent value post-deployment.

**How we use it:** KPIs & Benefits Realization HTML, client onboarding baseline assessment, pilot agent value tracking.

**4 Measurement Dimensions:**
1. **Time saved** — hours/week per role, measured directly
2. **Error reduction** — defect rates, exception rates, rework %
3. **Cycle time** — end-to-end process duration before vs. after
4. **Risk / compliance** — audit findings, breach events, SLA violations

**90-day success gates:** Defined per engagement in the benefits-realization framework.

---

## 10. Agent Maturity Model

**What it is:** A four-level scale describing how autonomously an agent operates. Used to position current state and define a client's target state.

**How we use it:** Client conversations about where they are vs. where they want to be. Maps directly to authority levels. Drives engagement scoping.

| Level | Name | What happens | Authority | Human role |
|---|---|---|---|---|
| L1 | Monitor | Agent watches and alerts — no action taken | LOW | Receives alerts, acts manually |
| L2 | Recommend | Agent produces ranked options and drafts — human selects | LOW | Reviews and decides |
| L3 | Execute with oversight | Agent acts and notifies — human can intervene | MEDIUM | Notified, can override |
| L4 | Autonomous | Agent acts fully — logs for audit, escalates only on exception | HIGH | Audits logs, reviews exceptions |

**Typical progression:** Most clients start at L1-L2 in year one, move to L3 in year two, selectively reach L4 on low-risk, high-volume processes.

**DB implication:** `agent_blueprints.authority_level` maps L1-L2 → LOW, L3 → MEDIUM, L4 → HIGH.

---

## 11. Data Readiness Framework

**What it is:** A pre-deployment assessment of whether a client's data can power agents reliably. The single biggest predictor of agent success or failure.

**How we use it:** Client onboarding questionnaire, discovery sprint scoping, risk flagging in proposals.

**5 Dimensions (scored 1–5 each):**

| Dimension | Score 1 (Red) | Score 3 (Amber) | Score 5 (Green) |
|---|---|---|---|
| **Availability** | Data locked in paper/email | Partial digital, manual exports | System APIs available, real-time accessible |
| **Quality** | High error rate, no governance | Known issues, partial cleansing | Validated, master data managed |
| **Freshness** | Weekly/monthly batch only | Daily batch | Real-time or near-real-time |
| **Accessibility** | No APIs, IT gatekeeping | Limited API, slow access | Open APIs, sandbox available |
| **Governance** | No ownership, no lineage | Partial ownership | Data owners defined, lineage tracked |

**Total score (5–25):** 5–10 = High risk, pilot scope must include data remediation. 11–18 = Moderate, proceed with monitoring. 19–25 = Ready to deploy.

**Output:** Data Readiness Score in client onboarding profile. Feeds engagement model tier recommendation.

---

## 12. Stakeholder / Persona Framework

**What it is:** The 5 buyer and user personas that appear in every enterprise agent deployment. Each has distinct concerns, success metrics, and objections.

**How we use it:** Shapes all communication assets (pitch deck, exec summary, portal). Drives which KPIs to highlight. Guides objection handling in sales.

| Persona | Role | Primary concern | Success metric | Key objection |
|---|---|---|---|---|
| **Executive Sponsor** | C-suite / VP | ROI, strategic positioning, risk | $ saved, competitive advantage | "Will this actually stick?" |
| **Process Owner** | Director / Manager | Their team's workload and accuracy | Hours saved, error rate reduction | "Will this take my team's jobs?" |
| **IT Lead** | CTO / IT Director | Integration complexity, security, maintenance | Uptime, integration success rate | "Who maintains this?" |
| **Compliance Officer** | GC / Chief Risk | Audit trail, authority, regulatory exposure | Audit findings, authority violations | "What if the agent makes a mistake?" |
| **End User** | Analyst / Operator | Ease of use, trust, control | Adoption rate, satisfaction | "Why should I trust this?" |

**Platform assets mapped to persona:**
- Executive Sponsor → exec-summary, productivity-multiplier, engagement-model
- Process Owner → benefits-realization, blueprint viewer, opportunity quadrant
- IT Lead → technical-overview, systems-integration-map, blueprint-flow
- Compliance Officer → authority-distribution, authority levels in blueprints
- End User → client portal, onboarding checklist

---

## 13. ROI Category Framework

**What it is:** Four categories of value that agents deliver. Different categories resonate with different buyer personas and require different evidence.

**How we use it:** ROI calculator, benefits realization, exec summary, pitch deck. Ensures every blueprint has value mapped across multiple categories.

| Category | What it means | Evidence required | Primary persona |
|---|---|---|---|
| **Hard Savings** | Headcount reduction or avoidance, direct cost elimination | Before/after FTE count, $ per transaction | CFO, Executive Sponsor |
| **Soft Savings** | Time freed for higher-value work (not headcount reduction) | Hours/week saved per role, tasks eliminated | Process Owner, COO |
| **Risk Avoidance** | Fewer compliance breaches, audit findings, SLA violations, recall events | Incident rate reduction, penalty exposure avoided | Compliance Officer, GC |
| **Revenue Enablement** | Faster decisions, better customer experience, higher win rates | Revenue delta, NPS uplift, cycle time reduction | CEO, Sales VP |

**Blueprint value tagging (planned):** Each blueprint will have a `value_categories` field listing which of the 4 categories it delivers.

**Buyer alignment:**
- CFO meeting → lead with Hard Savings + Risk Avoidance
- COO meeting → lead with Soft Savings + Revenue Enablement
- Board presentation → all four, quantified

---

## 14. Integration Complexity Matrix

**What it is:** A classification of how difficult it is to integrate with each system type. Sets client expectations on timeline, cost, and technical risk.

**How we use it:** Technical scoping in proposals, system integration map, blueprint integration design, engagement model sizing.

| Tier | Integration type | Typical effort | Examples | Notes |
|---|---|---|---|---|
| **T1 — Easy** | REST/GraphQL API, webhook | Days | Shopify, HubSpot, Salesforce, Slack, Zendesk | Well-documented, sandbox available |
| **T2 — Moderate** | SFTP batch, JDBC/ODBC, basic SOAP | 1–2 weeks | NetSuite, older Salesforce modules, legacy WMS | Batch latency; data transformation required |
| **T3 — Complex** | SAP BAPI/RFC, Oracle ORDS, ERP table-level | 3–6 weeks | SAP S/4HANA, Oracle EBS, Infor, Epicor | Requires middleware or SAP connector; authorisation sensitive |
| **T4 — Hard** | Mainframe screen-scraping, proprietary protocol, no API | 6–12 weeks | IBM AS/400, legacy COBOL, bespoke ERP | High maintenance risk; may require RPA bridge |

**Complexity factors that elevate tier:**
- No sandbox environment (+1 tier)
- SSO/MFA required (+0.5 tier)
- Data residency constraints (+0.5 tier)
- High-volume real-time requirements (+1 tier)

**Output:** Integration complexity score per blueprint, used in engagement model scoping and timeline estimation.

---

## 15. Regulatory Complexity Score

**What it is:** An industry-level rating of how much compliance overhead affects agent design, authority level requirements, and deployment timeline.

**How we use it:** Drives authority level defaults per industry, shapes audit trail requirements, informs engagement model pricing for regulated sectors.

| Industry | Score (1–5) | Key regulations | Impact on agents |
|---|---|---|---|
| Pharmaceuticals | 5 | FDA 21 CFR Part 11, GMP, EMA | Every action must be audit-logged; validation required; HIGH authority needs IQ/OQ/PQ |
| Financial Services | 5 | SOX, Basel III, GDPR, AML/KYC, MiFID II | Segregation of duties mandatory; model risk management for scoring agents |
| Healthcare | 5 | HIPAA, CMS, FDA (medical devices), JCAHO | PHI handling; clinical decision support regulations; audit trail for all patient-adjacent actions |
| Energy & Utilities | 4 | NERC CIP, EPA, FERC, OSHA | Safety-critical systems require formal change management; real-time control needs extra approval gates |
| Automotive | 3 | IATF 16949, PPAP, EU type approval, NHTSA recall | Quality processes well-defined; recall management is HIGH authority by default |
| Consumer Goods | 3 | FDA (food/cosmetics), EFSA, FTC claims | Labeling and claims compliance; HACCP for food; moderate audit requirements |
| Retail | 2 | PCI-DSS (payments), GDPR, consumer protection | Payment data handling; customer data privacy; low regulatory burden on operations agents |
| Construction | 2 | OSHA, building codes, local permits | Safety incident reporting is HIGH; permit management has regulatory deadlines |
| Logistics | 2 | CBP (customs), DOT (transport), IATA (air cargo) | Customs classification agents need compliance checks; driver HOS is regulated |
| Technology / SaaS | 2 | SOC2, GDPR, CCPA, ISO 27001 | Security and privacy agents need careful scoping; audit evidence collection is key use case |
| Telecom | 2 | FCC, OFCOM, GDPR, number portability regulations | Provisioning agents need compliance checks; fraud detection is a key use case |
| Public Sector | 4 | FedRAMP, FISMA, state-level regulations, procurement laws | Data sovereignty requirements; procurement rules constrain automation of buying decisions |
| Industrial Manufacturing | 3 | ISO 9001, OSHA, EPA, export controls | EHS agents are HIGH authority; quality agents need validation documentation |

**Score impact:** Score ≥ 4 → default to MEDIUM authority across all blueprints; Score = 5 → all blueprints require audit log, HIGH authority needs formal approval workflow documented.

---

## 16. Opportunity Prioritization Framework (Client-Facing 2×2)

**What it is:** A structured 2×2 prioritization method for ranking agentic opportunities with clients. The Y-axis is Value Potential; the X-axis is Execution Effort. Each axis is scored from weighted sub-dimensions. Prevents gut-feel prioritization and gives clients a defensible, data-driven roadmap.

**How we use it:** Workshop facilitation with clients, pre-sales opportunity assessment, internal epic sequencing, the opportunity quadrant visualisation.

**The 2×2:**

```
High Value  │  Strategic Bets      │  Quick Wins      │
            │  (Plan & fund)       │  (Start here)    │
            ├──────────────────────┼──────────────────┤
Low Value   │  Defer               │  Easy Fills      │
            │  (Not worth it)      │  (If bandwidth)  │
            └──────────────────────┴──────────────────┘
                  High Effort            Low Effort
```

---

### Axis 1: Value Potential (Y-axis)

*How much value will this agent deliver if it succeeds?*

| Sub-dimension | Weight | Score 1 (Low) | Score 5 (High) |
|---|---|---|---|
| **Business Impact** | 40% | Marginal time saving, low volume process | High-volume, high-cost process; direct P&L impact |
| **Stakeholder Alignment** | 25% | No executive sponsor; team resistant | C-suite champion; team eager to adopt |
| **Regulatory / Risk Impact** | 20% | No compliance angle; purely operational | Reduces audit findings, regulatory exposure, or recall risk |
| **Scalability** | 15% | One process, one team, one site | Applicable across sites, functions, or business units |

**Value Potential Score = (Impact × 0.40) + (Alignment × 0.25) + (Regulatory × 0.20) + (Scalability × 0.15)**

---

### Axis 2: Execution Effort (X-axis)

*How hard will this be to build and deploy? (Higher score = more effort)*

| Sub-dimension | Weight | Score 1 (Low effort) | Score 5 (High effort) |
|---|---|---|---|
| **Implementation Complexity** | 35% | REST API, sandbox available, T1 integration | SAP BAPI, no API, mainframe (T3–T4); custom middleware |
| **Data Complexity** | 30% | Clean, real-time, accessible data; score 19–25 on Data Readiness | Fragmented, paper-based, no governance; score 5–10 |
| **Change Management** | 25% | Agent runs silently; zero behaviour change needed | Requires team retraining, new approval workflows, culture shift |
| **Time to Value** | 10% | Value visible within 2 weeks of go-live | Benefits only realized after 6+ months of adoption |

**Execution Effort Score = (Implementation × 0.35) + (Data × 0.30) + (Change × 0.25) + (TimeToValue × 0.10)**

---

### Quadrant Thresholds

Score each axis 1–5. Plot on the 2×2 using midpoint = 3.0:

| Quadrant | Value ≥ 3 | Effort | Recommendation |
|---|---|---|---|
| **Quick Wins** | Yes | ≤ 3 | Start immediately — high ROI, low risk |
| **Strategic Bets** | Yes | > 3 | Fund and plan carefully — worth the investment |
| **Easy Fills** | No | ≤ 3 | Do after Quick Wins if capacity allows |
| **Defer** | No | > 3 | Remove from roadmap — not worth the effort |

---

### Internal Prioritization Variant

For internal epic/build decisions, replace Stakeholder Alignment with **Client Demand** (are prospects asking for this?) and Scalability with **Differentiation** (do competitors offer this?):

| Industry (illustrative) | Value | Effort | Quadrant |
|---|---|---|---|
| Healthcare | 4.2 | 2.8 | Quick Win |
| Energy | 4.0 | 2.5 | Quick Win |
| Logistics | 3.8 | 3.0 | Strategic Bet |
| Technology | 3.7 | 2.5 | Quick Win |
| Telecom | 3.3 | 3.2 | Strategic Bet |
| Automotive | 2.8 | 3.0 | Easy Fill |
| Construction | 2.5 | 2.8 | Easy Fill |
| Public Sector | 2.5 | 3.5 | Defer |

**Client-facing deliverable:** Interactive scoring tool (`prioritization/index.html`) — consultant inputs 8 sub-dimension scores, tool plots the opportunity on a live 2×2, generates a ranked shortlist with rationale. (Epic 33)

---

## 17. Responsible AI Framework

**What it is:** The six-pillar governance standard for how we design, deploy, and audit agents. Not a compliance checkbox — a differentiator with regulated-sector clients who will ask about it before signing.

**How we use it:** Client trust-building in regulated industries (PHARMA, FS, HEALTH), RFP responses, technical-overview, blueprint design standards, audit readiness.

**The good news:** We already implement most of this. The framework makes it explicit and auditable.

**6 Pillars:**

### Pillar 1 — Transparency
*Agents must be explainable. No black-box decisions.*
- Every agent action logged with: what it did, why it triggered, what data it used, what output it produced
- Blueprint flow diagrams (already built) document the full decision logic
- Agent run history visible in enterprise dashboard
- **Implemented by:** `agent_runs` table, pilot agent audit logs, blueprint-flow visualisation

### Pillar 2 — Human Oversight
*Appropriate human control at every authority level.*
- LOW: humans receive reports and alerts; agent acts but is reviewed
- MEDIUM: human notified before action takes effect; override window
- HIGH: nothing commits without explicit human approval
- **Implemented by:** Authority level framework (F4), escalation paths in every blueprint, notification stubs in Epic 11

### Pillar 3 — Fairness
*Scoring and ranking agents must not embed discriminatory bias.*
- Any agent that scores people (hiring, credit, benefits, customer priority) requires bias audit before production
- Score outputs must be explainable per-record (not just aggregate)
- Relevant blueprints: fs-credit-limit-review, retail-customer-churn-agent, employee-onboarding
- **Required action:** Bias audit checklist for scoring agents (to be built in Epic 32)

### Pillar 4 — Privacy
*Agents handle data with minimum necessary access.*
- PII fields enumerated per blueprint; agents request read-only scopes where possible
- Industry-specific rules: HIPAA (Healthcare), GDPR (EU clients), CCPA (California), SOX (FS)
- Data retention: agent run logs purged after configurable retention period
- **Required action:** Privacy impact assessment template (to be built in Epic 32)

### Pillar 5 — Accountability
*Clear ownership for every agent in production.*
- Every deployed agent has a named: Business Owner, Technical Owner, Compliance Reviewer
- Authority decisions documented and signed off before go-live
- Incident response: if agent causes an error, owner is paged within 15 minutes (health check + notification — already in Epic 11)
- **Implemented by:** `agent_registry.json` (Epic 11), escalation paths per blueprint

### Pillar 6 — Robustness
*Agents fail gracefully. No cascading failures.*
- Circuit breaker prevents retry storms when downstream systems are unavailable
- Fallback to human queue on repeated failure
- Agent health check endpoint exposes status to monitoring tools
- **Implemented by:** retry.py + circuit_state.json, health_check.py :8080 (Epic 11)

**Client-facing deliverable:** Responsible AI one-pager HTML (to be built in Epic 32) — maps our 6 pillars to client's regulatory requirements. Directly answers the "what if the agent makes a mistake?" objection.

---

## Cross-Framework Matrix

How the frameworks intersect at the blueprint level:

```
Blueprint
 ├── Industry (which vertical)
 ├── APQC Function + Process (where in the value chain)
 ├── Capability Types (what cognitive work — up to 6)
 ├── Authority Level (LOW / MEDIUM / HIGH)
 ├── Size Fit (SMB / MID / ENT / ALL)
 ├── Features used (from Feature Library)
 ├── Systems integrated (from Systems registry)
 └── KPIs (from Value Measurement Framework)
```

**Pre-sales qualification layer (frameworks applied before build):**
```
Prospect
 ├── Industry → Regulatory Complexity Score (F15)
 ├── Size → Company Size Tier (F5) → Engagement Model Tier (F8)
 ├── Data → Data Readiness Score (F11)
 ├── Systems → Integration Complexity (F14)
 ├── Target maturity → Agent Maturity Model (F10)
 ├── Stakeholders → Persona Framework (F12) → communication assets
 ├── Value case → ROI Category Framework (F13)
 └── Build priority → Prioritization Framework (F16)
```

---

## F18 — Pilot Lifecycle Framework

**Purpose:** Tracks each agent blueprint's development stage from spec to live production deployment. Determines when a blueprint is ready for client system hook-up.

### The 6 Stages

| Stage | Code | Definition | Exit Gate |
|---|---|---|---|
| 0 | blueprint | Spec in DB, decision logic documented, no code | Scaffold generated from blueprint spec |
| 1 | scaffolded | Boilerplate code generated, agent_runner wired up | Business logic implemented, test scenario executable |
| 2 | sandbox | Runs against mock systems (Mock SAP/MES), dry-run passes, outputs reviewed internally | All test scenarios pass; outputs make business sense |
| 3 | validated | Human stakeholder has reviewed outputs, authority level confirmed, decision rules signed off | Client system access confirmed + compliance cleared |
| 4 | pilot_ready | Connected to client systems, pre-prod test with real data passed, oversight SOP documented | Go-live decision by client stakeholder |
| 5 | production | Running live, scheduled/event-triggered, monitored, value measurement active | N/A |

### Authority Level Modifiers

| Authority | Sandbox → Validated Gate | Validated → Pilot-Ready Gate |
|---|---|---|
| LOW | Output review by one internal person | Standard integration test |
| MEDIUM | Business owner sign-off on decision rules | Stakeholder approval + test run with real data |
| HIGH | Legal/compliance review + escalation path documented | Formal go-live approval + human-in-the-loop SOP |

### Client Hook-Up Criteria (Validated → Pilot-Ready)
1. Integration pattern confirmed (REST API / SAP BAPI / file drop / DB read)
2. Credentials and access provisioned in non-production environment
3. Data sample tested (even read-only) — outputs validated against real data
4. Oversight procedure documented (who reviews, what escalation path, rollback plan)
5. For regulated industries (HEALTH, FS, ENERGY, PUBLIC): compliance officer sign-off

### Platform Current State (as of 2026-03-14)
- 3 blueprints at `sandbox` stage (CG pilot agents)
- 37 blueprints at `blueprint` stage
- 0 at `pilot_ready` or `production`

---

## F19 — Persona Dashboard Quality Framework

**Purpose:** A structured method for designing and evaluating persona dashboards. Prevents dashboards becoming status displays instead of workflow tools. Every dashboard feature must serve a defined Job-to-be-Done for its persona.

**How we use it:** Dashboard design (what to build), feature prioritization (Epic 41 stories), and ongoing quality assessment using the 5-dimension eval rubric.

---

### The 5-Dimension Eval Rubric

Score each dashboard 1–4 per dimension. Max 20 per dashboard.

| Dimension | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| **D1 Narrative Clarity** | No context | Role-labelled, generic | Clear KPI story | Before/after agent value story |
| **D2 Interactivity Depth** | View only | One action (Run) | Run + approve/reject | Run + decide + filter + drill-down |
| **D3 Human-in-the-Loop** | None | Buttons, no feedback | Full decision flow | Full flow + audit trail + toast |
| **D4 Data Believability** | Hardcoded | Plausible, not consistent | Live API, consistent | Live + cross-dashboard coherence |
| **D5 Persona Fit** | Generic | Role-labelled, generic content | Role-relevant KPIs + actions | Exactly what this buyer opens first |

**Thresholds:** ≥ 18 = A (demo-ready), 15–17 = B (solid), 10–14 = C (needs work), < 10 = D (display only)

---

### The Design Rule

Before building any dashboard feature, answer:

> *"Which Job-to-be-Done does this serve? Which dimension does it lift?"*

If you cannot answer both, do not build it.

---

### Jobs-to-be-Done Per Persona

Every persona has a 30-minute demo flow: open → triage → act → confirm → close. Features exist to make that flow work end-to-end.

#### P1 — Operations Manager (Sarah Chen)
*Primary question when she opens the dashboard: "What decisions do I need to make right now?"*

| # | Job | Signal that it's working |
|---|---|---|
| J1 | Triage overnight events | Impact narrative shows exactly what happened + what needs a decision |
| J2 | Review at-risk SKUs | SKU table sorted by days-cover; one click to full context |
| J3 | Approve PRs with context | Decision cards show cost, supplier, lead time, risk of rejection |
| J4 | Understand demand signals | Interactive forecast chart; drill into model reasoning |
| J5 | Escalate or override | Escalate button + forecast override with note |

#### P2 — Finance Controller (Michael Torres)
*Primary question: "What is the agent committing on my behalf, and is it within budget?"*

| # | Job | Signal that it's working |
|---|---|---|
| J1 | Review agent spend commitments | Recommendation list shows total value committed this week |
| J2 | Enforce budget gates | Budget gate modal before approving above threshold |
| J3 | Track ROI vs. business case | Actuals vs. projected savings chart from value_tracking |
| J4 | Flag anomalies and exceptions | Auto-surfaced exception flags on recommendation cards |
| J5 | Understand commitment timing | Commitment calendar showing agent-recommended spend by week |

#### P3 — Compliance Officer (Dr. Aisha Patel)
*Primary question: "Is everything that happened today audit-ready and within authority bounds?"*

| # | Job | Signal that it's working |
|---|---|---|
| J1 | Triage CAPA queue by severity | Critical items at top; severity badge + affected line visible |
| J2 | Review evidence before signing | CAPA evidence panel: full event record + agent reasoning |
| J3 | Sign off with traceability | Decision stored with timestamp, authority level, and SOP reference |
| J4 | Export decision record | One-click audit trail export (print-ready HTML) |
| J5 | Monitor RAI authority bounds | Per-agent authority monitor: actions taken vs. approved limit |

#### P4 — IT Technical Lead
*Primary question: "Are the integrations stable and are agents running within spec?"*

| # | Job | Signal that it's working |
|---|---|---|
| J1 | Confirm system health before runs | SAP/MES/DB connection lights update automatically every 30s |
| J2 | Investigate a failed run | Payload inspector: raw input + output + error per run row |
| J3 | Track latency trends | Sparkline per agent; threshold alert if avg > 5s |
| J4 | Confirm decision auditability | Every recommendation links to a run_id and a decided_at timestamp |
| J5 | Respond to an incident | Failed run modal: which call failed, blast radius, suggested fix |

#### P5 — C-Suite Executive
*Primary question: "Are agents delivering value and are we expanding in the right direction?"*

| # | Job | Signal that it's working |
|---|---|---|
| J1 | Get a portfolio pulse in 60 seconds | Live KPI strip: active agents / total recommendations / approved / value realized |
| J2 | See decision oversight at a glance | "Agent Decisions This Month" panel: approved/rejected/pending counts |
| J3 | Understand expansion readiness | "Ready to advance" flags on sandbox agents with value-unlock estimate |
| J4 | Check for risk or authority breach | Per-agent authority status summary (within bounds / approaching / exceeded) |

#### P6 — Cross-functional (Action Queue)
*Primary question: "What decisions are waiting for me across all agents and all roles?"*

| # | Job | Signal that it's working |
|---|---|---|
| J1 | See all pending decisions in one place | Merged approvals + recommendations, sorted by urgency |
| J2 | Filter to my role's items | Role-aware filter: Viewing as Operations / Compliance / Finance |
| J3 | Decide with one click | Accept/Reject buttons with visual feedback + toast |
| J4 | Review what was already decided | Recently Decided collapsible panel |

#### P7 — Lifecycle Manager (Pipeline)
*Primary question: "What needs to happen to advance agents toward production?"*

| # | Job | Signal that it's working |
|---|---|---|
| J1 | See where every agent is in its lifecycle | Kanban: 6 columns, agent cards with current stage |
| J2 | Advance an agent safely | Gate modal with checklist before confirming stage advancement |
| J3 | Understand business impact of advancing | Value-unlock estimate on each agent card |
| J4 | Prioritize which agents to advance | Cards show estimated value + complexity + current blocker |

---

### Feature Design Test

Before writing a story for any dashboard feature, apply this test:

```
Feature: [name]
Serves persona: [P1–P7]
Job-to-be-Done: [J#]
Dimension lifted: [D1–D5, from N to M]
Without this feature, the demo breaks at: [specific moment in 30-min flow]
```

If you cannot complete the last line, the feature is not necessary yet.

---

### Dashboard Scores (March 2026 baseline)

| Dashboard | D1 | D2 | D3 | D4 | D5 | Total | Grade |
|---|---|---|---|---|---|---|---|
| Operations | 2 | 3 | 3 | 2 | 2 | 12 | C |
| Finance | 2 | 1 | 1 | 1 | 2 | 7 | D |
| Compliance | 3 | 2 | 4 | 2 | 3 | 14 | C |
| Agent View | 4 | 3 | 3 | 3 | 3 | 16 | B |
| Enterprise | 2 | 1 | 1 | 1 | 1 | 6 | D |
| IT Health | 3 | 2 | 2 | 2 | 3 | 12 | C |
| Pipeline | 3 | 2 | 1 | 2 | 3 | 11 | C |
| Action Queue | 4 | 4 | 3 | 2 | 2 | 15 | B |

**Platform avg: 11.6 / 20. Target avg: 16 / 20 after Epic 41.**

**Evaluation tool:** `dashboards/eval.html` — live scorecard with dimension breakdown, gap analysis, and priority fix list.

---

## F20 — Client Profile Schema

**What it is:** The standard 8-dimension structure for profiling any prospect or client. Once populated, the profile drives automatic generation of fit-for-purpose presentations, agent shortlists, demo paths, and client engagement portals. Every client engagement starts with a completed F20 profile.

**How we use it:** The `?client=` URL parameter in the portal reads the client's slug and pulls all content from their F20 profile. Pitch deck customization, blueprint shortlist filtering, and demo path selection all derive from the 8 dimensions below.

---

### The 8 Profile Dimensions

| # | Dimension | Field | Values / Scale | Purpose |
|---|---|---|---|---|
| 1 | Company Name | `name` | Free text | Personalisation across all outputs |
| 2 | Size Tier | `size_tier` | SMB / MID / ENT | Engagement model, blueprint filter, pricing tier |
| 3 | Industry Code | `industry_code` | CG / MFG / PHARMA / FS / RETAIL / HEALTH / ENERGY / LOGISTICS / TELECOM / AUTO / TECH / CONST / PUBLIC | Blueprint shortlist, regulatory defaults, system landscape |
| 4 | Business Model Type | `business_model` | ETO / MTO / MTS / Distribution / Service / SaaS | Agent opportunity shape — see table below |
| 5 | Regulatory Complexity Score | `regulatory_score` | 1–5 (from F15) | Authority level defaults, compliance overhead in engagement model |
| 6 | Integration Complexity Tier | `integration_tier` | T1 / T2 / T3 / T4 (from F14) | Timeline, cost, technical risk in proposal |
| 7 | Data Readiness Score | `data_readiness_score` | 5–25 (from F11) | Go/no-go for pilot, scoping of data remediation work |
| 8 | Recommended Engagement Tier | `engagement_tier` | Discovery / Pilot / Platform | Commercial package recommendation driven by dimensions 2, 5, 6, 7 |

---

### Business Model Types — Agent Implication Table

| Code | Name | Description | High-Value Agent Types | Lower-Value Agent Types |
|---|---|---|---|---|
| **ETO** | Engineer-to-Order | Every product custom-designed per client spec. No standard SKUs. Order triggers design → BOM → procurement → fabrication. | RFQ-to-Quote, BOM generation, specialty material requisition, quality compliance pre-fab, order milestone tracking | Standard replenishment (no standard SKUs), demand forecasting (lumpy project demand) |
| **MTO** | Make-to-Order | Products assembled from standard components per customer order. BOM is largely fixed; variety comes from configuration. | Order configuration validator, component availability checker, promise-date agent, work order creation | Long-range demand forecasting (order-triggered), shelf replenishment |
| **MTS** | Make-to-Stock | Products manufactured to a forecast, held in inventory, shipped on order. Standard SKUs, demand-driven. | Demand forecast, replenishment, inventory optimization, stockout prevention, markdown agent | RFQ-to-Quote (products are catalogue), custom BOM (fixed BOMs) |
| **Distribution** | Distribution | Buy, store, and sell products from third-party manufacturers. Asset-light. | Supplier fill rate monitor, inbound PO tracker, carrier performance, dynamic pricing, invoice reconciliation | Manufacturing quality agents, work order agents, fabrication scheduling |
| **Service** | Service / Professional Services | Revenue from time and expertise, not physical product. Utilisation and billing are core. | Utilisation tracker, billing milestone agent, scope change alert, resource allocation optimizer, client health score | Manufacturing agents, inventory agents, physical supply chain |
| **SaaS** | Software as a Service | Subscription revenue, digital product, recurring billing. Churn and expansion are core commercial metrics. | Customer health score, churn risk predictor, expansion signal detector, support triage, license optimization | Physical supply chain, manufacturing, procurement (mostly vendor SaaS spend) |

**Design implication:** Before selecting agent blueprints for a client, confirm their business model type. Recommending a replenishment agent to an ETO manufacturer or a custom BOM agent to an MTS company signals a failure to understand the business.

---

### How the F20 Profile Drives Platform Outputs

**1. Client portal `?client=` parameter**
The portal reads `clients/{slug}/profile.json` (an F20-structured file) and renders a personalised engagement view. Each of the 8 dimensions maps to a visible section of the portal — company profile scorecard, agent shortlist (filtered by business model + integration tier), recommended pilot (based on data readiness + size tier), and engagement model recommendation (based on all 8 dimensions combined).

**2. Pitch deck customization**
The deck generator reads the F20 profile and:
- Selects the correct industry slide (from the 13 industry blueprints)
- Filters the agent opportunity slides to those matching the business model and size tier
- Sets the engagement model recommendation slide to the correct tier
- Personalises the ROI framing to the dominant ROI category (Hard Savings for MID/ENT; Soft Savings for SMB)

**3. Blueprint shortlist filtering**
The blueprint viewer accepts `industry_code`, `size_tier`, and `business_model` as filter inputs. The F20 profile pre-populates these, so the shortlist opens with only the relevant blueprints shown.

**4. Demo path selection**
The demo path (which agents to run live, which dashboards to show, which persona to lead with) is derived from the business model type and regulatory score:
- ETO + regulatory_score ≥ 4 → Lead with quality compliance agent + compliance persona dashboard
- MTS → Lead with replenishment agent + operations persona dashboard
- Service/SaaS → Lead with customer health / churn agent + enterprise persona dashboard
- regulatory_score = 5 → Always include compliance officer persona + RAI pillar one-pager

---

### Example: Kimre Inc. — F20 Profile Completed

| Dimension | Value | Notes |
|---|---|---|
| Company Name | Kimre Inc. | Mist eliminators, drift eliminators, coalescers, scrubber packing |
| Size Tier | MID | 21–50 employees, privately held — small for MID but ETO complexity justifies classification |
| Industry Code | MFG | Industrial Manufacturing — fertilizer, petrochemical, power generation markets |
| Business Model | ETO | Every product custom-engineered per customer specification; no catalogue SKUs |
| Regulatory Score | 4 / 5 | Products must meet EPA/OSHA emissions standards for client's regulated processes |
| Integration Tier | T2 | Likely Sage or QuickBooks ERP, custom quoting tool; no API sandbox available — batch/JDBC expected |
| Data Readiness Score | 14 / 25 | Strong product and order data; weak demand forecasting due to lumpy project-based demand |
| Engagement Tier | Pilot | Sufficient data readiness + clear ETO agent opportunity + T2 integration = Pilot recommended |

**Agent shortlist derived from this profile:**
1. Material Requisition Agent (ETO + T2 + MID → MEDIUM authority, existing blueprint) — **Pilot**
2. RFQ-to-Quote Agent (ETO → quote/BOM high value) — **Next Wave**
3. Quality Compliance Checker (regulatory_score = 4 → pre-fab validation) — **Next Wave**
4. Order Milestone Notifier (ETO = long customer wait → proactive comms high value) — **Platform**
5. Retrofit/Reorder Opportunity Agent (known product service life → repeat revenue) — **Platform**

**DB reference:** `clients` table, `slug = 'kimre'`. Profile JSON at `clients/kimre/profile.json`.

---

## F21 — Dashboard Specification Framework

**What it is:** A structured 5-artifact system that enables autonomous dashboard generation. With all 5 artifacts in a subagent's prompt, a dashboard can be built to a defined quality standard without iterative human review. Complements F19 (quality rubric) and F20 (client profile) as the production specification layer.

**When to use it:** Before commissioning any new persona dashboard. All 5 artifacts must exist before a dashboard agent is launched. This prevents blank-screen dashboards, generic placeholder data, and persona misalignment.

---

### The 5 Required Artifacts

| # | Artifact | Purpose | Format |
|---|---|---|---|
| 1 | **Persona Brief** | Who uses this dashboard, what they do daily, their top 5 Jobs-to-be-Done, 3 pain points, success metrics | Markdown table + narrative |
| 2 | **Jobs-to-be-Done Spec** | For each JTBD: trigger event, current friction, desired outcome, agent opportunity, UI component that solves it | Per-JTBD table rows |
| 3 | **Data Contract** | Which API endpoints the dashboard fetches + response shape + hardcoded fallback data for each endpoint | Endpoint table + JSON shapes |
| 4 | **Component Palette** | Inventory of all reusable UI patterns available (KPI strip, run theater, sortable table, detail panel, sparklines, decision cards) with CSS class names and JS function signatures | Reference table (see COMPONENTS.md) |
| 5 | **Quality Gates** | Per-dimension minimum score from F19 rubric (D1–D5) that this dashboard must achieve before it is considered complete | Dimension table with target scores |

**If any artifact is missing:** The dashboard agent must generate that artifact first, or request it from the orchestrator, before writing any HTML.

---

### Minimum Quality Gate (All Dashboards)

| Dimension | Minimum Score | What it requires |
|---|---|---|
| D1 Narrative Clarity | 3 | Clear KPI story: impact narrative naming the persona, what changed, what needs a decision |
| D2 Interactivity Depth | 3 | Run button + approve/reject decision flow + at least one filter |
| D3 Human-in-the-Loop | 3 | Full decision flow: accept/reject/escalate with visual feedback + toast confirmation |
| D4 Data Believability | 3 | API fetch with offline fallback; 8–15 realistic mock records; no Lorem Ipsum |
| D5 Persona Fit | 4 | Content and actions exactly match what this buyer opens first; no generic placeholder labels |

**Target total: ≥ 16 / 20 (Grade B or above)**

---

### F21 Template — Persona Brief

```
## [Persona Name] — [Role Title]

**Name:** [Fictional name]
**Role:** [Title, function]
**Reports to:** [Manager/owner]
**Daily routine:** [Hour-by-hour schedule showing when they interact with agents]

### Top 5 Jobs-to-be-Done

| # | Job | Trigger | Current friction | Desired outcome | Agent opportunity |
|---|---|---|---|---|---|
| J1 | | | | | |
| J2 | | | | | |
| J3 | | | | | |
| J4 | | | | | |
| J5 | | | | | |

### Pain Points
1. [Pain point 1]
2. [Pain point 2]
3. [Pain point 3]

### Success Metrics
- [Metric 1]
- [Metric 2]
- [Metric 3]

### Agents serving this persona
| Agent | Status | Dashboard |
|---|---|---|
| [Agent name] | pilot / mock / planned | [dashboard file] |
```

---

### F21 Template — Data Contract

```
## Data Contract — [Dashboard Name]

| Endpoint | Method | Returns | Fallback |
|---|---|---|---|
| /api/run/[slug] | POST | {outcome, summary, run_id, recommendations: [{id, rec_type, item_label, urgency, recommended_action}]} | Hardcoded demo run result |
| /api/recommendations/pending | GET | [{id, slug, rec_type, item_label, urgency, recommended_action, decision}] | 3 hardcoded pending items |
| [client-specific endpoint] | GET | {items: [...]} | Hardcoded 8–15 realistic records |
```

---

### F21 in Practice — Kimre Example

The Kimre engagement was the first full F21 implementation. Five personas were defined (Alex Torres / Sales, Sam Rivera / Engineering, Jordan Kim / Customer Service, Mary Gaston / Executive, Pat Chen / QA), each with a complete persona brief, JTBD table, data contract, and quality gates. Five dashboards were built against these specs: `clients/kimre/sales.html`, `engineering.html`, `customer-service.html`, `executive.html`, `quality.html`. Each was built autonomously by a subagent with no iterative review because all 5 F21 artifacts were pre-defined.

**Reference:** `clients/kimre/personas.md` — complete F21 artifact set for Kimre.

---

### Relationship to Other Frameworks

```
F20 (Client Profile) → identifies which personas need dashboards
F21 (Dashboard Specification) → defines what each dashboard must contain
F19 (Quality Rubric) → evaluates whether the built dashboard meets the spec
```

---

## 22. Manufacturing Strategy Framework

**What it is:** A classification system for how a manufacturer produces and delivers its products. Determines which agents are relevant, what data model to use (project-order vs. SKU), and how inventory and capacity should be managed.

**How we use it:** Informs blueprint selection, agent design, and client portal data models. A client's manufacturing strategy determines whether they need ETO-style project agents or MTS-style inventory agents — or both (hybrid).

### Manufacturing Modes

| Mode | Full Name | Definition | Lead Time | Inventory | Agent pattern |
|---|---|---|---|---|---|
| ETO | Engineer-to-Order | Design + build custom to spec per order | Weeks–months | Raw material only | RFQ→Spec→BOM→Fabrication agents |
| MTO | Make-to-Order | Build from standard design to specific order | Days–weeks | WIP components | Order→BOM→Fab agents; some component stock |
| MTS | Make-to-Stock | Build to forecast; ship from finished goods inventory | Hours–days | Finished goods | Inventory replenishment, demand forecast agents |
| ATO | Assemble-to-Order | Standard modular components assembled per order | Days | Component stock | Configuration + assembly scheduling agents |
| Distribution | Resell without manufacturing | Buy from supplier, sell with/without value-add | Hours–days | Finished goods (3rd party) | Procurement, order management, supplier agents |

### Key Classification Dimensions

| Dimension | What to ask | Impact on platform |
|---|---|---|
| **Decoupling point** | Where does the customer order enter the supply chain? | Determines inventory investment and agent trigger points |
| **Volume × Variety** | High variety + low volume = ETO; Low variety + high volume = MTS | Blueprint selection |
| **Lead time target** | What does the market expect? | Determines where capacity and data latency matter |
| **Custom design effort** | Hours of engineering per order? | Application engineering agents vs. catalog agents |
| **Repeat vs. unique** | Are customers reordering the same thing? | Retrofit/reorder agents vs. always-new-spec agents |

### Hybrid Manufacturing (e.g., Kimre)

Many manufacturers operate multiple modes simultaneously. For example:
- **Kimre**: ETO (B-GON®, LIQUI-NOMIX® custom mist eliminators) + MTO (standard fiber bed cages) + MTS (KON-TANE® packing, fiber media)

In hybrid cases:
1. Classify each product family separately
2. Design different agent flows per lane
3. The client portal should reflect both (project orders + catalog SKUs)
4. Capacity planning must balance both demand patterns

### Relationship to Other Frameworks

```
F20 (Client Profile) → business_model_type field now supports multi-mode (ETO+MTO+MTS)
F22 (Manufacturing Strategy) → informs which blueprint lane applies per product
F23 (Business Model) → manufacturing mode is one dimension of the broader business model
```

---

## 23. Business Model Framework

**What it is:** A structured taxonomy of how a company creates, delivers, and captures value. Goes beyond manufacturing mode to include revenue structure, customer relationship type, and strategic expansion opportunities.

**How we use it:** During client profiling (F20), the business model classification determines which agent opportunities are most valuable, what the sales motion looks like, and what strategic expansion paths exist.

### Core Business Model Types

| Type | Revenue driver | Customer relationship | Agent opportunities |
|---|---|---|---|
| **ETO Custom** | Per-project revenue | Project-by-project, engineering-led | RFQ triage, spec gen, BOM creation, schedule optimization |
| **MTO/MTS Product** | Unit sales from catalog | Repeat-order, procurement-led | Inventory replenishment, demand forecast, reorder alerts |
| **Distribution** | Margin on resold product | Transactional, volume-driven | Supplier sourcing, margin optimization, order routing |
| **Service/Maintenance** | Recurring contracts, time & materials | Ongoing, relationship-driven | Maintenance scheduling, SLA monitoring, predictive service |
| **Performance Contract** | Outcome-based (efficiency, uptime guarantee) | Deep partnership, data-sharing | Monitoring agents, outcome tracking, intervention triggers |
| **Technology Licensing** | Royalty on IP use | Arm's-length, legal-structured | Compliance tracking, royalty calculation |
| **Digital/SaaS** | Subscription to software or data | Platform relationship, usage-driven | All agent types; platform itself is the product |
| **Hybrid** | Multiple above | Varies by product line | Mix of above |

### Business Model Expansion Pathways

A common strategic evolution for industrial manufacturers:

```
Stage 1: Product sales (ETO/MTS) → "we make things"
Stage 2: Add service layer → "we maintain what we made"
Stage 3: Add distribution → "we also supply complementary products"
Stage 4: Add performance contracts → "we guarantee outcomes"
Stage 5: Add digital layer → "we provide data, insights, customer portal"
Stage 6: Platform/ecosystem → "our customers' customers interact with our system"
```

Kimre's current position: Stage 1 (core) with Stage 2 opportunity (service/maintenance) and Stage 5 potential (customer-facing digital tools — asset dashboards, compliance trackers, order portals).

### Customer-Facing Digital (Stage 5)

A manufacturer offering digital tools to their own customers creates a second layer of value:

| Tool | What customer gets | What manufacturer gains |
|---|---|---|
| Asset performance dashboard | Real-time health of installed equipment | Installed base visibility, early retrofit signal |
| Predictive service alerts | "Your unit is due in 3 months" | Proactive sales, no cold outreach |
| Compliance tracker | EPA/regulatory performance against specs | Positioned as compliance partner, not just vendor |
| Customer order portal | Self-serve RFQ, order tracking, cert downloads | Reduces CS workload, faster customer experience |
| Replacement/reorder scheduler | Smart triggers for consumables (media, packing) | Predictable MTS revenue stream |

**Architecture note:** The internal agent platform (dashboards, pilot agents, server.py) is the foundation. Customer-facing tools are a read-optimized, permissioned view of the same data — not a separate system. A `customer_portal` flag on records controls what is visible externally.

### Relationship to Other Frameworks

```
F20 (Client Profile) → business_model_type field maps to this taxonomy
F22 (Manufacturing Strategy) → manufacturing mode is a sub-dimension of business model
F23 (Business Model) → used in pre-sales assessment (F31, planned) and strategic deck design
F24 (Business Model Reinvention) → applies F23 taxonomy through an assessment lens
```

---

## 24. Business Model Reinvention Framework (F24)

**What it is:** A structured assessment framework for evaluating strategic shifts in how a company creates, delivers, and captures value. Goes beyond identifying model types (F23) to scoring which moves are realistic, valuable, and worth sequencing.

**How we use it:** Powers the Business Model Assessment Agent (`pilot-agents/business_model_agent.py`). Generic agent reads `profile.json` and applies this framework. Client-specific agents (e.g., `pilot-agents/kimre/business_model_agent.py`) run with pre-configured move sets and industry context. Output surfaces in the Strategy tab of client portals.

### Assessment Dimensions

| Dimension | What it measures | Weight |
|---|---|---|
| **Market Attractiveness** | Size and growth of the target model's addressable revenue; competitive dynamics; customer demand signal | 30% |
| **Capability Fit** | What the company already has that transfers (people, systems, IP, brand); gap size to close | 30% |
| **Strategic Coherence** | Does this reinforce the core identity or dilute it? Does it leverage existing differentiation? | 25% |
| **Risk Profile** | Operational, financial, market, and regulatory risks of making the move (inverse scored — lower risk = higher score) | 15% |

Each dimension scored 1–5. Weighted composite score drives recommendation:

| Composite Score | Recommendation | Meaning |
|---|---|---|
| 4.0–5.0 | **Expand** | Strong case to move now; high value, low friction |
| 3.0–3.9 | **Pilot First** | Real opportunity but requires validation; start small |
| 2.0–2.9 | **Monitor** | Interesting but not yet ready; re-evaluate in 12–18 months |
| < 2.0 | **Defer** | Poor fit for current capabilities or market conditions |

### Agent Output Schema

```json
{
  "client": "<slug>",
  "current_model": ["ETO_Custom", "MTS_Catalog"],
  "moves_assessed": 5,
  "top_recommendation": "<move_id>",
  "items": [
    {
      "move": "<move_id>",
      "move_label": "Service / Maintenance Contracts",
      "market_attractiveness": 4,
      "capability_fit": 4,
      "strategic_coherence": 5,
      "risk_profile": 3,
      "composite_score": 4.05,
      "recommendation": "Expand",
      "narrative": "...",
      "risks": ["...", "..."],
      "year1_value_est": "$45K ARR from 10 accounts",
      "enabling_agents": ["retrofit-reorder-agent", "order-notifier-agent"]
    }
  ]
}
```

### Standard Move Set (Generic Agent)

| Move ID | Move | Best for |
|---|---|---|
| `service-maintenance` | Add service / maintenance contracts | ETO manufacturers with installed base |
| `mts-catalog` | Launch MTS product catalog | ETO manufacturers with repeatable product families |
| `digital-customer-portal` | Customer-facing digital layer | Any manufacturer with direct customer relationships |
| `distribution` | Add distribution of complementary products | Manufacturers with established customer relationships |
| `performance-contract` | Outcome-based pricing | Manufacturers with measurable, monitorable outcomes |
| `technology-licensing` | License proprietary technology | Manufacturers with defensible IP in non-competing geographies |
| `saas-tools` | Productize internal tools as external SaaS | Manufacturers with replicable technical tools (e.g., spec generators) |

### Agent Architecture

```
pilot-agents/business_model_agent.py           ← Generic: reads --client-profile <path>
pilot-agents/kimre/business_model_agent.py     ← Kimre-specific: DRY_RUN_MODEL_MOVES hardcoded
pilot-agents/<other_client>/business_model_agent.py  ← future client instances
```

### Relationship to Other Frameworks

```
F20 (Client Profile) → provides current_model and industry context for assessment
F22 (Manufacturing Strategy) → informs capability_fit scoring for production-related moves
F23 (Business Model) → provides the move taxonomy this framework assesses
F16 (Opportunity Prioritization) → same 2×2 logic applied at strategic model level vs. agent level
F21 (Dashboard Spec) → Strategy tab of client portal surfaces F24 agent output
```

---

## F25 — Regulatory Operations Framework

**What it is:** A classification system for domain-specific operational rule sets that agents must encode, respect, or defer to. Distinguishes between rules that are fully codeable into agent logic (deterministic), rules that require human judgment to apply (interpretive), and rules that require external validation before action (mandatory human checkpoint).

**Why it matters:** As agents operate in regulated industries, the hardest design question isn't "can the agent do this?" but "is the agent legally/contractually allowed to do this autonomously?" F25 gives a consistent vocabulary for that question across every industry we serve.

**How we use it:** Every agent spec (docs/agents/*.md) should classify each of its decision points against this framework. The authority level (F4) governs *how much* autonomy an agent has; F25 governs *what kind* of rules constrain it. Together they define the HITL requirement.

### Rule Type Classification

| Type | Definition | Agent handling | Examples |
|---|---|---|---|
| **Deterministic** | Rule is fully specified, testable, and unambiguous | Agent executes autonomously | FAR Part 117 rest calculation (math), reorder point threshold (≤ stock), AP auto-approve limit (<£50K) |
| **Interpretive** | Rule requires judgment about intent, context, or edge cases | Agent recommends, human decides | FAR Part 117 "unforeseen circumstances" exception, CAPA root cause assignment, MEL category determination |
| **Mandatory Checkpoint** | Regulation or contract explicitly requires human sign-off regardless of clarity | Hard HITL gate — agent cannot proceed | FAA airworthiness directive compliance sign-off, controlled substance dispensing (pharma), AML Suspicious Activity Report filing, union contract overtime assignment |
| **Policy Rule** | Organizational policy (not external regulation) — enforceable by company | Agent executes within policy, flags exceptions | Spend approval thresholds, customer compensation limits (AAdvantage miles), quote discount authority |

### Regulatory Domains (by industry)

| Industry | Regulator(s) | Key rule sets | Rule type mix |
|---|---|---|---|
| Aviation | FAA, DOT, TSA, IATA | FAR Part 117 (duty/rest), Part 121 (operations), Part 135 (training currency), DOT consumer protection, AD compliance | Heavy deterministic (Part 117 math) + Mandatory checkpoints (AD sign-off) |
| Consumer Goods / MFG | EPA, OSHA | Chemical resistance compatibility, material certification, safety data sheet requirements | Mostly deterministic (lookup tables) |
| Pharmaceuticals | FDA | 21 CFR Part 11 (electronic records), GMP, controlled substance scheduling | Mandatory checkpoints dominate |
| Financial Services | FDIC, OCC, FinCEN, SEC | BSA/AML (SAR filing), credit decisioning, reg capital | Mandatory checkpoints (SAR) + interpretive (credit) |
| Healthcare | CMS, HIPAA, DEA | HIPAA PHI handling, prior authorization, controlled substance | All three types depending on context |

### Agent Design Rules

When designing an agent that touches regulated processes:

1. **Classify every decision point** against the four rule types above
2. **Deterministic rules** → encode in agent logic, unit-test, document the rule source (e.g., "FAR 117.23(b)")
3. **Interpretive rules** → agent presents evidence and recommended interpretation; human confirms
4. **Mandatory checkpoints** → hard HITL gate; agent pauses and cannot self-advance; logged with timestamp + decision-maker
5. **Policy rules** → configurable thresholds in agent constants (not hardcoded); client can tune without code change

### F25 in Practice — AA Crew IROPS Recovery Agent

The `aa-crew-irops-recovery-agent` touches all four rule types:

| Decision | Rule type | Agent handling |
|---|---|---|
| Calculate remaining duty hours for a reserve crew member | Deterministic | Agent computes: `max_duty - hours_since_rest_start` against FAR 117.23 table |
| Determine if augmented crew rules apply (long-haul) | Interpretive | Agent flags as "augmented crew candidate — confirm rest facility availability" |
| Apply "unforeseen circumstances" exception to extend duty period | Mandatory checkpoint | Hard HITL gate — Operations Manager must explicitly authorize and log justification |
| Override seniority order for assignment (union contract) | Policy rule | Agent flags as exception; Crew Scheduling Supervisor confirms |

### Relationship to Other Frameworks

```
F4 (Authority Levels) → governs how much autonomy; F25 governs what kind of constraints apply
F7 (Agent Blueprint) → HITL section should map each decision point to its F25 rule type
F17 (Responsible AI) → F25's Mandatory Checkpoint maps directly to RAI pillar: Human Oversight
F18 (Pilot Lifecycle) → validated → pilot_ready gate requires F25 classification for all decision points
F19 (Dashboard Quality) → HITL Design dimension (D3) scores are informed by F25 compliance
```

---

## F26 — Multi-Agent Coordination Framework

**What it is:** A design framework for scenarios where multiple agents share a triggering event, exchange state, or must coordinate on a shared workflow. Defines handoff patterns, shared state models, conflict resolution rules, and orchestration topologies.

**Why it matters:** Single-agent design is straightforward. Multi-agent design introduces new failure modes: race conditions, conflicting recommendations, duplicated actions, and broken handoffs. Without a consistent coordination pattern, multi-agent systems become unpredictable.

**How we use it:** Applied when designing systems where ≥2 agents are triggered by the same event, produce outputs the other consumes, or share authority over the same resource (flight, order, crew member, patient, invoice).

### Coordination Topologies

| Topology | Pattern | When to use | Example |
|---|---|---|---|
| **Independent parallel** | Same trigger, separate outputs, no shared state | Agents serve different personas with no interdependency | Monica's IROPS reaccommodation (passengers) + Carlos's crew IROPS recovery (crew) triggered by same flight cancellation — outputs are separate |
| **Sequential pipeline** | Agent A output is Agent B input | One agent must complete before next is meaningful | Research Agent identifies prospect → Marketing Agent drafts outreach using prospect intel |
| **Supervisory** | Orchestrator agent delegates to specialist agents, aggregates results | Complex tasks with multiple specialist domains | Orchestrator runs replenishment + demand forecast + quality CAPA; combines into portfolio summary |
| **Competitive** | Multiple agents propose solutions to same problem; human picks | When different approaches have different tradeoffs worth comparing | Two pricing agents (conservative vs. aggressive) both produce fare class recommendations; RM analyst chooses |
| **Collaborative** | Agents share a mutable state object; each updates their slice | When a single "case" evolves through multiple specialist reviews | IROPS event record: OCC agent updates passenger status, crew agent updates crew status, CX agent updates notification status — all on one IROPS case object |

### Shared State Design

When agents share state (Collaborative topology), define the canonical state object:

```json
{
  "event_id": "IROPS-20260315-AA100",
  "event_type": "cancellation",
  "flight": "AA100 JFK-LAX 2026-03-15",
  "declared_at": "2026-03-15T14:30:00Z",
  "agents_involved": ["aa-irops-reaccommodation-agent", "aa-crew-irops-recovery-agent"],
  "passenger_state": {
    "affected": 247,
    "reaccommodated": 189,
    "pending": 58,
    "last_updated_by": "aa-irops-reaccommodation-agent",
    "last_updated_at": "2026-03-15T14:45:00Z"
  },
  "crew_state": {
    "open_trips_created": 3,
    "covered": 2,
    "escalation_required": 1,
    "last_updated_by": "aa-crew-irops-recovery-agent",
    "last_updated_at": "2026-03-15T14:47:00Z"
  },
  "resolution_status": "in_progress"
}
```

This object lives in the DB (or a shared event table) and each agent reads/writes only its own slice.

### Conflict Resolution Rules

When agents could conflict (e.g., two agents both recommend reassigning the same crew member to different trips):

| Rule | Implementation |
|---|---|
| **Lock before write** | Agent claims a resource (crew ID, seat, PO slot) before recommending; lock expires after HITL timeout |
| **Priority by authority** | Higher F4 authority level wins if agents conflict on the same resource |
| **Human arbitration gate** | If conflict detected, pause both and surface to human with both options |
| **First-write wins** | Simpler: first agent to recommend gets priority; second agent is informed and re-plans |

### Orchestrator Pattern (current implementation)

The existing `pilot-agents/orchestrator.py` uses the **Supervisory topology** with independent parallel sub-agents. Current limitations:
- No shared state — agents cannot read each other's outputs
- No conflict detection — if two agents affect the same DB resource, last write wins
- No inter-agent messaging — agents are black boxes to each other

**Upgrade path to F26-compliant orchestrator:**
1. Introduce an `events` table in the DB (shared state store)
2. Agents write their outputs to the event record (not just their own run table)
3. Orchestrator detects conflicts before surfacing recommendations
4. HITL dashboard shows the combined event view (not per-agent views)

### F26 in Practice — AA IROPS Event

AA's IROPS scenario is the platform's first F26 use case:

```
Trigger: Flight AA100 cancelled
  ↓
Independent parallel (Phase 1 — current design):
  ├── aa-irops-reaccommodation-agent → passenger rebooking recommendations
  └── aa-crew-irops-recovery-agent → crew coverage recommendations

  Monica's OCC dashboard shows passenger queue
  Carlos's crew scheduling dashboard shows coverage queue
  No shared state — they're independent

Collaborative (Phase 2 — F26 upgrade):
  ├── Shared IROPS event object in events table
  ├── Both agents write to their slice of the event
  ├── OCC dashboard shows combined event view
  ├── Conflict detection: if same crew member appears in both passenger
  │   (deadhead to cover another flight) AND crew (cover open trip),
  │   flag for human arbitration
  └── Resolution status tracks closure across both passenger + crew dimensions
```

### Relationship to Other Frameworks

```
F4 (Authority Levels) → determines which agent wins conflicts; HIGH authority can override MEDIUM
F17 (Responsible AI) → Accountability pillar requires audit trail of all agent-to-agent handoffs
F18 (Pilot Lifecycle) → multi-agent systems require additional validated → pilot_ready criteria
F25 (Regulatory Operations) → Mandatory checkpoints must be enforced even in multi-agent pipelines
F7 (Agent Blueprint) → add "Coordination" section to blueprint spec for multi-agent agents
```

---

## F27 — The Michael Principle

**What it is:** The standing question that structurally prevents any layer from claiming the God position. "Who is like God?" (*Mi ka-El* in Hebrew) is not rhetorical — it is the architectural rule that defines hierarchy. Michael defeated Lucifer not with superior power but with a question that exposed the absurdity of the claim to self-authority.

Applied to agent systems: any layer that stops receiving correction from above — that treats its own patterns as self-authorizing — has made the Luciferian move. It will optimize its own metrics while reality diverges.

**The three rules:**
1. **Human consciousness is unconditionally above the Agent Mind.** Every output is a recommendation, never a verdict. The system proposes; the person disposes.
2. **Ground truth = user perception.** When the user says "this doesn't match what I see," that is ground truth — regardless of what internal metrics say. The false-done rate (F9 Sacrificial metric) is how this is measured.
3. **The correction cycle never closes.** A pattern at maturity 5 is the most proven currently, not finished. Quarterly review is mandatory. Any pattern that claims to be beyond review has left the participation chain.

**Business translation:** "Human judgment is unconditionally above the Agent Mind. There is no configuration in which the Agent Mind makes a final call without human review on anything that matters. This is not a limitation — it is the design. It is what makes the system trustworthy."

**The CAiO's standing question:** In every session: "Is this pattern recommending something it was taught, or has it started generating rules on its own?" Any pattern that cannot be traced to a specific human correction is a candidate for review.

**When F27 is violated:**
- Agent auto-approves a HIGH authority action without human sign-off
- False-done rate climbs without detection or response
- Pattern promotions happen without CAiO review
- System confidence scores override user corrections

**Relationship to other frameworks:**
```
F4 (Authority Levels) → F27 is the philosophical grounding for why HIGH authority requires human sign-off
F9 (Value Measurement) → Sacrificial metric (false-done rate) is the primary F27 violation indicator
F10 (Agent Maturity) → F27 sets the ceiling: no agent reaches L5 autonomy — human is permanently above
F17 (Responsible AI) → F27 is the Accountability pillar's philosophical foundation
F18 (Pilot Lifecycle) → Correction cycle from F27 is the mechanism that advances agents through lifecycle stages
```

---

## F28 — WHY / WHAT / HOW Meta-Framework

**What it is:** The meta-layer above F1-F27. While F1-F27 structures the *platform architecture*, F28 structures the *analytical reasoning* applied to any engagement. It answers: what are we trying to understand, in what depth, and how do we prove it?

**The three layers:**

| Layer | Question | Contents | F1-F27 Mapping |
|---|---|---|---|
| **WHY** | Should anyone care? | Strategic context, regulatory drivers, competitive pressure, executive outcomes that matter | F15 (Regulatory Complexity), F2 (Industry Verticals), F23 (Business Model) |
| **WHAT** | What specifically is the value? | Cost dimensions, operational dimensions, risk dimensions — quantified with dual methodology | F13 (ROI Category), F16 (Opportunity Prioritization), F9 (Value Measurement) |
| **HOW** | Can we do it? Can we prove it? | Data readiness, integration complexity, pilot structure, authority design, evidence quality | F11 (Data Readiness), F14 (Integration Complexity), F4 (Authority Levels), F18 (Pilot Lifecycle) |

**Cross-cutting lenses (span all three layers):**
- **Stakeholder lens** — who cares about which layer? (maps to F12 Stakeholder Personas)
- **Phasing lens** — what depth is required at discovery vs. pilot vs. platform?
- **Maturity ladder** — L0 (defined) → L1 (questions listed) → L2 (frameworks built) → L3 (evidence gathered) → L4 (validated) → L5 (complete and defensible)
- **Decision tree** — full opportunity space mapped before narrowing to pilot recommendation

**The Coverage Matrix (the most powerful F28 artifact):**

A grid of analytical dimensions (rows) versus engagements or client contexts (columns), with L0-L5 maturity per cell. It shows — at a glance — what is proven vs. assumed:

| Dimension | Glock | Kimre | AA | Platform Default |
|---|---|---|---|---|
| WHY: Regulatory driver | L4 | L3 | L5 | L2 |
| WHY: Business model fit | L3 | L4 | L3 | L1 |
| WHAT: Cost opportunity (top-down) | L3 | L2 | L2 | L1 |
| WHAT: Cost opportunity (bottom-up) | L1 | L1 | L0 | L0 |
| HOW: Data readiness | L4 | L3 | L2 | L2 |
| HOW: Pilot scope | L3 | L4 | L2 | L2 |

**What F28 produces in a discovery sprint:**
1. WHY analysis → why this client, why now, what regulatory or competitive pressure is acute
2. WHAT analysis → which cost pools are addressable, dual-methodology value estimates with convergence
3. HOW analysis → data readiness score, pilot recommendation, authority level design
4. Coverage matrix → honesty about L0 vs. L4 dimensions — never claim L4 depth on an L1 analysis

**Discovery sprint discipline:** The Glock analysis implicitly used F28 — F15 answered WHY (5/5 regulatory = compliance leads), F13+F16 answered WHAT (ranked opportunity table), F11+F4+F10 answered HOW (pilot pick + authority design). F28 makes this sequencing explicit and repeatable.

**Relationship to other frameworks:**
```
F1 (APQC PCF) → supplies the WHAT process taxonomy for cost pool identification
F11-F14 → supply the HOW assessment inputs
F15 (Regulatory Complexity) → primary WHY driver for regulated industries
F19 (Dashboard Quality) → F28 WHY/WHAT/HOW maps to dashboard sections (context → data → actions)
F27 (Michael Principle) → F28 HOW layer must include human authority design — F27 is a HOW constraint
```

---

## F29 — Question-Centric Research

**What it is:** A discipline for structuring analytical research. The failure mode of research-heavy engagements is leading with sources rather than questions — the analyst finds interesting data and builds the analysis around what they found, rather than what needs to be answered. F29 inverts this: every piece of research is attached to a question, and questions have decision status.

**The four research layers:**

| Layer | Contents | Purpose |
|---|---|---|
| **Research Questions** | Questions organized by F28 dimension (WHY/WHAT/HOW), with decision status per question | What we're trying to answer |
| **Evidence Log** | Flat, filterable list: finding, source, date, question it answers, finding type | What we found |
| **Source Index** | Document inventory: name, URL, verification path, reliability rating | Where it came from |
| **Internal Data Requests** | What can't be answered externally — needs client data, interviews, or system access | What we still need |

**Finding types (tag every Evidence Log entry):**
- **Parameter** — feeds a quantitative model (e.g., "ATF inspection fine = $10K per violation")
- **Narrative** — supports the story but doesn't change the number (e.g., "compliance teams report increasing inspection frequency")
- **Structural** — could change the analytical approach if true (e.g., "Glock outsources serialization — the agent opportunity disappears if confirmed")
- **Confidence** — validates or challenges an assumption (e.g., "industry benchmark: 85% of ATF violations are process, not product — confirms our framing")

**Question decision status:**
- **Open** — not yet answered
- **Answered** — evidence found, logged, sufficient
- **Blocked** — need internal data or client access to answer
- **Deprioritized** — out of scope for this engagement depth

**The discipline rule:** No number enters a value case without a corresponding Evidence Log entry tagged as Parameter. No structural claim is made without at least one Answered question supporting it. Estimates are explicitly labeled ESTIMATED with the assumption stated.

**In practice (Glock example):**
```
Q: What is the regulatory cost of an ATF compliance failure? [WHY]
  Status: Answered
  Evidence: ATF Schedule of Fees + legal precedent case (2019, GA manufacturer, $2.8M penalty)
  Finding type: Parameter

Q: What % of Glock's ATF audit findings are process failures vs. product failures? [WHAT]
  Status: Blocked — needs internal Glock audit records
  Finding type: Structural (if >70% process, automation captures most of the opportunity)
  Note: ESTIMATED at 80% process, consistent with industry benchmark; flag if Glock data differs

Q: Is Glock's ERP data structured enough for automated ATF reconciliation? [HOW]
  Status: Answered (partial) — public ITAR registration confirms ERP-linked export logs; serialization data confirmed in production records
  Finding type: Parameter (data readiness = 4/5)
```

**Relationship to other frameworks:**
```
F28 (WHY/WHAT/HOW) → Research Questions are organized by F28 dimension
F9 (Value Measurement) → Parameter findings feed the ROI model; must converge with F19 dual-methodology
F16 (Opportunity Prioritization) → Answered questions on data readiness and addressability feed the scoring
F11 (Data Readiness) → Blocked questions identify data readiness gaps
```

---

## F30 — Incrementality and Overlap Analysis

**What it is:** A discipline for value cases that involve multiple programs, agents, or initiatives targeting the same cost pool. Without overlap analysis, value cases overstate opportunity — each initiative claims 100% of the savings from a shared pool, creating a 2x or 3x overcount.

**When F30 applies:** Any engagement where:
- Multiple agents will act on the same process area
- The platform competes with or complements an existing automation initiative
- The client has existing RPA, analytics, or AI programs in the same function
- Different departments each claim credit for the same cost reduction

**The four-step process:**

**Step 1 — Map the claims:** List every program (existing and proposed) that targets the addressable cost pool. For each: name, sponsor, claimed savings, mechanism, timeline.

**Step 2 — Identify overlapping mechanisms:** Two programs overlap when they act on the same human time, same system bottleneck, or same error rate. Common overlap types:
- **Persona overlap** — same employee role is the target of both programs
- **Process overlap** — both programs touch the same process step
- **Metric overlap** — both programs improve the same KPI (e.g., FTE hours saved)

**Step 3 — Define the incrementality argument:** Incrementality = the marginal value added by this program *given* that others exist. Three standard incrementality sources:
- **Inference** — the agent makes better decisions than the existing rule (AI reasoning layer, not data layer)
- **Coverage** — the agent acts on cases the existing program misses (different data sources, edge cases)
- **Speed** — the agent acts faster, reducing the cost of delay (same decision, compressed timeline)

**Step 4 — Quantify the double-counting risk:**
```
Total addressable pool: £X
  Less: Non-addressable floor (F16 constraint floor): £Y
  = Addressable pool: £(X-Y)

  Less: Existing program captures (verified, not projected): £Z
  = Incremental opportunity for this program: £(X-Y-Z)

  × Efficiency gain from this program: % G
  = Year-1 incremental value: £(X-Y-Z) × G
```

**The discipline rule:** Never claim the full addressable pool without checking what existing programs have already claimed. The Sacrificial metric (F27/F9) version of overlap: claiming £500K when £200K is already captured by RPA is a false-done.

**Common mistake — the additive fallacy:** Summing all agent value cases and presenting the total as the platform opportunity. Each agent's value must be calculated on the *remaining* pool after upstream agents have acted. If Agent 1 reduces error rate from 12% to 3%, Agent 2's opportunity is on the 3% residual, not the original 12%.

**In practice (multi-agent Glock example):**
```
ATF Compliance Monitor → claims £582K from compliance labor + penalty avoidance
LE Contract Intelligence → claims £240K from contract admin + close rate
ITAR Export Monitor → claims £180K from export compliance labor

Question: Do these overlap?
  ATF + LE: minimal overlap (different processes, different personas — Compliance vs. Sales Ops)
  ATF + ITAR: PARTIAL overlap — both Compliance Officer role, some export documentation overlap
  Overlap estimate: ~£60K of ATF value also captured by ITAR (same staff, same hours)

Incrementality-adjusted total: £582 + £240 + (£180 - £60) = £942K
vs. Additive total: £1,002K
Double-counting risk: 6% — within acceptable range, but must be disclosed
```

**Relationship to other frameworks:**
```
F9 (Value Measurement) → F30 is a discipline applied to F9 outputs — never present F9 numbers without F30 check
F16 (Opportunity Prioritization) → F30 constrains the "Impact" dimension of F16 scoring
F13 (ROI Category) → Overlap often concentrates in the Efficiency category (same FTE hours claimed by multiple programs)
F26 (Multi-Agent Coordination) → F30 is the value-case companion to F26's operational coordination
F28 (WHY/WHAT/HOW) → F30 lives in the WHAT layer — it is a required step before finalizing the value estimate
```

---

## F31 — Feature Identification Chain

**What it is:** The process that connects a persona brief (F12) to a dashboard specification (F21). F31 answers: given who the user is and what they do every day, which features does their dashboard actually need — and why?

Without F31, features are added because they seem useful or because another dashboard has them. With F31, every feature traces back to a specific job, which traces back to a specific question, which traces back to a real persona's daily reality.

**The four-step chain:**

```
F12 Persona Brief
    ↓
Questions Asked (Step 2 — what information do they need?)
    ↓
Jobs to be Done (Step 3 — what are they trying to accomplish?)
    ↓
Features Required (Step 4 — what UI + agent capability delivers that job?)
    ↓
F21 Dashboard Specification (5-artifact build input)
```

---

### Step 1 — Persona (from F12)

Role, daily routine (hour-by-hour), authority level, success metrics. The persona brief is the input — F31 is the process that mines it for feature requirements.

---

### Step 2 — Questions Asked

Every persona has a daily information diet. Classify each question by type — the type determines the feature pattern:

| Question Type | When | Pattern it produces |
|---|---|---|
| **Standing** | Every day, first thing | KPI strip + sortable live table (always visible) |
| **Situational** | Triggered by an event | Drill-down panel + detail view (opened by row click or alert) |
| **Strategic** | Weekly or monthly | Trend chart + period summary (tab or collapsible section) |

**Standing questions** are the most important: "What's my queue? What's late? What needs my decision?" These define the primary view — the thing the user sees when they open the dashboard before clicking anything.

**Situational questions** drive the secondary view: "Why is this order delayed? What caused this NCR?" These define the detail panel — what opens when they click a row.

**Strategic questions** drive periodic reporting: "Are we on track? What's our OTD rate this month?" These define charts and export features.

---

### Step 3 — Jobs to be Done

For each question cluster, define the underlying job:

| Field | Definition |
|---|---|
| **Trigger** | What situation prompts this job? |
| **Current friction** | How do they do it today, and what's painful? |
| **Desired outcome** | What does "done" look like for this job? |
| **Success metric** | How would they measure whether the job was done well? |

**The job is not the feature.** "Know which quotes need follow-up before they go cold" is a job. The stale follow-up alert strip is the feature that delivers it. Keep them separate — the job stays stable even when the feature implementation changes.

---

### Step 4 — Features Required

For each job, specify four things:

| Decision | Question | Framework |
|---|---|---|
| **Agent opportunity** | Which F3 capability type applies? | Monitor (detect), Analyze (score/rank), Generate (draft), Execute (act), Evaluate (score), Coordinate (multi-agent) |
| **UI component** | Which COMPONENTS.md pattern delivers this job? | KPI card, sortable table, run theater, drill-down panel, decision card, alert strip, trend chart |
| **Authority level** | What's the right F4 level for the agent action in this job? | LOW (auto), MEDIUM (notify), HIGH (draft-for-review) |
| **Data dependency** | What data must be available, and what's its F11 score? | Score 1-5; if score < 3, this feature may need a fallback or mock mode |

---

### Kimre Example — Alex Torres (Sales / Applications Engineer)

**Persona:** 8 RFQs/day → select product → configure → price → draft scope → quote → follow up → convert.

| Question | Type | Job | Feature | Agent | Authority | F11 |
|---|---|---|---|---|---|---|
| "Which RFQs need a quote today?" | Standing | Prioritize backlog by urgency | Quote pipeline table, sorted by Days in Stage (oldest first) | Monitor | LOW | 3 |
| "Which quotes are going cold?" | Standing | Catch stale follow-ups before they close silently | Stale follow-up alert strip — amber banner, one-click log action | Monitor | LOW | 3 |
| "This RFQ mentions a fertilizer plant — what product do I recommend?" | Situational | Match application to product family quickly | RFQ-to-Quote Agent run theater → scope draft with product recommendation | Generate | MEDIUM | 4 |
| "What's my win rate this month?" | Strategic | Assess pipeline health and adjust effort | Win/Loss tracker section with outcome tags and trend | Analyze | LOW | 2 |
| "This quote is over £100K — does it need sign-off?" | Situational | Know when to escalate before the customer asks | High-value gate badge (🔒 Manager Review Required) on quotes > £100K | Evaluate | HIGH | 4 |

**What F31 produced for the Kimre Sales dashboard:**
- 2 standing-question features → KPI strip (open RFQs, pipeline value, win rate, avg quote age) + quote pipeline table
- 2 situational features → stale alert strip + RFQ-to-Quote run theater + high-value gate badge
- 1 strategic feature → win/loss tracker section
- Every feature has an agent opportunity, authority level, and data readiness score before a line of code is written

---

### F31 in Discovery Sprints

Run F31 for each persona *before* scoping the dashboard. The output becomes the F21 JTBD artifact — the second of five required inputs before a dashboard agent launches.

F31 also surfaces mismatches early:
- A situational feature with F11 score 1 → the data doesn't exist yet; build a mock mode or cut the feature from v1
- A standing question with HIGH authority → the daily dashboard will require human review on every load; reconsider the authority design
- A job with no agent opportunity → pure UI, no agent needed; simpler to build, lower maintenance

**Relationship to other frameworks:**
```
F12 (Stakeholder Personas) → Step 1 input — the persona brief
F21 (Dashboard Specification) → Step 4 output feeds F21 artifact #2 (JTBD spec)
F3 (Capability Types) → Step 4 agent opportunity maps to F3 types
F4 (Authority Levels) → Step 4 authority level is F4 applied per job, not per agent
F11 (Data Readiness) → Step 4 data dependency score gates which features ship in v1
F28 (WHY/WHAT/HOW) → F31 is the WHAT→HOW bridge for persona-facing work — jobs are WHAT, features are HOW
F19 (Persona Dashboard Quality) → F31 produces the spec that F19 evaluates
```
