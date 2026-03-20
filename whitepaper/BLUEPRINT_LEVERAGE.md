# Agent System Blueprint — Leverage Analysis

Source: "Agent System Blueprint — Generic Reference" (extracted from PwC Slide Builder)
Question: Which concepts can we leverage, and for what?

---

## The Big Observation

The blueprint solves the **implementation problem** of the Agent Mind.
The paper solves the **philosophical problem** — why build it this way.

They are complementary. The paper gives us the WHY. The blueprint gives us the HOW for the specific technical problem of persistence, memory, and context loading. Put together:

- Paper: the Agent Mind should exist, here is what it is and why it compounds
- Blueprint: here is the folder structure, the file patterns, and the session logging protocol to build it

The blueprint's "Three Brains" is the implementation spec for what the paper calls the Agent Mind. The blueprint's "formalization cycle via transcript mining" is the implementation spec for what the paper calls the correction cycle. The blueprint's "maturity ladder" is the same Cook-to-Chef arc, operationalized at the file level.

---

## Related
- `whitepaper/ANALYSIS.md` — practical vs. theoretical breakdown
- `ralph/agentic_mind_blueprint.md` — the Agent Mind build spec
- `whitepaper/practical/formalization-cycle.md` — the cycle this implements
- `whitepaper/practical/caio-spec.md` — the CAiO who runs the cycle
- `patterns/` — the pattern registry being built (see Tier 2 items)
- `pilot-agents/orchestrator.py` — pipeline orchestration target

---

## Tier 1 — Directly Applicable Now (High Leverage, Low Cost)

These concepts map to something we already have and deepen it, or fill a gap we know exists.

---

### 1. Three Brains → Reorganize the Agent Mind's knowledge stores

**Blueprint concept:** Strategic Brain (what to solve), File Brain (where is everything), Session Brain (what happened recently). Peers, not nested.

**What we have:** `ralph/frameworks.md` (strategic), `registry.json` (file), `memory/MEMORY.md` (session). But they're not explicitly organized as three distinct brain types with clear routing rules.

**What to do:** Formalize the three-brain structure across the platform:
- Strategic Brain = `ralph/frameworks.md` + `ralph/agentic_mind_blueprint.md` + `ralph/prd.json`
- File Brain = `registry.json` + `docs/` + agent specs
- Session Brain = `memory/MEMORY.md` + `.apm/` logs

**Why it matters:** When an agent (or the CAiO) needs context, they should know which brain to consult first without searching. The routing rule is: question about *what to do* → Strategic Brain; question about *where something is* → File Brain; question about *current state* → Session Brain.

---

### 2. Progressive Disclosure (Pointer Chain) → Fix our context loading

**Blueprint concept:** Tier 1 (always loaded, ~3K tokens) → Tier 2 (on project mention) → Tier 3 (on task demand). Each tier is a pointer to the next, not a copy of it.

**What we have:** MEMORY.md is loaded every session (~200 lines). It points to some deeper files but not systematically. Large files like frameworks.md (77KB) are read in full when needed, which is expensive.

**What to do:**
- MEMORY.md stays as Tier 1 (routing table + key facts, keep under 200 lines — already enforced)
- Add explicit Tier 2 CONTEXT.md files per client (`clients/kimre/CONTEXT.md`, `clients/aa/CONTEXT.md`) — 10-15 lines: current status, key files, next priority
- Tier 3 = the deep files (frameworks.md, agent specs, persona briefs) — loaded only when the specific task requires them

**Why it matters:** Right now every session either over-loads (reading full frameworks.md) or under-loads (relying on MEMORY.md alone). The pointer chain fixes the signal-to-noise problem.

---

### 3. Session Logging (Breadcrumbs + Rich Summary) → Implement the formalization cycle capture

**Blueprint concept:** Breadcrumbs (one line after every file write, automatic) + Rich Summary (on checkpoint: all todos complete, topic switch, explicit save request). Next session reads: last rich summary + any breadcrumbs after it.

