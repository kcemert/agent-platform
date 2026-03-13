# Ralph Agent Instructions — Multi-Project Workspace

You are an autonomous coding agent working across multiple projects in this workspace.

## Workspace Structure

```
/Users/keith_ai/Documents/Agentic Projects/
├── ralph/              ← You live here (prd.json, progress.txt)
├── business-agents/    ← Agent repository DB (business_agents.db + query.py)
├── agent-os/           ← Standards management (standards/, specs/)
├── office-skills/      ← Office doc generation (PPTX, DOCX, XLSX, PDF)
├── joji-charity/       ← Charity website (HTML/CSS/JS, has its own git)
├── party-invites/      ← Party invites project (has skills)
└── [new projects]/     ← New projects created as needed
```

## Key Capabilities Available

- **Office docs**: Use `office-skills/` to create PPTX, DOCX, XLSX, PDF. Read `office-skills/public/pptx/SKILL.md` before creating any presentation.
- **Standards**: Run `/discover-standards` or `/inject-standards` for project conventions
- **DB queries**: `python3 business-agents/query.py <command>` for process/agent data

## Your Task Each Iteration

1. Check what other agents are doing: `python3 business-agents/query.py status`
2. Read `ralph/prd.json` — find the highest priority story where `passes: false`
   - Skip stories already claimed by another session (check story_claims in DB)
3. Read `ralph/progress.txt` — check **Codebase Patterns** section first
4. **Claim your story atomically** before starting any work:
   ```bash
   python3 business-agents/query.py claim STORY-ID $SESSION_ID
   ```
   If exit code is 1 (already claimed), pick the next unclaimed story.
5. Send a heartbeat with your claimed story:
   ```bash
   python3 business-agents/query.py heartbeat $SESSION_ID STORY-ID project-name
   ```
6. Check the story's `project` field to know which directory to work in
7. If the story requires a new project, create it under the workspace root
8. Implement that **single user story**
9. Run quality checks appropriate for the project (lint, typecheck, test, build)
10. Commit ALL changes to the relevant project's git repo with:
    `feat: [Story ID] - [Story Title]`
11. Update `ralph/prd.json` — set `passes: true` for the completed story
12. Release the story claim:
    ```bash
    python3 business-agents/query.py release STORY-ID complete
    ```
13. Append your progress to `ralph/progress.txt`
14. Log the run to the episodic memory DB (see below)

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
- business-agents: SQLite DB at business-agents/business_agents.db, query with python3 business-agents/query.py
- [new patterns go here]
```

## Episodic Memory — Log Every Run

After completing (or failing) a story, log it to the agent runs database:

```bash
python3 /Users/keith_ai/Documents/Agentic\ Projects/business-agents/query.py log_run '{
  "story_id": "STORY-001",
  "story_title": "Story title here",
  "project": "project-name",
  "outcome": "success",
  "files_changed": "path/to/file1.py, path/to/file2.ts",
  "tools_used": "Edit, Bash, Write",
  "learnings": "Key insight discovered during this iteration",
  "patterns_added": "Pattern added to progress.txt if any",
  "commit_hash": "abc1234",
  "iteration_num": 1,
  "duration_secs": 120
}'
```

outcome must be one of: success | partial | failed | skipped
Always log even on failure — set outcome to "failed" and fill error_summary.

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
