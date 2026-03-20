# Microsoft (Azure Cloud Operations) — Client Spec

**Status:** Designed — not yet built
**Pointer file:** `clients/microsoft/CONTEXT.md`
**Accent:** `#0078d4` (Azure blue)

---

## Profile (F20)

| Field | Value |
|---|---|
| Client | Microsoft Corporation — Azure Cloud Operations |
| HQ | Redmond, WA |
| Size | ENT (100K+ employees, $200B+ revenue) |
| Industry | TECH |
| Model | SaaS / Platform (internal ops + external customer delivery) |
| Regulatory | 4/5 (SOC 2 Type II, ISO 27001, FedRAMP High, GDPR) |
| Integration | T3 (Azure Monitor, Azure DevOps, Sentinel, Cost Management, ServiceNow) |
| Pilot rec | Azure Incident Triage Agent — 6-week pilot |
| Engagement tier | ENT Discovery → ENT Pilot |
| Accent | `#0078d4` |

**Why Azure Cloud Ops:**
Microsoft runs one of the world's largest cloud platforms. The operations center manages thousands of alerts per day, FinOps teams track billions in cloud spend, and compliance teams monitor policy drift across millions of resources. Every one of these is an agent opportunity with clear ROI and measurable output.

---

## 6 Personas

### P1: Elena Vasquez — SRE Lead / Incident Commander
**Focus:** Availability, reliability, incident response, SLO enforcement

**Daily routine:**
- 7am: Review overnight alert queue (PagerDuty / Azure Monitor)
- 8am: Triage P1/P2 incidents — assign runbook, notify stakeholders
- 10am: Post-incident review for any SEV1 from prior 24h
- 12pm: SLO burn rate review — which services are at risk?
- 2pm: Runbook authoring / improvement from recent incidents
- 4pm: Capacity headroom check for weekend traffic
- 5pm: On-call handoff brief

**Top 5 JTBDs:**
1. Triage incoming alerts in < 5 min — classify severity, assign owner, draft stakeholder update
2. Know which services are at SLO risk before customers notice
3. Generate post-incident report from incident timeline in < 30 min
4. Surface relevant runbook for active incident without searching Confluence
5. Track mean time to resolution (MTTR) trend across teams

**Pain points:**
- Alert fatigue: 300+ alerts/day, 80% are noise
- Post-mortems take 2–3h of manual timeline reconstruction
- Runbook discovery is search + tribal knowledge
- SLO burn rate visibility is manual (spreadsheet + Azure Monitor query)

**Success metrics:** P1 MTTR < 30 min | SLO breach rate < 0.1% | Alert noise ratio < 20% | Post-mortem published < 4h after resolution

**Pilot agent:** Azure Incident Triage Agent

---

### P2: Marcus Webb — Cloud FinOps Manager
**Focus:** Cloud cost governance, budget tracking, anomaly detection, showback/chargeback

**Daily routine:**
- 8am: Review overnight spend vs. budget across 200+ subscriptions
- 9am: Investigate any anomaly flags (spend spike > 15% vs. 7-day avg)
- 11am: Review committed spend utilization (Reserved Instances, Savings Plans)
- 1pm: Prepare weekly FinOps report for VP Engineering
- 3pm: Work with engineering teams on rightsizing recommendations
- 4pm: Update cost allocation tags — fix untagged resources

**Top 5 JTBDs:**
1. Know which subscription/service is over budget before end of month
2. Detect and investigate spend anomalies the same day they occur
3. Identify rightsizing opportunities (over-provisioned VMs, idle resources)
4. Generate weekly FinOps report for leadership without manual Excel work
5. Enforce tagging policy — flag and remediate untagged resources automatically

**Pain points:**
- Cost anomalies often discovered at month-end, too late to act
- Rightsizing analysis is manual — takes a full day per workload
- Tagging compliance is 60% — untagged spend is unallocatable
- RI/Savings Plan utilization not visible in one view

**Success metrics:** Anomaly detected < 24h of occurrence | Tagging compliance > 95% | RI utilization > 85% | Monthly report in < 30 min

**Pilot agent:** Azure Cost Anomaly Agent

---

### P3: Priya Nair — Cloud Security & Compliance Manager
**Focus:** Azure Policy compliance, security posture, audit response, FedRAMP/SOC 2 evidence

