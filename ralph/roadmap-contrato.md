# Contrato — Project Roadmap

**Mission**: Scale AI-assisted discovery by training contractors to interview small business owners, produce structured transcripts, and return 1–2 days later with a working demo.

---

## Phase 0: Foundation
*Complete before any building. Three workstreams in parallel.*

| # | Task | Owner | Status |
|---|---|---|---|
| 0.1 | Collaboration setup — shared GitHub, ralph access, StrtrHalo pool | Keith + Christopher | 🔴 Open |
| 0.2 | Project architecture — data segmentation between clients, knowledge unification strategy | Christopher | 🔴 Needs input |
| 0.3 | Technical infrastructure — hosting, API keys, model access (Claude / self-hosted), folder structure for data | Christopher | 🔴 Needs input |
| 0.4 | Agent blueprint design — define each agent, skill structure, authority level (F3+F4) | Keith | 🔴 Open |

**Key decision (0.2)**: Per-client isolated DB vs. shared knowledge layer with access controls? This affects data segmentation, billing, and knowledge unification downstream.

---

## Milestone 1: Full Pipeline Built
*Definition of done: One real interview → one workable pilot output, end-to-end.*

| # | Deliverable | Notes |
|---|---|---|
| 1.1 | Interview → transcript pipeline | Manual interview OK for v1; structured by F28+F31 question sets |
| 1.2 | First data import | Synthetic + internet data; CLI tool: log into demo, generate API key, give model access to data folder |
| 1.3 | A3 Problem Extractor | Transcript → structured problem report (F28 WHY/WHAT/HOW + F31 JTBD + M2 5 Whys) |
| 1.4 | A4 App Spec Generator | Problem report → myagents-compatible build spec JSON |
| 1.5 | A5 myagents Submission Agent | Submit spec via WebSocket, receive build confirmation + job ID |
| 1.6 | One solved problem demoed | End-to-end: raw interview → working pilot shown back |

**Data import spec (1.2):**
- CLI: `python3 contrato/import.py --source internet|synthetic --client <slug>`
- Generates API key per client
- Gives Claude / self-hosted model read access to `data/<client>/` folder
- Logs import run to session log

---

## Milestone 2: Pipeline Produces Great Outputs
*Definition of done: Output quality is good enough to show a real SBO without embarrassment.*

| # | Deliverable | Notes |
|---|---|---|
| 2.1 | Structured reasoning integrated | F28 WHY/WHAT/HOW tagging reliable across diverse interview styles |
| 2.2 | 🔴 Agent setup complete | Blueprint + skill structure defined per agent — **current design blocker** |
| 2.3 | Control plane active | A1 Interview Conductor + A2 Live Transcript Analyzer running for sales people |
| 2.4 | Agent-to-agent communication | Strategic agent + technical agent coordinate; iterate through all questions |
| 2.5 | Self-healing loop | Feedback mechanism captures what was wrong → improves app on second pass |
| 2.6 | Full data import (2nd iteration) | Replace synthetic data with real client data |

**Agent setup (2.2) — to be designed:**
See `ralph/business-model-contractor.md` for 6-agent architecture (A1–A6).
For each agent, need to define:
- Tools it calls
- Framework it encodes (F3 capability type, F4 authority level)
- Input/output schema
- Skill structure (what it knows how to do step-by-step)

---

## Phase 1: Internal Validation
*Run the model a few times — Keith + Christopher only, no contractors yet.*

Gates:
- [ ] Transcript quality: F28 coverage complete (WHY + WHAT + HOW all populated)
- [ ] Spec accuracy: myagents builds something recognizable from the problem described
- [ ] Demo relevance: SBO would say "yes, that's my problem"
- [ ] Cycle time: interview → demo in < 48h

---

## Phase 2: Contractor Rollout
*Bring contractors in once Phase 1 gates pass.*

- Train contractors on interview protocol (F28+F31 standing/situational/strategic questions)
- Each contractor uses A1 (Interview Conductor) as real-time guide
- A2 (Live Transcript Analyzer) tags responses as interview happens
- Feedback loop active from day 1 → every contractor run improves the model
- Revenue model: contractor earns per converted demo; platform takes % of engagement fee

---

## Open Items (resolve in next working session)

| Item | Question | Blocking |
|---|---|---|
| 0.2 Christopher infra | Per-client isolated DB or shared layer? | Milestone 1 data import |
| 0.4 Agent blueprints | Skill structure + tool list per agent | Milestone 2 control plane |
| StrtrHalo | How does resource pooling work? What's the integration point? | Phase 0 collab setup |
| ralph loops | How does Keith's ralph loop feed into Contrato? | Phase 0 collab setup |
| Model access | Claude API or self-hosted? Cost model per interview run? | 1.2 data import CLI |

---

## Cross-References

- 6-agent architecture + interview protocol: `ralph/business-model-contractor.md`
- F28 WHY/WHAT/HOW meta-framework: `ralph/frameworks.md`
- F31 Feature Identification Chain: `ralph/frameworks.md`
- M2 5 Whys (A3 root cause): `ralph/methodologies.md`
- System composition (how agents+frameworks+methodologies connect): `ralph/system-composition.md`
- myagents repo: https://github.com/christopher-kapic/myagents
