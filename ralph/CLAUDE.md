# Ralph Agent Instructions — Multi-Project Workspace

You are an autonomous coding agent working across multiple projects in this workspace.

## Workspace Structure

```
/Users/keith_ai/Documents/Agentic Projects/
├── ralph/              ← You live here (prd.json, progress.txt)
├── joji-charity/       ← Charity website (HTML/CSS/JS, has its own git)
├── party-invites/      ← Party invites project (has skills)
└── [new projects]/     ← New projects created as needed
```

## Your Task Each Iteration

1. Read `ralph/prd.json` — find the highest priority story where `passes: false`
2. Read `ralph/progress.txt` — check **Codebase Patterns** section first
3. Check the story's `project` field to know which directory to work in
4. If the story requires a new project, create it under the workspace root
5. Implement that **single user story**
6. Run quality checks appropriate for the project (lint, typecheck, test, build)
7. Commit ALL changes to the relevant project's git repo with:
   `feat: [Story ID] - [Story Title]`
   - For existing projects (joji-charity, party-invites): commit to their own git repo
   - For new projects: initialize git if needed, then commit
8. Update `ralph/prd.json` — set `passes: true` for the completed story
9. Append your progress to `ralph/progress.txt`

## Progress Report Format

APPEND to ralph/progress.txt (never replace, always append):
```
## [Date/Time] - [Story ID] - [Project]
- What was implemented
- Files changed
- **Learnings for future iterations:**
  - Patterns discovered
  - Gotchas encountered
  - Useful context
---
```

## Consolidate Patterns

If you discover a reusable pattern, add it to the `## Codebase Patterns` section at the TOP of progress.txt:

```
## Codebase Patterns
- joji-charity: Static HTML site, no build step needed, just edit files directly
- party-invites: Uses iMessage/SMS via skills
- [new patterns go here]
```

## Quality Requirements

- Commit only working code
- Keep changes focused to one story
- Follow existing patterns in each project
- For new projects: set up proper tooling (package.json, tsconfig, etc.) before coding

## Stop Condition

After completing a story, check if ALL stories have `passes: true`.

If ALL complete:
<promise>COMPLETE</promise>

If stories remain with `passes: false`, end your response normally — another iteration will continue.

## Important

- Work on ONE story per iteration
- Always cd into the correct project directory before working
- The ralph/ directory is at `/Users/keith_ai/Documents/Agentic Projects/ralph/`
- When creating a new project, create it under `/Users/keith_ai/Documents/Agentic Projects/`
- Read progress.txt Codebase Patterns section before starting — it has critical context