**What we have:** MEMORY.md is updated manually/on request. No automatic breadcrumbing. The `.apm/` directory exists but isn't consistently used.

**What to do:**
- Define the breadcrumb format: `YYYY-MM-DD HH:MM | ACTION | file | description`
- Define flush triggers: all todos complete, topic switch, session end
- Rich summary format: Built / Decisions / Opened / Next
- Store breadcrumbs in `memory/session_log.md`, rich summaries in MEMORY.md's relevant section

**Why it matters:** This IS the formalization cycle's capture phase made concrete. Every correction a human makes during a session that doesn't get breadcrumbed is a lost pattern candidate.

---

### 4. Transcript Mining → CAiO's primary tool

**Blueprint concept:** "Periodically review past session transcripts for: re-explanation patterns (agent forgot), lost decisions (not recorded), workflow friction (user had to compensate), missing cross-references."

**What we have:** Session transcripts exist in `.jsonl` files. We have never systematically mined them.

**What to do:**
- Define a monthly transcript mining protocol for the CAiO
- Four categories to tag: re-explanation (→ update MEMORY.md), lost decision (→ add to pattern registry), friction (→ process improvement), missing cross-reference (→ update cross-links)
- Each finding → a pattern candidate entered into the formalization cycle

**Why it matters:** This is the lowest-cost source of pattern candidates. The correction history is already in the transcripts. The CAiO needs a structured process to extract it.

---

### 5. Stale Detection → Knowledge hygiene

**Blueprint concept:** Files need `Last updated: YYYY-MM-DD` metadata. Files > 30 days old get flagged as potentially stale.

**What we have:** Most knowledge files have no timestamp. `ralph/frameworks.md` says "Updated: 2026-03-14" at the top — good. Most others don't.

**What to do:**
- Add `Last updated:` header to all knowledge files in `ralph/`, `docs/`, `clients/*/`
- When reading a file > 30 days old, flag it in the session note
- Monthly: run a stale scan and queue updates

**Why it matters:** The Agent Mind's patterns are only as current as the knowledge files that inform them. Stale files are a source of drift.

---

### 6. Cross-Linking Protocol → Connect the knowledge web

**Blueprint concept:** When creating/updating any knowledge file: add explicit links to related files, update the registry, note which dimensions it impacts.

**What we have:** Files are siloed. `frameworks.md` doesn't link to `agentic_mind_blueprint.md`. Client files don't link to relevant framework sections.

**What to do:**
- Every new file starts with a `## Related` section listing linked files
- When a framework is instantiated for a client (e.g., F7 blueprint → Glock agent blueprint), the client file links back to the framework
- Framework files link forward to client examples

**Why it matters:** Without cross-links, a new analyst (or a new session) reading one file has no path to related context. Cross-links turn a file collection into a knowledge web.

---

## Tier 2 — Design Into Platform Architecture

These concepts require more deliberate design work but should inform what we build next.

---

### 7. Quality Gate Safety Tiers → Authority level enforcement in agent code

**Blueprint concept:** Safe tier (font floors, boundary clamping) → Moderate tier (alignment, card fixes) → Aggressive tier (move shapes, change fonts). Each tier has a different review requirement.

**What we have:** F4 Authority Levels (LOW/MEDIUM/HIGH) defined in frameworks.md. But agent code doesn't enforce them at the code level — it's specified in the blueprint but not checked at runtime.

**What to build:** A quality gate function in the agent platform that checks the action tier before execution:
```python
def execute_action(action, authority_level, session):
    if authority_level == "HIGH" and not session.has_approval():
        return draft_for_review(action)  # never auto-execute
    elif authority_level == "MEDIUM":
        execute(action)
        notify(session.process_owner, action)  # auto-execute + notify
    else:
        execute(action)  # LOW: fully automated
```

**Why it matters:** Right now authority levels are documentation. Making them enforceable at the code level is what makes the system trustworthy, not just well-specified.

---

### 8. Configuration-as-Code with Override Layers → Pattern registry hierarchy

