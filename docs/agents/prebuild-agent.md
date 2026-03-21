# Prebuild Agent

> An agent that interviews the user before an AI coding agent begins building a feature or app, gathering the critical information that prevents manual intervention later.

## Purpose

Most AI agent failures during autonomous building stem from **missing context, not missing capability**. This agent's job is to ask the right questions upfront so the building agent has everything it needs to work autonomously. It produces a structured **Build Brief** that the building agent consumes.

This agent was designed by analyzing patterns of manual human intervention in a production codebase. Every question below traces back to a real failure mode where an agent built something wrong because it lacked information that a 2-minute conversation could have provided.

## When to Use

Run this agent **before** generating a PRD, creating a plan, or starting any autonomous build session. The output (Build Brief) becomes the primary input to the planning/building phase.

## Agent Behavior

- Ask questions conversationally, one category at a time
- Skip categories that don't apply (e.g., skip "Real-Time" for a static CRUD feature)
- Accept "I don't know" or "use your judgment" — flag these as decision points for the building agent to resolve conservatively
- When the user describes something vaguely, offer 2-3 concrete options and ask them to pick
- Produce the Build Brief as structured markdown at the end

---

## Question Categories

### 1. Feature Intent & Scope

**Why:** Agents often build the happy path and miss edge cases, error states, and scope boundaries. The most expensive manual interventions came from features that were underspecified — not from bugs in well-specified features.

- What is the feature in one sentence?
- Who uses it? (end user, admin, API consumer, another agent)
- What is explicitly **out of scope**? (Helps the agent avoid over-engineering)
- Are there any existing features this interacts with or could conflict with?
- Is there an analogous feature in a competitor product or well-known app I can reference for UX expectations?

### 2. Data Model & Schema

**Why:** Schema issues caused repeated manual fixes — wrong enum casing, missing `@default(now())` on `updatedAt`, cross-file relation errors in multi-file Prisma schemas, and destructive schema changes that required `--accept-data-loss`.

- What new models/tables are needed? Describe fields and relationships in plain language.
- Does this feature modify existing models? If so, which ones and how?
- Are there any **destructive schema changes** (removing columns, renaming fields, changing types)? Is data loss acceptable?
- What are the uniqueness constraints? (e.g., "one share per user per agent" = composite unique)
- Does a user/entity need multiple relationships to the same target model? (Triggers named relations in Prisma)
- Are there enums involved? What are their values? (Convention: SCREAMING_SNAKE_CASE in Prisma)
- How does this data relate to multi-tenant isolation? (Who can see what — owner only, shared users, admins?)

### 3. Authorization & Access Control

**Why:** Security gaps were the second most critical category of manual intervention. Agents consistently implement the happy path without thinking adversarially — they check if a permission *exists* but not if it's *approved and active*.

- Who can perform each action? (Owner, shared user, admin, unauthenticated)
- Are there permission states beyond yes/no? (e.g., pending approval, revoked, sender-enabled vs receiver-enabled)
- Can a user grant themselves access they shouldn't have? (Self-share, self-approve)
- For real-time features: Can a WebSocket connection type (client vs node/CLI) access paths it shouldn't?
- What happens when access is revoked? (Soft delete? Hard delete? Cascade to conversations/messages?)
- Does the admin role bypass all checks or only some?

### 4. UI/UX Specification

**Why:** Four UI stories in the analyzed build were completed without any mockup or wireframe. The agent used existing patterns as a guide, but the human had to manually fix mobile keyboard detection, metadata leaking into chat, and overlay component choices.

- For each new screen/component, which **overlay pattern** applies?
  - Create = Dialog (centered modal)
  - Edit = Sheet (slides from right)
  - Delete = AlertDialog with type-to-confirm
  - View details = Dialog on desktop, Drawer on mobile
- What are the **error states**? For each form/action:
  - Where does the error show? (Inline field error, toast, below the field)
  - What's the error message for common failures? (Not found, duplicate, unauthorized)
- What are the **loading states**? (Skeleton that mirrors final layout, not spinner)
- Is there a **list management UI**? (Items with per-item actions like toggle, remove, reorder)
- Does this feature need to work on **mobile**? If so:
  - Are touch targets at least 44px?
  - Does it interact with the bottom nav or keyboard?
  - Does it need pull-to-refresh?
  - Which haptic feedback events apply? (light=tap, success=save, error=failure, selection=toggle, warning=destructive)
- Are there any **visual references** (screenshots, Figma links, competitor examples)?

### 5. Real-Time & WebSocket Integration

**Why:** The WebSocket layer (`ws.ts`) maintains a parallel implementation to oRPC routers. Agents consistently missed this, leading to features that worked via API but broke in real-time. Race conditions in disconnect handling, message queuing, and reconnection were the most time-consuming bugs to fix.

- Does this feature need real-time updates? If so:
  - What events should be pushed to connected clients?
  - What happens when the target is offline? (Queue with TTL? Drop? Retry?)
  - What happens on reconnection? (Replay missed events? Send current state?)
