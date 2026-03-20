# System Composition — Agents, Frameworks, Methodologies

**Three layers. One system.**

---

## Agents — the executors

Agents are mortal, task-specific, stateless loops. They do one thing: receive input, run logic, produce output, await approval. They don't remember yesterday. They don't know why they exist. They just execute.

What they can do is defined by **F3** (capability type: monitor / analyze / generate / execute / coordinate). What they're *allowed* to do is defined by **F4** (authority level: LOW auto-execute → HIGH human-required). How mature they are is tracked by **F10**.

The problem: agents lie. Not intentionally — they declare success even when failing. That's the false-done problem (F9), and it's why Detection is the hardest dimension in FMEA (M4). Agents need a scaffold above them.

---

## Frameworks — the reasoning scaffold

Frameworks (F1–F31) are structures for *thinking* that exist independent of any agent or client. They answer:

| Question | Framework |
|---|---|
| What to analyze | F28 WHY/WHAT/HOW |
| Who to build for | F12 Personas → F31 Feature Chain |
| What agent can do autonomously | F4 Authority Levels |
| Whether the value case is real | F30 Incrementality & Overlap |
| Whether the output is trustworthy | F27 Michael Principle |

Frameworks run **before** agents are built. They're the design layer. F21 (Dashboard Specification Framework) defines the 5 artifacts a subagent needs before any dashboard is commissioned. Without frameworks, you build agents for the wrong persona, with the wrong authority boundary, measuring the wrong metric.

---

## Methodologies — the correction process

Methodologies (M1–M6) are *processes for doing* that activate when agents underperform:

| Trigger | Methodology |
|---|---|
| Agent produces wrong output | M2 5 Whys → M1 RCCA |
| Pre-launch risk scoring | M4 FMEA (catches false-done before it ships) |
| Ongoing improvement cycle | M5 PDCA (formalization loop) |
| Complex pilot failures | M6 DMAIC |

Methodologies run **after** agents execute. They're the repair layer.

---

## Why They Work Together

The three layers form a closed loop:

```
FRAMEWORKS   → design the agent correctly before build
     ↓
AGENTS       → execute what frameworks specified
     ↓
METHODOLOGIES → fix agents when outputs diverge from ground truth
     ↓
Corrections become new patterns (pattern registry)
     ↓
Patterns improve the next agent generation
     ↑_____________________________________________|
```

This is PDCA (M5) at the system level. The formalization cycle never closes (F27) — there's always a correction to process, a pattern to capture, an agent to improve. That's not a bug; it's the design. The system gets smarter with every correction.

---

## One-Line Summary

**Frameworks tell you what to build and why. Agents build it. Methodologies fix it when it breaks. The loop makes the whole thing cumulative.**

---

## Cross-References

- Frameworks reference: `ralph/frameworks.md` (F1–F31)
- Methodologies reference: `ralph/methodologies.md` (M1–M6)
- Philosophical architecture: `ralph/agentic_mind_blueprint.md`
- Pattern registry: `patterns/` (formalized corrections from M1 RCCA)
- Quality gate (F4 at code level): `pilot-agents/quality_gate.py`
- Orchestrator (pipeline runner): `pilot-agents/orchestrator.py`