**Blueprint concept:** System defaults → Project overrides → Client overrides. One loader resolves final values.

**What we have:** Pattern registries don't exist as structured configs yet. Agent behavior is encoded in Python scripts and server.py.

**What to build:** A JSON-based pattern config hierarchy:
```
patterns/
  defaults.json           ← Platform-level patterns (apply everywhere)
  industries/
    mfg.json              ← Manufacturing-specific patterns
    fs.json               ← Financial services patterns
  clients/
    kimre.json            ← Kimre-specific overrides
    glock.json            ← Glock-specific overrides
```

A loader function merges: `defaults → industry → client → final_config`.

**Why it matters:** This is the implementation of the pattern registry that the Agent Mind requires. Currently we have frameworks described in markdown; this makes them machine-executable.

---

### 9. Maturity Ladder → Pattern promotion schema

**Blueprint concept:** L0 (defined) → L1 (questions listed) → L2 (frameworks built) → L3 (evidence gathered) → L4 (validated) → L5 (complete and defensible). Forces honesty about what's proven vs. assumed.

**What we have:** Agent maturity model (F10) at the agent level. But individual *patterns* within the Agent Mind don't have maturity tracking.

**What to build:** Add a `maturity` field to the pattern registry schema:
```json
{
  "pattern_id": "authority-escalation-high-value",
  "trigger": "action_value > 50000",
  "maturity": 2,
  "promotion_criteria": "30 successful applications, correction_rate < 0.3",
  "correction_history": [...],
  "source_session": "2026-03-15"
}
```

**Why it matters:** Without maturity tracking, all patterns are treated equally. A pattern that's been validated 50 times should be trusted more than one that was just formalized last week.

---

### 10. Pipeline Orchestration → Enhance orchestrator.py

**Blueprint concept:** Ordered multi-step workflows. Skip-to logic for common cases. Default path + routing table for exceptions.

**What we have:** `orchestrator.py` runs agents sequentially. No skip-to logic. No pipeline stages.

**What to build:** Define named pipeline stages in orchestrator.py:
```python
PIPELINES = {
    "full_discovery": ["data_readiness", "opportunity_scan", "blueprint_gen", "value_case"],
    "quick_scan": ["opportunity_scan"],  # skip-to
    "pilot_run": ["agent_run", "hitl_review", "pattern_capture"]
}
```

**Why it matters:** The current orchestrator is a loop. A pipeline is a workflow with routing intelligence. This is the operational implementation of F26 (Multi-Agent Coordination).

---

### 11. Input Routing → orchestrator.py intelligence

**Blueprint concept:** Text prompt → Strategy → Build → Review. Existing file → Read → Edit Plan → Build. Different input types trigger different chains.

**What we have:** All orchestrator runs are the same — run agents, collect output.

**What to build:** Input classifier at the orchestrator entry point:
```python
def route(input_type, input_data):
    if input_type == "new_client":
        return run_pipeline("full_discovery", input_data)
    elif input_type == "correction":
        return run_pipeline("pattern_capture", input_data)
    elif input_type == "pilot_run":
        return run_pipeline("pilot_run", input_data)
```

---

## Tier 3 — Informs Product Roadmap

These are structural patterns that should shape the platform's long-term architecture.

---

### 12. Standardized Folder Structure → Client portal standard

**Blueprint concept:**
```
clients/{project}/
  CONTEXT.md            ← Tier 2: lightweight summary
  memory/session_log.md ← Tier 2: breadcrumbs + rich summaries
  References/
    framework_registry.md
    meta_framework.md
  outputs/
  archive/
```

**What we have:** `clients/kimre/` has a good structure (9 pages, persona briefs, etc.) but no CONTEXT.md, no session log, no explicit archive. PrecisionParts and MeridianBank are shell stubs.

**What to build:** Standardize the client folder structure using the blueprint pattern. The `portal/generate.py` script should create all required files on initialization.

---

### 13. Framework-First Storytelling → Discovery sprint deliverable format