**Daily routine:**
- 8am: Review Defender for Cloud secure score delta
- 9am: Check new policy drift alerts (non-compliant resources created overnight)
- 11am: Respond to security questionnaire from enterprise customer
- 1pm: Evidence collection for SOC 2 / FedRAMP audit cycle
- 3pm: Review Sentinel alerts — SIEM triage
- 4pm: Certificate expiry check — anything expiring in < 30 days?

**Top 5 JTBDs:**
1. Know current policy compliance % and what's newly non-compliant
2. Auto-remediate or route non-compliant resources to owning team
3. Generate audit evidence package (SOC 2 / FedRAMP) without manual collection
4. Triage Sentinel alerts — separate real threats from noise
5. Track certificate expiry across all Azure services — no surprises

**Pain points:**
- Policy drift discovered during audits, not in real-time
- Evidence collection for SOC 2 takes 3 weeks of manual work
- Sentinel produces thousands of alerts; triage is manual
- Cert expiry surprises cause P1 incidents

**Success metrics:** Policy compliance > 98% | Audit evidence package in < 2h | Sentinel triage time < 15 min/alert | Zero cert expiry incidents

**Pilot agent:** Azure Policy Drift Agent

---

### P4: James Okafor — Enterprise Sales Engineer
**Focus:** Customer architecture reviews, POC delivery, technical objection handling, RFP responses

**Daily routine:**
- 8am: Review active POC status — any blockers?
- 9am: Customer architecture review call — assess workload fit for Azure
- 11am: Draft technical proposal / architecture diagram
- 1pm: RFP response — answer technical requirements section
- 3pm: Competitive objection brief — AWS vs. Azure for specific workload
- 4pm: POC handoff to CSA team — document what was built

**Top 5 JTBDs:**
1. Prepare customer architecture review in < 2h from workload description
2. Generate RFP technical response section from requirements doc
3. Surface relevant Azure reference architecture for customer's workload
4. Draft competitive positioning brief (AWS/GCP vs. Azure) for specific scenario
5. Document POC outcomes + next steps for handoff to CSA

**Pain points:**
- Architecture reviews require deep tribal knowledge — hard to delegate
- RFP responses are repetitive — similar questions answered from scratch each time
- Competitive intel is scattered across internal wikis
- POC documentation is incomplete — CSA team lacks context

**Success metrics:** Architecture review prep < 2h | RFP technical section draft in < 4h | POC handoff doc quality score > 4/5

**Agent:** Azure Sales Engineer Assistant (planned)

---

### P5: Sofia Chen — Partner Success Manager
**Focus:** ISV partner health, co-sell pipeline, certification status, partner onboarding

**Daily routine:**
- 8am: Review partner health dashboard — any at-risk partners?
- 9am: Co-sell pipeline review — which opportunities need Microsoft support?
- 11am: Partner QBR prep — pull partner KPIs, co-sell wins, cert status
- 1pm: Onboard new ISV partner — technical integration review
- 3pm: Certification expiry alerts — which partners need to re-certify?
- 4pm: Escalation: partner with blocked co-sell deal — coordinate with sales

**Top 5 JTBDs:**
1. Know which partners are at risk (low engagement, expiring certs, stalled pipeline)
2. Identify co-sell opportunities where Microsoft field engagement would unlock the deal
3. Prepare partner QBR report without manual data pulling
4. Track certification status across 50+ partners — never miss an expiry
5. Route partner escalations to the right internal team fast

**Pain points:**
- Partner health is scattered across Partner Center, CRM, email
- Co-sell pipeline visibility requires manual reporting
- QBR prep takes 1.5 days of data pulling
- Certification expiries caught reactively

**Success metrics:** At-risk partners identified 30 days in advance | QBR prep < 2h | Co-sell attach rate > 40% | Zero cert expiry surprises

**Agent:** Partner Health Agent (planned)

---

### P6: Daniel Park — VP Engineering / CTO (Executive)
**Focus:** Platform health, engineering org productivity, cost vs. growth, agent program ROI

**Daily routine:**
- 9am: Review platform health summary — any SEV1/SEV2 active?
- 10am: FinOps weekly — cost vs. budget vs. forecast
- 11am: Engineering velocity review — deployment frequency, incident rate, DORA metrics
- 2pm: Agent program review — what's the ROI on the AI ops investments?
- 4pm: Board/exec prep — platform reliability narrative

