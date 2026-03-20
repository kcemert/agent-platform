
# Methodologies Registry
*Companion to `ralph/frameworks.md` — M-series entries*

Last updated: 2026-03-19

## Related
- `ralph/frameworks.md` — F1-F31 reasoning frameworks
- `whitepaper/practical/formalization-cycle.md` — the cycle these methodologies operate within
- `whitepaper/practical/caio-spec.md` — the CAiO who applies these methodologies

## Frameworks vs. Methodologies

**Framework** — a *structure for thinking*. Organizes a domain into dimensions, categories, or decision rules. Tells you *what* to consider and *how to classify* it.

**Methodology** — a *process for doing*. A repeatable sequence of steps with specific techniques. Tells you *how* to execute within a framework.

F1-F31 are frameworks. M1-M6 are methodologies. They work together: the frameworks provide the analytical structure; the methodologies provide the operational discipline.

---

## M1 — Root Cause Corrective Action (RCCA)

**What it is:** A structured process for moving from symptom (a problem is observed) to verified fix (the problem is eliminated and won't recur). RCCA is the difference between treating symptoms and solving problems.

**The six steps:**

| Step | Action | Output |
|---|---|---|
| 1. Define the problem | State the problem precisely: what happened, when, where, how often, impact | Problem statement |
| 2. Contain the damage | Immediate action to prevent further harm while investigation runs | Containment action log |
| 3. Find the root cause | Use M2 (5 Whys) or M3 (Fishbone) to identify the cause beneath the cause | Root cause statement |
| 4. Develop corrective action | Design the fix that eliminates the root cause, not just the symptom | Corrective action plan |
| 5. Implement and verify | Execute the fix; verify the problem is actually gone (not just quieter) | Verification evidence |
| 6. Prevent recurrence | Update the system, process, or pattern to prevent the same class of problem | Pattern update or process change |

**Platform application — when the CAiO runs RCCA:**
- A pattern's false-done rate climbs above threshold (F9 Sacrificial metric)
- An agent produces a HIGH authority action that was later overridden by the human
- The same correction appears in session transcripts 3+ times without being formalized
- A pilot agent enters production and user complaints increase rather than decrease

**RCCA in the formalization cycle:** Step 3 produces the root cause. Step 4 produces the corrective pattern. Step 6 formalizes it into the pattern registry (F7). RCCA is the formalization cycle's quality arm.

**Example (agent false-done):**
```
Problem: cg-replenishment-pr-agent is generating PRs that the Purchasing Manager overrides 40% of the time.

Step 1 — Problem: Agent creates PRs at standard lead-time reorder point, but PM overrides to account for seasonal demand spikes not in the ERP data.

Step 2 — Contain: Flag all agent PRs as "pending PM review" until root cause resolved. Stop auto-approve.

Step 3 — Root cause (5 Whys):
  Why is the PM overriding? → PR quantity doesn't account for seasonal demand
  Why doesn't it account for seasonal demand? → Agent reads ERP forecast, which doesn't include seasonal adjustments
  Why doesn't ERP have seasonal adjustments? → PM does seasonal planning in a separate spreadsheet
  Why is it separate? → ERP doesn't have a seasonal adjustment field
  Root cause: The agent's data source (ERP forecast) is structurally missing the PM's tacit seasonal knowledge

Step 4 — Corrective action: Add seasonal multiplier field to agent config, populated by PM before each quarter. Agent reads config before calculating PR quantity.

Step 5 — Verify: Override rate drops to <10% in subsequent 30 runs.

Step 6 — Prevent recurrence: Add "seasonal demand adjustment required" as a standard field in F7 Agent Blueprint for all inventory agents. Add pattern to patterns/industries/mfg.json: "inventory-seasonal-adjustment-gate".
```

**Relationship to frameworks:**
```
F9 (Value Measurement) → Sacrificial metric (false-done rate) triggers RCCA
F7 (Agent Blueprint) → Step 6 output updates the blueprint
F10 (Agent Maturity) → RCCA is required before any pattern promotion above maturity 3
F27 (Michael Principle) → High override rate is a F27 violation signal — correction cycle failing
patterns/ → Step 6 output enters the pattern registry
```

---

## M2 — 5 Whys

**What it is:** An iterative root cause interrogation technique. For any problem, ask "why?" and then ask "why?" again for each answer — repeat until you reach a cause that is actionable and structural (not symptomatic).

**The rule:** Stop at 5 only if you've reached a root cause. Some problems resolve at Why 3; some require Why 7. The number is a heuristic, not a law.

**The failure mode:** Stopping too early (at a symptom) or drifting (each "why" goes in a different direction). The discipline is to follow one causal chain to its structural end, not explore all possible causes simultaneously (use M3 for that).

**Platform application:**
- M1 Step 3 — finding root cause in an RCCA
- CAiO investigating a pattern that keeps getting triggered incorrectly
- Discovery sprint when client describes a problem ("we have too many late orders")

**Example (client discovery — Kimre):**
```
Problem: Customer service gets surprised by late orders.

Why 1: Why are they surprised? → They find out when customers call, not before.
Why 2: Why do they find out when customers call? → There's no proactive delay alert.
Why 3: Why is there no proactive delay alert? → No one monitors fabrication milestones against customer commit dates.
Why 4: Why does no one monitor? → Milestone data is in the production whiteboard, not in the ERP.
Why 5: Why is it on the whiteboard? → Production team added it to avoid ERP re-entry friction.

Root cause: Milestone data lives outside the ERP because the ERP's data entry flow is too slow for production pace.

Corrective action candidates:
  A) Agent monitors whiteboards (requires OCR/camera — complex)
  B) Lightweight milestone update form that writes to ERP (low friction, agent-readable)
  C) Agent monitors the ERP's "expected completion" field and alerts CS when it slips

Chosen action: B + C → Production team updates expected completion in a simple form; Order Milestone Notifier agent monitors and alerts CS proactively.
```

**Relationship to frameworks:**
```
M1 (RCCA) → M2 is the tool for M1 Step 3 (root cause)
M3 (Fishbone) → use when the "why" branches into multiple possible causes simultaneously
F31 (Feature Identification Chain) → "current friction" in the JTBD spec is often revealed by 5 Whys
F29 (Question-Centric Research) → Blocked questions in F29 may require 5 Whys to determine why the data doesn't exist
```

---

## M3 — Fishbone Diagram (Ishikawa)

**What it is:** A cause-effect mapping technique that organizes potential causes of a problem into structured categories. Where M2 (5 Whys) follows one causal chain, M3 maps all possible causes simultaneously — useful when the root cause isn't obvious and multiple hypotheses need to be tested.

**The six standard categories (6M for manufacturing):**

| Category | What it captures | Agent platform equivalent |
|---|---|---|
| **Method** | Process or procedure failures | Agent logic / decision rules |
| **Machine** | Equipment or system failures | Integration failures, API errors, data pipeline issues |
| **Material** | Input quality failures | Data quality, schema mismatches, stale patterns |
| **Man** | Human error or training gaps | Human correction patterns, override behavior |
| **Measurement** | Measurement or metric failures | False-done rate measurement, wrong KPI tracked |
| **Environment** | Context or conditions | Regulatory changes, client system changes, seasonal effects |

**Platform application:**
- When multiple agents are underperforming and the root cause isn't clear
- Discovery sprint when a client process has chronic failures with no obvious single cause
- RCCA Step 3 when 5 Whys keeps branching (multiple simultaneous causes)

**Adapted categories for agent platform (6D):**

| Category | What it captures |
|---|---|
| **Data** | Input data quality, schema, completeness, freshness |
| **Decision** | Agent logic, pattern definition, authority level misconfiguration |
| **Design** | Dashboard UX, workflow design, HITL gate placement |
| **Domain** | Client-specific business rules not captured in patterns |
| **Detection** | Monitoring gaps — false-done not detected, metrics not tracked |
| **Direction** | CAiO oversight gaps — pattern promotions without review, no quarterly cycle |

**Example (agent underperformance analysis):**
```
Problem: kimre-order-notifier-agent is generating notifications that Jordan (Customer Service) is rejecting 60% of the time.

Fishbone (6D):
  Data: Order milestone dates in ERP are not updated in real-time (production team updates at end of shift)
  Decision: Agent notification threshold is "milestone_date = today" — too broad, includes orders that are fine
  Design: Notification draft shows technical fields (order_id, milestone_code) rather than customer-facing language
  Domain: Some delay notifications don't need to go to customers (internal milestone, customer not aware of it)
  Detection: No tracking of which notification types get rejected — can't tell where the 60% comes from
  Direction: Pattern was promoted to maturity 3 without Jordan's review — no ground truth check

Action: Fix Data (real-time milestone updates), fix Decision (tighten threshold to "milestone delayed > 2 days AND customer-visible"), fix Design (plain language template), add Detection (track rejection reason per notification type)
```

**Relationship to frameworks:**
```
M1 (RCCA) → M3 is an alternative to M2 for M1 Step 3 when multiple causes exist
F27 (Michael Principle) → "Direction" category on fishbone maps directly to F27 violations
F9 (Value Measurement) → "Detection" category addresses Sacrificial metric measurement gaps
patterns/ → each category's findings produce pattern update candidates
```

---

## M4 — Failure Mode and Effects Analysis (FMEA)

**What it is:** A proactive risk technique that systematically identifies potential failure modes *before* they occur, assesses their severity and likelihood, and prioritizes which risks to mitigate. Used during design, not after failure.

**The three dimensions:**
- **Severity (S)**: How bad is the impact if this failure occurs? (1=negligible → 10=catastrophic)
- **Occurrence (O)**: How likely is this failure to happen? (1=unlikely → 10=certain)
- **Detection (D)**: How likely is this failure to be detected *before* it affects the user? (1=certain to detect → 10=impossible to detect)

**Risk Priority Number (RPN):** S × O × D. Higher = higher priority to mitigate.

**Platform application:**
- Pilot risk assessment before a new agent goes live (required for any HIGH authority agent)
- Authority level design — what's the worst case if this agent acts incorrectly?
- Integration design — which failure modes in the data pipeline affect agent reliability?

**Agent FMEA template:**

| Failure Mode | Effect | S | O | D | RPN | Mitigation |
|---|---|---|---|---|---|---|
| Agent acts on stale data | Incorrect recommendation | 7 | 4 | 3 | 84 | Add data freshness check before each run |
| Agent misclassifies severity | High-severity item auto-closed | 9 | 2 | 4 | 72 | Require human review for any CRITICAL classification |
| Authority gate bypassed | HIGH action auto-executed | 10 | 1 | 2 | 20 | Quality gate code-level enforcement (quality_gate.py) |
| Pattern promotes without CAiO review | Immature pattern at maturity 4 | 8 | 3 | 5 | 120 | Maturity-gated-promotion pattern in registry |
| False-done undetected | User loses trust silently | 8 | 4 | 6 | 192 | Sacrificial metric daily monitoring by CAiO |

**The critical FMEA insight for agent systems:** Detection (D) is the highest-risk dimension. Most agent failures are hard to detect because the agent declares success. A failure with D=8 (hard to detect) and S=8 (severe impact) is far more dangerous than a failure with S=9 but D=2 (obvious when it fails). This is why the false-done rate (F9) is the primary metric — it directly addresses the detection problem.

**Relationship to frameworks:**
```
F4 (Authority Levels) → HIGH authority agents require FMEA before pilot launch
F17 (Responsible AI) → Risk Assessment pillar requires FMEA for any production agent
F18 (Pilot Lifecycle) → FMEA is a required artifact at validated → pilot_ready transition
F9 (Value Measurement) → Sacrificial metric (false-done) directly addresses high-D failure modes
quality_gate.py → implements the mitigations for the highest-RPN failure modes
```

---

## M5 — PDCA (Plan-Do-Check-Act)

**What it is:** The foundational continuous improvement cycle. Four phases that repeat indefinitely — the cycle never closes because there is always a deeper level of optimization available.

| Phase | Action |
|---|---|
| **Plan** | Identify the problem, analyze the current state, design the improvement |
| **Do** | Implement the improvement in a controlled, observable way |
| **Check** | Measure the result — did the improvement work? What did we learn? |
| **Act** | Standardize what worked; if it didn't work, return to Plan with new knowledge |

**The formalization cycle IS PDCA for agent patterns:**

| Formalization Cycle | PDCA equivalent |
|---|---|
| Intuit → Articulate | Plan — identify the pattern, describe it |
| Formalize | Plan → Do — write the pattern definition |
| Validate | Check — test the pattern against real agent runs |
| Internalize | Act — promote the pattern; standardize it |
| Deeper Intuit | Return to Plan at a deeper level |

**Platform application — the CAiO's weekly cycle:**

```
Plan: Review false-done log, identify which pattern is underperforming
Do: Apply corrective action (retrain pattern, adjust threshold, add context)
Check: Monitor false-done rate for that pattern for next 2 weeks
Act: If improved, promote pattern to next maturity level. If not, return to Plan.
```

**PDCA at the platform level (quarterly):**

```
Plan: Coverage matrix review — which dimensions are stuck at L1-L2?
Do: Commission research or client interviews to advance those dimensions
Check: Did the new evidence change the analysis? (F29 Question-Centric Research)
Act: Update pattern registry, F28 coverage matrix, advance maturity levels
```

**The key principle:** The "Act" phase never means "we're done." It means "we've standardized what we learned, and the next cycle begins at a higher level." This is the same principle as the correction cycle never closes (F27).

**Relationship to frameworks:**
```
Formalization Cycle (whitepaper/practical/formalization-cycle.md) → PDCA is the meta-structure
F10 (Agent Maturity) → each PDCA cycle advances the agent one maturity level
F27 (Michael Principle) → correction cycle never closes = PDCA never closes
F28 (WHY/WHAT/HOW) → PDCA "Check" phase uses F28 coverage matrix to assess what advanced
```

---

## M6 — DMAIC (Define-Measure-Analyze-Improve-Control)

**What it is:** The Six Sigma improvement methodology. More rigorous than PDCA — DMAIC requires quantitative measurement at every phase and has a formal "Control" phase to prevent regression. Used for complex, high-stakes improvements where informal methods aren't sufficient.

**The five phases:**

| Phase | Action | Platform artifact |
|---|---|---|
| **Define** | State the problem, scope, stakeholders, success criteria | Problem statement + F28 WHY layer |
| **Measure** | Establish baseline metrics — where are we now? | F9 value measurement baseline + false-done rate baseline |
| **Analyze** | Find root cause using data (M2, M3) — why are we where we are? | RCCA (M1) + 5 Whys (M2) + Fishbone (M3) |
| **Improve** | Design and test the solution | Pattern update + pilot run + FMEA (M4) |
| **Control** | Standardize the solution; prevent regression | Pattern registry update + CAiO monitoring protocol |

**When DMAIC applies (vs. PDCA):**
- PDCA: routine improvement cycles, monthly pattern reviews, most CAiO work
- DMAIC: significant underperformance requiring structured investigation, any agent that fails its pilot acceptance criteria, regulatory compliance failures

**Platform application — agent pilot failure:**

```
Define: cg-quality-capa-agent has a 45% human override rate (target: <20%). Scope: CAPA triage logic for HIGH severity items. Success: override rate <20% in 30 consecutive runs.

Measure: Baseline override rate = 45% (12/26 runs in pilot month). Override pattern: 80% of overrides are for items classified HIGH that should be MEDIUM. CRITICAL never overridden.

Analyze: Why is HIGH misclassified? (5 Whys)
  → Agent classifies "customer-facing = true AND any defect" as HIGH
  → But many customer-facing items are cosmetic (packaging, labeling) and don't affect product integrity
  → HIGH should require: customer-facing + affects product integrity or regulatory compliance
  → Root cause: severity classification rule is too broad — no product integrity check

Improve: Add "product_integrity_affected" field to CAPA input schema. Update HIGH classification rule to require both customer-facing AND product_integrity_affected. Run 20 dry-run tests, verify classification.

Control: Add CAPA classification to CAiO weekly review. Add pattern "quality-capa-triage" to mfg.json with new classification logic at maturity 2. Schedule promotion review in 60 days if override rate holds below 20%.
```

**DMAIC and the F28 coverage matrix:** DMAIC's "Measure" phase advances a dimension from L1 (questions listed) to L3 (evidence gathered). DMAIC's "Control" phase advances it to L4 (validated). Running DMAIC on a key process dimension is how the platform moves from assumed to proven.

**Relationship to frameworks:**
```
F18 (Pilot Lifecycle) → DMAIC structures the validated → pilot_ready → production transition
F28 (WHY/WHAT/HOW) → Define = WHY, Measure+Analyze = WHAT, Improve+Control = HOW
M1-M3 → DMAIC Analyze phase uses RCCA, 5 Whys, Fishbone as its tools
M4 (FMEA) → DMAIC Improve phase uses FMEA to assess the proposed improvement
M5 (PDCA) → DMAIC is PDCA with formal measurement and a Control phase added
F9 (Value Measurement) → DMAIC Measure and Control phases require F9 instrumentation
```

---

## Methodology Selection Guide

| Situation | Use |
|---|---|
| Something broke — investigate quickly | M2 (5 Whys) |
| Something broke — multiple possible causes | M3 (Fishbone) |
| Something broke — need structured fix that won't recur | M1 (RCCA) |
| About to launch a new agent — assess risks proactively | M4 (FMEA) |
| Running regular monthly/quarterly improvement cycles | M5 (PDCA) |
| Agent failed its pilot — need rigorous structured recovery | M6 (DMAIC) |

**The typical sequence for a CAiO responding to a rising false-done rate:**
1. **M2** (5 Whys) → find the root cause quickly
2. **M1** (RCCA) → structure the fix and verify it
3. **M5** (PDCA) → standardize the improvement into the monthly cycle
4. **M4** (FMEA) → if the failure was severe, proactively assess other similar patterns for the same failure mode