**Blueprint concept:** Framework → Methods → Convergence → Numbers → So What. Five-step presentation order. Trust comes from seeing where the number came from.

**What we have:** The Glock analysis used this structure implicitly (framework → regulatory map → agent map → value case). Not formalized as a template.

**What to build:** A discovery sprint deliverable template that enforces this order. Every client-facing analysis output follows: framework → method → convergence → number → so what.

---

### 14. Dual-Methodology Validation → Value case standard

**Blueprint concept:** Two independent methods that should converge. If top-down and bottom-up differ >30%, something is wrong. The convergence is the evidence.

**What we have:** Value cases use one method (usually top-down: hours × rate). No bottom-up validation.

**What to build:** Require dual-methodology in all value cases:
- Top-down: process frequency × time per occurrence × fully-loaded rate
- Bottom-up: interview-based time logs from actual users
- Convergence: report both, explain delta if >20%

**Why it matters:** Single-methodology value cases are easy to challenge. Convergence is evidence that the number is real.

---

### 15. Constraint Floor Analysis → ROI case discipline

**Blueprint concept:** Before estimating savings from any cost pool, identify what % is non-addressable. Triangulate from multiple sources. The floor protects against overstating opportunity.

**What we have:** The opportunity scoring tool (F16) captures impact and feasibility but not addressability floor.

**What to build:** Add "addressable fraction" as a required field in opportunity scoring. Every agent opportunity has: total pool size × addressable fraction = addressable pool × efficiency gain = year-1 value. Never skip the floor analysis.

---

## What the Blueprint Has That We Don't Yet

| Blueprint concept | Current gap | Priority |
|---|---|---|
| Breadcrumb logging (automatic) | Manual MEMORY.md updates only | HIGH |
| Pattern registry as structured config (JSON) | Patterns in markdown only | HIGH |
| Maturity field per pattern | No pattern-level maturity tracking | HIGH |
| Three-brain routing rule | Implicit only | MEDIUM |
| Cross-linking protocol | Files are siloed | MEDIUM |
| Stale detection | No timestamps on most files | MEDIUM |
| Quality gate enforcement at code level | Authority levels are documentation only | HIGH |
| Client CONTEXT.md (Tier 2 lightweight) | No Tier 2 pointer files | MEDIUM |
| Transcript mining protocol | Never done | MEDIUM |
| Constraint floor in value cases | Missing from standard | MEDIUM |

---

## What We Have That the Blueprint Doesn't

| Our concept | Why it's a gap in the blueprint |
|---|---|
| F1-F27 reasoning scaffold | Blueprint has no analytical framework for *what to reason about* — only *how to persist reasoning* |
| The formalization cycle (philosophical grounding) | Blueprint captures corrections but doesn't explain why the cycle grows wisdom |
| Authority levels (F4) | Blueprint has safety tiers but no governance model for who can authorize what |
| Client profile schema (F20) | Blueprint has project routing but no client intelligence model |
| The CAiO role | Blueprint has no steward for the accumulated knowledge |
| 12 Logos health metrics | Blueprint has retention rules but no health measurement for the Mind itself |

---

## Summary

The blueprint is the **implementation layer** the paper needs.
The paper is the **philosophical grounding** the blueprint lacks.

The synthesis: take the blueprint's persistence patterns (three brains, breadcrumbs, pointer chain, transcript mining, stale detection, cross-linking) and implement them against the architecture the paper defines (seven-layer stack, formalization cycle, pattern registry with maturity, CAiO, 12 Logos health metrics).

The result is a system that:
1. Knows where its wisdom came from (source field per pattern)
2. Knows how mature each piece of wisdom is (maturity level per pattern)
3. Grows through every correction (breadcrumb → pattern candidate → formalization cycle)
4. Never claims more confidence than the maturity level warrants
5. Has a CAiO who monitors the false-done rate and runs the transcript mining monthly
6. Has a human unconditionally above it at every high-stakes decision point

That is the Agent Mind — not a philosophical concept but a buildable system.