**Top 5 JTBDs:**
1. Know platform health at a glance — reliability, cost, velocity in one view
2. Understand agent program ROI vs. investment (hours saved, incidents avoided)
3. Approve high-value decisions escalated from SRE / FinOps / Security teams
4. Track DORA metrics (deployment frequency, change failure rate, MTTR) trend
5. Generate exec summary for board on platform reliability + AI ops progress

**Success metrics:** Full platform picture in < 5 min | Agent ROI positive by month 3 | DORA metrics improving QoQ

---

## 6 Agents

| Rank | Agent | Persona Served | Status | Slug |
|---|---|---|---|---|
| 1 | Azure Incident Triage Agent | Elena (SRE) | PILOT | `msft-incident-triage-agent` |
| 2 | Azure Cost Anomaly Agent | Marcus (FinOps) | Next | `msft-cost-anomaly-agent` |
| 3 | Azure Policy Drift Agent | Priya (Security) | Next | `msft-policy-drift-agent` |
| 4 | Azure Capacity Planner | Elena + Daniel | Planned | `msft-capacity-planner-agent` |
| 5 | Partner Health Agent | Sofia (Partner) | Planned | `msft-partner-health-agent` |
| 6 | Azure Postmortem Agent | Elena + Daniel | Planned | `msft-postmortem-agent` |

### Pilot Agent: Azure Incident Triage Agent (`msft-incident-triage-agent`)
- **Input:** Azure Monitor alerts feed (or dry-run: 12 hardcoded alerts)
- **Logic:** Classify severity (P1/P2/P3) → match runbook → draft stakeholder update → flag for Elena if P1
- **Output:** `{alerts_processed: 12, p1_count: 1, p2_count: 3, auto_resolved: 5, escalated: 4, items: [{alert_id, service, severity, runbook_matched, stakeholder_draft, action}]}`
- **Authority:** LOW → auto-triage and draft; HIGH → P1 escalation requires Elena approval
- **Year-1 value:** £180K (2.5h/day triage time recovered × 250 days × blended rate)

---

## Engagement Model (F8)

| Phase | Scope | Fee |
|---|---|---|
| Discovery | Azure ops assessment, 6-persona interview, agent opportunity map | £15K |
| Pilot | Incident Triage Agent — 6-week live pilot on Azure Monitor feed | £35K |
| Platform | All 6 agents, dashboards per persona, orchestrator | £120K+ |

**Break-even:** Week 6 (pilot phase ROI positive)
**18-month value:** £820K (across all 6 agents at full deployment)

---

## Implementation Epics (Planned)

| Epic | Deliverable | Files |
|---|---|---|
| E1 | Client profile + portal | `clients/microsoft/profile.json`, `clients/microsoft/index.html` |
| E2 | Persona briefs + JTBD specs | `clients/microsoft/personas.md` |
| E3 | SRE Dashboard | `clients/microsoft/sre.html` |
| E4 | FinOps Dashboard | `clients/microsoft/finops.html` |
| E5 | Security & Compliance Dashboard | `clients/microsoft/security.html` |
| E6 | Sales Engineer Dashboard | `clients/microsoft/sales-eng.html` |
| E7 | Partner Success Dashboard | `clients/microsoft/partner.html` |
| E8 | Executive Dashboard | `clients/microsoft/executive.html` |
| E9 | Azure Incident Triage Agent | `pilot-agents/microsoft/incident_triage_agent.py` |
| E10 | Azure Cost Anomaly Agent | `pilot-agents/microsoft/cost_anomaly_agent.py` |
| E11 | Azure Policy Drift Agent | `pilot-agents/microsoft/policy_drift_agent.py` |
| E12 | Server + registry wiring | `dashboards/server.py` (msft-* slugs) |

---

## Cross-References

- AA client spec (same pattern): `memory/aa.md` (if built) / `clients/aa/CONTEXT.md`
- Kimre (gold standard portal): `clients/kimre/`
- F20 Client Profile Schema: `ralph/frameworks.md`
- F12 Stakeholder Personas: `ralph/frameworks.md`
- F31 Feature Identification Chain: `ralph/frameworks.md`
- F8 Engagement Model: `ralph/frameworks.md`
