---
agent: general-purpose-subagent
task_ref: Task-9.1 / Epic-72
status: Completed
important_findings: false
compatibility_issues: false
ad_hoc_delegation: false
---

## Summary
Built `docs/architecture.html` — visual architecture reference for the Business Agents Platform. 57KB, 8 sections, Mermaid.js diagrams throughout.

## Output
- File: `docs/architecture.html`
- Accessible at: `http://localhost:8500/docs/architecture.html`
- Route added to `dashboards/server.py`: `@app.route("/docs/<path:filename>")`

## Details
8 sections: Platform Overview (3-layer diagram), Directory Structure (annotated tree), System Architecture (Mermaid flowchart), Database Schema (ER diagram + table), Agent Architecture (generic/specific pattern), Data Flow HITL (sequence diagram), Framework Registry (F1–F21 table), Running the Platform (quick-start code cards).

Mermaid initialized with dark theme matching platform palette (`#f97316` orange accent, `#161b2e` card bg).

## Issues
- Framework count shows F1–F21 but actual is F1–F24. generate.py should auto-update this.
- Stats strip shows 21 frameworks — needs live /api/db-stats integration.

## Next Steps
- Task 9.2: generate.py will auto-update stats in architecture.html
- Task 9.3: Per-agent spec stubs to be generated
