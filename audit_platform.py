#!/usr/bin/env python3
"""
audit_platform.py — Platform consistency audit.
Run after each session or epic to catch drift between registry, index.html, DB, and MEMORY.md.
Usage: python3 audit_platform.py
"""

import json
import os
import re
import sqlite3
import sys
from pathlib import Path

WS = Path("/Users/keith_ai/Documents/Agentic Projects")
DB = WS / "business-agents" / "business_agents.db"
REGISTRY = WS / "registry.json"
INDEX = WS / "index.html"
MEMORY = Path("/Users/keith_ai/.claude/projects/-Users-keith-ai-Documents-Agentic-Projects/memory/MEMORY.md")

PASS = "✅"
WARN = "⚠️ "
FAIL = "❌"

issues = []

# ── 1. Registry ────────────────────────────────────────────────────────────────
registry_data = json.loads(REGISTRY.read_text())
registry = registry_data.get("views", registry_data) if isinstance(registry_data, dict) else registry_data
reg_count = len(registry)

# Count stat badge in index.html
index_html = INDEX.read_text()
badge_match = re.search(r'(\d+)\s+tools', index_html)
badge_count = int(badge_match.group(1)) if badge_match else None

# Count tool cards in index.html (each card link uses class="card ")
card_count = index_html.count('class="card ')

print(f"\n{'='*55}")
print("  PLATFORM AUDIT")
print(f"{'='*55}")

print(f"\n── Registry & Index ──")
print(f"  registry.json entries : {reg_count}")
print(f"  index.html badge      : {badge_count}")
print(f"  index.html tool-cards : {card_count}")

if badge_count and badge_count != reg_count:
    msg = f"Badge says {badge_count} but registry has {reg_count}"
    issues.append(WARN + msg)
    print(f"  {WARN} {msg}")
else:
    print(f"  {PASS} Badge matches registry")

if card_count != reg_count:
    msg = f"Tool cards ({card_count}) don't match registry entries ({reg_count})"
    issues.append(WARN + msg)
    print(f"  {WARN} {msg}")
else:
    print(f"  {PASS} Tool cards match registry")

# Check all registry paths exist
missing = [e.get("path","") for e in registry if not (WS / e.get("path","")).exists() and e.get("path")]
if missing:
    for m in missing:
        issues.append(FAIL + f" Missing file: {m}")
        print(f"  {FAIL} Missing: {m}")
else:
    print(f"  {PASS} All registry paths exist")

# ── 2. Database ────────────────────────────────────────────────────────────────
print(f"\n── Database ──")
if not DB.exists():
    issues.append(FAIL + " DB not found")
    print(f"  {FAIL} DB not found at {DB}")
else:
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    def q(sql):
        return cur.execute(sql).fetchone()[0]

    industry_count     = q("SELECT COUNT(*) FROM industries")
    process_count      = q("SELECT COUNT(*) FROM processes")
    blueprint_count    = q("SELECT COUNT(*) FROM agent_blueprints")
    action_count       = q("SELECT COUNT(*) FROM process_agent_actions")
    system_count       = q("SELECT COUNT(*) FROM systems")
    function_count     = q("SELECT COUNT(*) FROM functions")

    print(f"  Industries   : {industry_count}")
    print(f"  Processes    : {process_count}")
    print(f"  Blueprints   : {blueprint_count}")
    print(f"  Agent actions: {action_count}")
    print(f"  Systems      : {system_count}")
    print(f"  Functions    : {function_count}")

    # Check all 12 functions have agent actions
    zero_fn = cur.execute("""
        SELECT f.name FROM functions f
        WHERE f.id NOT IN (
            SELECT DISTINCT p.function_id FROM processes p
            JOIN process_agent_actions paa ON paa.process_id = p.id
        )
    """).fetchall()
    if zero_fn:
        for fn in zero_fn:
            issues.append(WARN + f"Function with no agent actions: {fn[0]}")
            print(f"  {WARN} No agent actions: {fn[0]}")
    else:
        print(f"  {PASS} All {function_count} functions have agent actions")

    # Blueprints sanity: count by authority level
    auth_dist = cur.execute("""
        SELECT authority_level, COUNT(*) FROM agent_blueprints GROUP BY authority_level
    """).fetchall()
    auth_str = ", ".join(f"{a}:{n}" for a, n in auth_dist)
    print(f"  Authority dist: {auth_str}")

    conn.close()

# ── 3. MEMORY.md staleness check ───────────────────────────────────────────────
print(f"\n── MEMORY.md ──")
stale = False
if MEMORY.exists():
    mem = MEMORY.read_text()

    # Count-based checks
    mem_bp_match = re.search(r'(\d+) blueprints', mem)
    mem_bp = int(mem_bp_match.group(1)) if mem_bp_match else None
    if mem_bp and DB.exists():
        conn = sqlite3.connect(DB)
        db_bp = conn.execute("SELECT COUNT(*) FROM agent_blueprints").fetchone()[0]
        conn.close()
        if mem_bp != db_bp:
            msg = f"MEMORY.md says {mem_bp} blueprints, DB has {db_bp}"
            issues.append(FAIL + " " + msg)
            print(f"  {FAIL} {msg}")
            stale = True
        else:
            print(f"  {PASS} Blueprint count matches ({db_bp})")

    mem_tool_match = re.search(r'(\d+) tools', mem)
    mem_tools = int(mem_tool_match.group(1)) if mem_tool_match else None
    if mem_tools and mem_tools != reg_count:
        msg = f"MEMORY.md says {mem_tools} tools, registry has {reg_count}"
        issues.append(FAIL + " " + msg)
        print(f"  {FAIL} {msg}")
        stale = True
    elif mem_tools:
        print(f"  {PASS} Tool count matches ({reg_count})")

    # Timestamp-based staleness: DB newer than MEMORY.md by more than 2 min
    if DB.exists():
        db_age = DB.stat().st_mtime
        mem_age = MEMORY.stat().st_mtime
        lag_seconds = db_age - mem_age
        if lag_seconds > 120:
            import datetime
            lag_min = int(lag_seconds // 60)
            msg = f"DB is {lag_min}min newer than MEMORY.md — likely not updated after last work"
            issues.append(WARN + msg)
            print(f"  {WARN} {msg}")
            stale = True
        else:
            print(f"  {PASS} MEMORY.md is current (within 2min of DB)")
else:
    issues.append(FAIL + " MEMORY.md not found")
    print(f"  {FAIL} MEMORY.md not found")
    stale = True

# ── 4. Summary ─────────────────────────────────────────────────────────────────
print(f"\n── Summary ──")
if issues:
    print(f"  {len(issues)} issue(s) found:")
    for i in issues:
        print(f"    {i}")
else:
    print(f"  {PASS} All checks passed — platform is consistent")

if stale or issues:
    print(f"""
{'!'*55}
  WRAP-UP REQUIRED — SESSION NOT CLEAN
{'!'*55}
  The following must be completed before this session ends:

  1. Update MEMORY.md — reflect new epics/blueprints/tools
  2. Sync registry.json + index.html badge count
  3. Update ralph/roadmap.md — mark completed epics ✅
  4. Re-run: python3 audit_platform.py  (must be clean)

  MEMORY.md: {MEMORY}
{'!'*55}
""")
    sys.exit(1)
else:
    print(f"\n{'='*55}")
    print("  Session is clean. Safe to end.")
    print(f"{'='*55}\n")
