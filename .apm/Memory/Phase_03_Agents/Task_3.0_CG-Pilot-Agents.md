---
agent: orchestrator
task_ref: Epics-7-38-39
status: Completed
important_findings: true
compatibility_issues: false
ad_hoc_delegation: false
---

## Summary
3 CG pilot agents built, validated against mock sandbox APIs, wired into Flask server with HITL dashboard. Currently at lifecycle_stage = sandbox.

## Output
- `pilot-agents/replenishment_agent.py` — cg-replenishment-pr-agent
- `pilot-agents/demand_forecast_agent.py` — cg-demand-forecast-agent
- `pilot-agents/quality_capa_agent.py` — cg-quality-capa-agent
- All wired into `dashboards/server.py` AGENT_PATHS registry
- Run theater in operations.html, compliance.html

## Details
All agents follow pattern: subprocess run → JSON output → _extract_recommendations() → recommendations table → HITL dashboard cards.
Dry-run mode uses DRY_RUN_* hardcoded data. Live mode calls SAP (:3001) and MES (:3002) mock APIs.
Output schema: {agent, run_at, dry_run, summary, recommendations[]}.

## Important Findings
These 3 agents are the most production-ready in the platform. They represent the validated pattern for all subsequent agents. The generic→client-specific architecture was established from these.

## Next Steps
- Task 3.1: Promote to pilot_ready (validation criteria, error handling, HITL path test)
- All subsequent agents (Kimre, MFG, AP) follow this exact pattern
