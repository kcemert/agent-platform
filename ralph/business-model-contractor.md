# Business Model: Contractor-SBO Interview Pipeline

**The idea**: Scale discovery by training contractors to interview small business owners using agent-assisted protocols. The output is a structured transcript that feeds an automated app-building platform, delivering a working demo 1–2 days after the interview.

---

## The Flow

```
Contractor (trained on F28+F31 question sets)
    ↓
Interview small business owner (agent-assisted or manual)
    ↓
Structured transcript (problems tagged to F28 dimensions)
    ↓
Submit to myagents (Christopher Kapic's platform)
    ↓
Return 1–2 days later with a working demo
    ↓
SBO sees their problem solved → conversion
```

---

## Why This Works

- **Low barrier to entry**: Contractor doesn't need to be a developer — just trained on the interview protocol
- **High perceived value**: SBO gets a working demo of their specific problem, not a generic pitch
- **Franchise pattern**: Each contractor runs the same repeatable process; quality is encoded in the agents, not the contractor's skill
- **Speed**: 1–2 day turnaround from interview to demo is a competitive moat

---

## The 6-Agent Architecture

| Agent | Role | Input | Output |
|---|---|---|---|
| **A1** Interview Conductor | Guides contractor through F28+F31 question sets in real-time | Conversation context | Next question to ask |
| **A2** Live Transcript Analyzer | Tags responses to F28 dimensions as the interview happens | Raw transcript chunks | Structured tags (WHY/WHAT/HOW, confidence level) |
| **A3** Problem Extractor | Converts full transcript → structured problem report | Tagged transcript | Problem report JSON (F28+F31+M2 formatted) |
| **A4** App Spec Generator | Translates problem report → myagents-compatible build spec | Problem report JSON | App spec JSON |
| **A5** myagents Submission Agent | Submits spec to Christopher's platform via WebSocket | App spec JSON | Build confirmation + job ID |
| **A6** Demo Prep Agent | Prepares contractor for return visit (what to expect, talking points) | Build spec + job ID | Demo briefing doc |

**MVP = A3 + A4 + A5** (contractor does the interview manually; automate the back-end first)

---

## myagents Integration (Christopher Kapic)

**Repo**: https://github.com/christopher-kapic/myagents
**Stack**: TypeScript · React 19 · TanStack Router · Hono · oRPC · Prisma · PostgreSQL
**Protocol**: WebSocket-based multi-agent communication bus

```
# Agent registers:
{ type: "agent.register", agentId: "app-spec-submitter", capabilities: [...] }

# Submit job (A5 sends this):
{ type: "message.send", to: "myagents-builder", content: { spec: {...} } }

# Receive streaming response:
{ type: "message.chunk", content: "Building component..." }
{ type: "message.done", content: { buildId: "...", previewUrl: "..." } }
```

Agent-to-agent messaging requires permission model (myagents enforces this).

---

## Problem Extractor Output Schema (A3)

```json
{
  "sbo_name": "...",
  "business_type": "...",
  "interview_date": "...",
  "why_dimension": {
    "core_problem": "...",
    "root_cause_whys": ["...", "...", "..."],
    "confidence": 0.85
  },
  "what_dimension": {
    "current_process": "...",
    "pain_points": ["..."],
    "desired_outcome": "...",
    "jobs_to_be_done": [
      { "job": "...", "trigger": "...", "friction": "...", "desired_outcome": "..." }
    ]
  },
  "how_dimension": {
    "existing_tools": ["..."],
    "data_available": ["..."],
    "integration_complexity": 2,
    "regulatory_score": 1
  },
  "recommended_agent_type": "monitor|analyze|generate|execute",
  "authority_level": "LOW|MEDIUM|HIGH",
  "estimated_value_usd": 24000
}
```

---

## Interview Protocol (F28 + F31)

**Standing questions** (every SBO interview):
1. What does a bad day look like for you? (WHY)
2. Walk me through what you do from 8am to 10am on a typical day. (WHAT)
3. Where does work pile up / where do you feel behind? (WHY)
4. What tool do you use most? What's missing from it? (HOW)
5. If you could wave a wand and fix one thing, what would it be? (WHY)

**Situational questions** (based on responses):
- If they mention email overwhelm → drill into volume, response time, categorization
- If they mention tracking → drill into what gets lost, how they currently find it
- If they mention approvals → drill into who approves, how long it takes, what blocks it

**Strategic questions** (closing):
1. What would change in your business if this problem was solved?
2. How many hours per week does this cost you or your team?
3. Who else in your business feels this pain?

---

## Cross-References

- F28 WHY/WHAT/HOW Meta-Framework: `ralph/frameworks.md`
- F31 Feature Identification Chain (Persona→Questions→JTBDs→Features): `ralph/frameworks.md`
- M2 5 Whys (root cause in A3): `ralph/methodologies.md`
- F3 Capability Types (agent classification in A3 output): `ralph/frameworks.md`
- F4 Authority Levels (auto-execute vs. review): `ralph/frameworks.md`
- System composition (how agents+frameworks+methodologies connect): `ralph/system-composition.md`
