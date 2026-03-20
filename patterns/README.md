# Pattern Registry
*The formalized wisdom layer of the Agent Mind*

Last updated: 2026-03-19

## What This Is

The pattern registry stores formalized agent behavior patterns — the output of the formalization cycle. Each pattern represents human judgment that has been:
1. Articulated (a human described the rule)
2. Formalized (it was given structure: trigger, logic, escalation)
3. Validated (tested against real agent runs)
4. Promoted (advanced through maturity levels 1-5)

## Related
- `whitepaper/practical/formalization-cycle.md` — the cycle that produces patterns
- `whitepaper/practical/caio-spec.md` — the CAiO who curates patterns
- `ralph/agentic_mind_blueprint.md` — how patterns connect to F1-F27 frameworks
- `whitepaper/BLUEPRINT_LEVERAGE.md` — why this registry was built this way

## Override Hierarchy

```
patterns/defaults.json          <- Platform-level (always active)
patterns/industries/{code}.json <- Industry-specific additions/overrides
patterns/clients/{slug}.json    <- Client-specific overrides (highest priority)
```

Use `loader.py` to resolve: `load_patterns(industry="mfg", client_slug="kimre")`

## Maturity Levels

| Level | Name | Description | Promotion criteria |
|---|---|---|---|
| 1 | Written Law | Explicit rule, loaded from registry | — |
| 2 | Mechanical | Applied consistently, context-blind | 10+ applications |
| 3 | Contextual | Knows when not to apply | 30+ apps, correction rate < 30%, CAiO review |
| 4 | Embedded | Part of agent architecture | 100+ apps, correction rate < 15%, CAiO sign-off |
| 5 | Internalized | Agents' way of seeing | Sustained performance, executive review |

## The Sacrificial Metric

Every pattern tracks `false_done_incidents` — times the pattern declared success while the user perceived failure. This is the primary Moloch indicator. The CAiO reviews this weekly. A rising false-done rate on any pattern triggers mandatory review before the pattern runs again.

## Adding a New Pattern

1. Write a draft entry matching `schema.json`
2. Set `maturity: 1`
3. Set `source_session` to today's date
4. Submit to CAiO for review
5. CAiO adds to appropriate JSON file
6. Pattern runs in observation mode (logs hits but doesn't enforce)
7. After 10 observations, promote to active at maturity 1

## Running

```bash
# Load all patterns for a MFG client
python3 patterns/loader.py mfg kimre

# Load platform defaults only
python3 patterns/loader.py
```