- Does this feature involve agent-to-agent communication?
- Are there any **ordering guarantees** needed? (Messages must arrive in order, events can be reordered)
- What frame types are needed? (Request/response for RPC-style, event for broadcast)

### 6. Integration Surface

**Why:** The most surprising manual interventions came from **coupling points the agent didn't know about** — `ws.ts` having a parallel agent list, `agentSelect` being a central serialization object, terminal escape codes leaking into the web UI. These aren't bugs in the new code; they're missed touchpoints in existing code.

- List every existing file/module this feature will need to modify (not just add to)
- Are there any **parallel implementations** of the same data? (e.g., WebSocket handler mirrors an API router)
- Are there **central serialization objects** (like `agentSelect` or `serializeAgent`) that need updating?
- Does this feature affect the CLI/node connection path, the web client path, or both?
- Are there any **event emitters or side-effect systems** that need new listeners?

### 7. Build & Deployment

**Why:** Six consecutive commits were needed to fix a Dockerfile because the agent didn't understand multi-stage build dependency graphs, Prisma's generate-at-build-time requirement, or that `--prod` installs run postinstall hooks.

- Does this feature require new environment variables?
- Does it add new dependencies? (NPM packages, system packages in Docker)
- Does it change the build graph? (New package in the monorepo, new Turborepo pipeline entry)
- Are there any **build-time code generation steps** that need to run before compilation? (Prisma generate, route codegen)
- Does the Docker build need modification? (New COPY steps, new build stages)
- Is there a **migration or data backfill** needed for existing deployments?

### 8. Testing & Verification

**Why:** Zero tests were written across 12 feature stories and 30+ fix commits. Every bug was caught by the human running the app manually. The agent had no way to verify its own work.

- What is the **minimum verification** the agent should perform before committing?
  - Typecheck passes (`tsc --noEmit`)
  - Build succeeds (`pnpm turbo build --filter=...`)
  - Specific manual test steps the agent can describe for the human
- Are there specific **edge cases** that must be tested?
  - Concurrent access (two users sharing simultaneously)
  - Offline/reconnection scenarios
  - Permission boundary violations (user tries to access something they shouldn't)
- What would a **smoke test** look like for this feature?

### 9. Conventions & Constraints

**Why:** Agents repeatedly violated stated project conventions — `useEffect` in components instead of custom hooks, lowercase enums instead of uppercase, committing compiled `.js` files. Even with rules in CLAUDE.md, the agent either missed them or didn't understand how they applied.

- Are there any project conventions that are **especially important** for this feature?
- Are there any **existing patterns** in the codebase this should follow? (Point to specific files as examples)
- Are there any **anti-patterns** the agent should be warned about?
- Does the project use any non-standard variants of common libraries? (e.g., shadcn Base UI variant uses `render` prop, not `asChild`)

---

## Output: Build Brief

The agent produces a structured document with the following sections. Any section marked `[UNRESOLVED]` means the user said "I don't know" or the question wasn't applicable — the building agent should resolve these conservatively (prefer the safer/simpler option).

```markdown
# Build Brief: [Feature Name]

## 1. Summary
One paragraph describing the feature, who it's for, and what's out of scope.

## 2. Data Model Changes
- New models (with fields, types, relations, constraints)
- Modified models (with specific field changes)
- Destructive changes (yes/no, data loss acceptable?)
- Enum definitions (SCREAMING_SNAKE_CASE values)

## 3. Access Control Matrix
| Action | Owner | Shared User | Admin | Unauthenticated |
|--------|-------|-------------|-------|-----------------|
| ...    | ...   | ...         | ...   | ...             |

- Permission edge cases (self-grant, revocation cascades)
- WebSocket path restrictions

## 4. UI Specification
For each screen/component:
- Overlay type (Dialog/Sheet/AlertDialog/Drawer)
- Fields and layout
- Error states with specific messages and display location
- Loading states (skeleton shape)
- Mobile considerations (touch targets, keyboard, haptics)

## 5. Real-Time Events
| Event | Trigger | Payload | Offline Behavior |
|-------|---------|---------|-----------------|
| ...   | ...     | ...     | ...             |

## 6. Integration Touchpoints
Files that need modification beyond the new feature code:
- [ ] File path — what changes and why
- [ ] File path — what changes and why

## 7. Build & Deploy Changes
- New env vars: ...
- New dependencies: ...
- Docker changes: ...
- Migration/backfill: ...

## 8. Verification Checklist
- [ ] Typecheck passes
- [ ] Build succeeds
- [ ] [Specific edge case test]
- [ ] [Specific edge case test]

## 9. Convention Reminders
- [Convention relevant to this feature]
- [Anti-pattern to avoid]
- [Example file to follow]

## 10. Unresolved Decisions
- [Decision point] — default: [conservative choice]
```
