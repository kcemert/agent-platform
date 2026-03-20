# American Airlines — Context
Last updated: 2026-03-19

**What:** Major US airline — Fort Worth, TX — ENT — LOGISTICS / Service
**Size:** ENT | **Industry:** LOGISTICS | **Regulatory:** 5/5 (FAA, DOT, TSA, OSHA) | **Integration:** T3
**Accent:** `#003087` (AA blue) | **Status:** Roadmap designed — not yet built (Epics 78–89)

## Profile
- Model: Service (ops-driven, 24/7)
- Pilot rec: IROPS Reaccommodation Agent — 6-week pilot
- 6 Agents planned (all slug prefix `aa-`):
  - aa-irops-reaccommodation-agent (PILOT)
  - aa-crew-irops-recovery-agent (next)
  - aa-aog-parts-agent (next)
  - aa-customer-sentiment-agent, aa-revenue-integrity-agent, aa-faa-compliance-monitor

## 7 Personas
Monica Chen (OCC Director) | David Park (MRO Manager) | Sarah Kim (Rev Mgmt) | James Torres (CX) | Carlos Mendez (Crew Scheduling) | Alex Rivera (Network Planning) | Sandra Martinez (VP Ops/Executive)

## Key Files
- Detailed roadmap: `memory/aa.md`
- Implementation plan: `Implementation_Plan.md` Phase 10

## Critical Design Note
Carlos Mendez (Crew Scheduling) dashboard = dispatch tool, NOT reporting. Open time board + FAR Part 117 legality check. Legal ≠ available — must check both. T3 integration makes this Phase 2.

## Next Priority
Begin Epic 78 — AA client profile JSON + index.html portal
