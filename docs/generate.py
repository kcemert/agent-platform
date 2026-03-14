#!/usr/bin/env python3
"""
Business Agents Platform — Documentation Generator
Run: python3 docs/generate.py [--agents-only | --status]
Reads: DB, pilot-agents/, dashboards/server.py, ralph/frameworks.md
Writes: docs/status.json, docs/agents/index.html, docs/api/reference.html, docs/agents/[slug].md stubs
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
SCRIPT_DIR  = Path(__file__).parent                         # docs/
WORKSPACE   = SCRIPT_DIR.parent                             # Agentic Projects/
DB_PATH     = WORKSPACE / "business-agents" / "business_agents.db"
SERVER_PATH = WORKSPACE / "dashboards" / "server.py"
FRAMEWORKS_PATH = WORKSPACE / "ralph" / "frameworks.md"
AGENTS_DIR  = WORKSPACE / "pilot-agents"
DOCS_DIR    = SCRIPT_DIR
AGENTS_DOCS = DOCS_DIR / "agents"
API_DOCS    = DOCS_DIR / "api"

GENERATOR_VERSION = "1.0"

# ── Known slug map (file → slug) ───────────────────────────────────────────
SLUG_MAP = {
    "replenishment_agent.py":           "cg-replenishment-pr-agent",
    "demand_forecast_agent.py":         "cg-demand-forecast-agent",
    "quality_capa_agent.py":            "cg-quality-capa-agent",
    "marketing_agent.py":               "marketing-agent",
    "research_agent.py":                "research-agent",
    "business_model_agent.py":          "business-model-agent",
    "mfg-predictive-maintenance-agent.py": "mfg-predictive-maintenance-agent",
    "ap-invoice-processing.py":         "ap-invoice-processing",
    "orchestrator.py":                  "orchestrator",
    "stakeholder-enrichment-agent.py":  "stakeholder-enrichment-agent",
    # kimre/
    "kimre/rfq_quote_agent.py":             "kimre-rfq-quote-agent",
    "kimre/quality_compliance_agent.py":    "kimre-quality-compliance-agent",
    "kimre/order_notifier_agent.py":        "kimre-order-notifier-agent",
    "kimre/retrofit_reorder_agent.py":      "kimre-retrofit-reorder-agent",
    "kimre/marketing_agent.py":             "kimre-marketing-agent",
    "kimre/research_agent.py":              "kimre-research-agent",
    "kimre/business_model_agent.py":        "kimre-business-model-agent",
}

# ── Utility ────────────────────────────────────────────────────────────────
def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def now_date() -> str:
    return datetime.now().strftime("%Y-%m-%d")

def snake_to_readable(name: str) -> str:
    """Convert snake_case / slug to readable title."""
    name = name.replace("_", " ").replace("-", " ")
    return " ".join(w.capitalize() for w in name.split())


# ══════════════════════════════════════════════════════════════════════════════
# SECTION A — DB Stats
# ══════════════════════════════════════════════════════════════════════════════
def section_a_db_stats() -> dict:
    """Query the SQLite DB for platform statistics."""
    stats = {
        "industries": 0,
        "processes": 0,
        "blueprints": 0,
        "agent_actions": 0,
        "systems": 0,
        "blueprint_lifecycle": {},
        "blueprint_size_fit": {},
        "industry_process_coverage": {},
    }

    if not DB_PATH.exists():
        print(f"  [WARN] DB not found at {DB_PATH}", file=sys.stderr)
        return stats

    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=10)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Basic counts
        stats["industries"]    = cur.execute("SELECT COUNT(*) FROM industries").fetchone()[0]
        stats["processes"]     = cur.execute("SELECT COUNT(*) FROM processes").fetchone()[0]
        stats["blueprints"]    = cur.execute("SELECT COUNT(*) FROM agent_blueprints").fetchone()[0]
        stats["agent_actions"] = cur.execute("SELECT COUNT(*) FROM process_agent_actions").fetchone()[0]
        stats["systems"]       = cur.execute("SELECT COUNT(*) FROM systems").fetchone()[0]

        # Blueprint lifecycle distribution
        rows = cur.execute(
            "SELECT lifecycle_stage, COUNT(*) as n FROM agent_blueprints GROUP BY lifecycle_stage"
        ).fetchall()
        stats["blueprint_lifecycle"] = {r["lifecycle_stage"] or "unknown": r["n"] for r in rows}

        # Blueprint size_fit distribution
        rows = cur.execute(
            "SELECT size_fit, COUNT(*) as n FROM agent_blueprints GROUP BY size_fit"
        ).fetchall()
        stats["blueprint_size_fit"] = {r["size_fit"] or "unknown": r["n"] for r in rows}

        # Per-industry process count
        rows = cur.execute("""
            SELECT i.code, i.name, COUNT(ip.process_id) as proc_count
            FROM industries i
            LEFT JOIN industry_processes ip ON ip.industry_id = i.id
            GROUP BY i.id
            ORDER BY proc_count DESC
        """).fetchall()
        stats["industry_process_coverage"] = {r["code"]: r["proc_count"] for r in rows}

        # Blueprint lifecycle lookup for agent catalog
        rows = cur.execute(
            "SELECT slug, lifecycle_stage FROM agent_blueprints"
        ).fetchall()
        stats["_blueprint_lifecycle_by_slug"] = {r["slug"]: r["lifecycle_stage"] for r in rows}

        conn.close()
    except Exception as e:
        print(f"  [WARN] DB query failed: {e}", file=sys.stderr)

    return stats


# ══════════════════════════════════════════════════════════════════════════════
# SECTION B — Agent Discovery
# ══════════════════════════════════════════════════════════════════════════════
def extract_docstring_first_line(filepath: Path) -> str:
    """Extract the first meaningful line of a Python file's module docstring."""
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        # Match triple-quoted docstring at top of file (after shebang/encoding)
        m = re.search(r'"""(.*?)"""', content, re.DOTALL)
        if m:
            lines = [l.strip() for l in m.group(1).strip().splitlines() if l.strip()]
            if lines:
                return lines[0]
    except Exception:
        pass
    return ""


def section_b_agent_discovery() -> list[dict]:
    """Scan pilot-agents/ and kimre/ for Python agent files."""
    agents = []

    if not AGENTS_DIR.exists():
        print(f"  [WARN] Agents dir not found: {AGENTS_DIR}", file=sys.stderr)
        return agents

    # Files to skip (non-agent scripts)
    skip_files = {"__init__.py", "generate_dashboard.py", "agent_runner.py"}

    def process_file(filepath: Path, rel_key: str):
        filename = filepath.name
        if filename in skip_files:
            return

        slug = SLUG_MAP.get(rel_key) or SLUG_MAP.get(filename) or filepath.stem.replace("_", "-")
        description = extract_docstring_first_line(filepath)
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        has_dry_run = bool(re.search(r"dry.run|DRY_RUN", content, re.IGNORECASE))
        has_client_profile = bool(re.search(r"client.profile|CLIENT_PROFILE", content, re.IGNORECASE))
        size_kb = round(filepath.stat().st_size / 1024, 1)

        agents.append({
            "slug": slug,
            "file": str(filepath.relative_to(WORKSPACE)),
            "filename": filename,
            "description": description,
            "has_dry_run": has_dry_run,
            "has_client_profile": has_client_profile,
            "size_kb": size_kb,
            "lifecycle": "unknown",  # filled later from DB
        })

    # Top-level .py files
    for fp in sorted(AGENTS_DIR.glob("*.py")):
        process_file(fp, fp.name)

    # kimre/ subdirectory
    kimre_dir = AGENTS_DIR / "kimre"
    if kimre_dir.exists():
        for fp in sorted(kimre_dir.glob("*.py")):
            process_file(fp, f"kimre/{fp.name}")

    return agents


# ══════════════════════════════════════════════════════════════════════════════
# SECTION C — API Route Discovery
# ══════════════════════════════════════════════════════════════════════════════
def section_c_api_routes() -> list[dict]:
    """Parse dashboards/server.py for Flask route decorators."""
    routes = []

    if not SERVER_PATH.exists():
        print(f"  [WARN] server.py not found at {SERVER_PATH}", file=sys.stderr)
        return routes

    content = SERVER_PATH.read_text(encoding="utf-8", errors="ignore")

    # Match @app.route("...") optionally with methods=[...]
    pattern = re.compile(
        r'@app\.route\("([^"]+)"(?:,\s*methods=\[([^\]]+)\])?\)\s*\ndef\s+(\w+)',
        re.MULTILINE,
    )

    internal_paths = {"/", "/<path:filename>"}

    for m in pattern.finditer(content):
        path    = m.group(1)
        methods_raw = m.group(2)
        func    = m.group(3)

        if path in internal_paths and not path.startswith("/api"):
            # Keep static-serve routes but flag them
            pass

        if methods_raw:
            methods = [x.strip().strip('"').strip("'") for x in methods_raw.split(",")]
        else:
            methods = ["GET"]

        routes.append({
            "path": path,
            "methods": methods,
            "function": func,
            "description": snake_to_readable(func),
            "is_api": path.startswith("/api"),
        })

    return routes


# ══════════════════════════════════════════════════════════════════════════════
# SECTION D — Framework Count
# ══════════════════════════════════════════════════════════════════════════════
def section_d_frameworks() -> tuple[int, list[dict]]:
    """Parse ralph/frameworks.md and return count + framework list."""
    frameworks = []

    if not FRAMEWORKS_PATH.exists():
        print(f"  [WARN] frameworks.md not found at {FRAMEWORKS_PATH}", file=sys.stderr)
        return 0, frameworks

    content = FRAMEWORKS_PATH.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()

    i = 0
    while i < len(lines):
        line = lines[i]
        # Match "## N. Title" or "## N Title"
        m = re.match(r"^##\s+(\d+)\.\s+(.+)$", line)
        if not m:
            # Also match "## Title" style without number (for future-proofing)
            m = re.match(r"^##\s+(.+)$", line)
            if m and not m.group(1).startswith("#"):
                num = None
                title = m.group(1).strip()
            else:
                i += 1
                continue
        else:
            num = int(m.group(1))
            title = m.group(2).strip()

        # Get first non-empty line after heading as description
        desc = ""
        j = i + 1
        while j < len(lines):
            candidate = lines[j].strip()
            if candidate and not candidate.startswith("#"):
                # Strip markdown bold
                candidate = re.sub(r"\*\*([^*]+)\*\*", r"\1", candidate)
                desc = candidate[:120]
                break
            j += 1

        frameworks.append({"num": num, "title": title, "description": desc})
        i += 1

    return len(frameworks), frameworks


# ══════════════════════════════════════════════════════════════════════════════
# SECTION E — Write docs/status.json
# ══════════════════════════════════════════════════════════════════════════════
def section_e_write_status(db_stats: dict, agents: list[dict], routes: list[dict],
                            framework_count: int) -> dict:
    """Assemble and write docs/status.json."""
    ts = now_iso()
    today = now_date()

    # Determine which doc sections exist and their coverage
    sections = []

    def check_section(sid, fname, manual=False, notes=""):
        fpath = DOCS_DIR / fname
        exists = fpath.exists()
        auto = not manual
        entry = {
            "id": sid,
            "file": f"docs/{fname}",
            "exists": exists,
            "last_verified": None,
            "stale": False,
            "auto_generated": auto,
            "notes": notes,
        }
        if auto and exists:
            entry["last_generated"] = ts
            entry["coverage"] = 1.0
        elif manual and exists:
            entry["last_generated"] = today
            entry["coverage"] = 0.75
        else:
            entry["last_generated"] = None
            entry["coverage"] = 0.0

        if notes:
            entry["notes"] = notes
        return entry

    sections.append(check_section(
        "architecture", "architecture.html", manual=True,
        notes="Manually built. Run generate.py to keep stats strip current."
    ))
    sections.append(check_section("agents/index", "agents/index.html"))
    sections.append(check_section("api/reference", "api/reference.html"))

    # Per-agent spec stubs
    agent_slugs_with_specs = []
    agent_slugs_without_specs = []
    for ag in agents:
        spec_path = AGENTS_DOCS / f"{ag['slug']}.md"
        if spec_path.exists():
            agent_slugs_with_specs.append(ag["slug"])
            sections.append(check_section(f"agents/{ag['slug']}", f"agents/{ag['slug']}.md"))
        else:
            agent_slugs_without_specs.append(ag["slug"])

    # Guide stubs
    missing_sections = []
    if not (DOCS_DIR / "guides" / "developer.md").exists():
        missing_sections.append("guides/developer")
    if not (DOCS_DIR / "guides" / "client-kimre.md").exists():
        missing_sections.append("guides/client-kimre")

    # Overall coverage
    total_expected = len(sections) + len(missing_sections)
    covered = sum(1 for s in sections if s.get("coverage", 0) > 0)
    overall = round(covered / total_expected, 2) if total_expected > 0 else 0.0

    api_endpoints = len([r for r in routes if r["is_api"]])

    status = {
        "generated_at": ts,
        "generator_version": GENERATOR_VERSION,
        "platform_stats": {
            "industries": db_stats.get("industries", 0),
            "processes": db_stats.get("processes", 0),
            "blueprints": db_stats.get("blueprints", 0),
            "agent_actions": db_stats.get("agent_actions", 0),
            "systems": db_stats.get("systems", 0),
            "frameworks": framework_count,
            "agents_discovered": len(agents),
            "api_endpoints": api_endpoints,
        },
        "blueprint_lifecycle": db_stats.get("blueprint_lifecycle", {}),
        "blueprint_size_fit": db_stats.get("blueprint_size_fit", {}),
        "sections": sections,
        "overall_coverage": overall,
        "stale_sections": agent_slugs_without_specs,
        "missing_sections": missing_sections,
    }

    out_path = DOCS_DIR / "status.json"
    out_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
    print(f"  Wrote {out_path.relative_to(WORKSPACE)}")

    return status


# ══════════════════════════════════════════════════════════════════════════════
# SECTION F — Write docs/agents/index.html
# ══════════════════════════════════════════════════════════════════════════════
LIFECYCLE_BADGE_COLORS = {
    "blueprint":   ("#1e293b", "#94a3b8"),
    "scaffolded":  ("#1e3a5f", "#60a5fa"),
    "sandbox":     ("#2d1b4e", "#a855f7"),
    "validated":   ("#1a3a2e", "#34d399"),
    "pilot_ready": ("#3a2a10", "#f59e0b"),
    "production":  ("#1a3020", "#22c55e"),
    "unknown":     ("#1e293b", "#64748b"),
}

def lifecycle_badge_html(stage: str) -> str:
    stage = stage or "unknown"
    bg, fg = LIFECYCLE_BADGE_COLORS.get(stage, LIFECYCLE_BADGE_COLORS["unknown"])
    return (f'<span style="background:{bg};color:{fg};padding:2px 8px;'
            f'border-radius:3px;font-size:11px;font-weight:600;'
            f'text-transform:uppercase;letter-spacing:.04em">{stage}</span>')

def bool_badge(val: bool, label: str) -> str:
    if val:
        return (f'<span style="color:#22c55e;font-weight:600">{label}</span>')
    return f'<span style="color:#475569">—</span>'


def section_f_agents_index(agents: list[dict], ts: str) -> None:
    """Write docs/agents/index.html — the auto-generated agent catalog."""
    specs_exist = sum(1 for ag in agents if (AGENTS_DOCS / f"{ag['slug']}.md").exists())

    rows_html = ""
    for ag in agents:
        spec_path = AGENTS_DOCS / f"{ag['slug']}.md"
        spec_exists = spec_path.exists()
        spec_link = (f'<a href="{ag["slug"]}.md" style="color:#f97316;text-decoration:none">'
                     f'View Spec</a>'
                     if spec_exists else
                     f'<span style="color:#475569;font-style:italic">No spec</span>')
        desc = ag["description"] or "<em style='color:#475569'>No docstring</em>"
        rows_html += f"""
          <tr>
            <td><code style="color:#f1f5f9;font-family:JetBrains Mono,monospace;font-size:12px">{ag['slug']}</code></td>
            <td style="color:#94a3b8;max-width:340px">{desc}</td>
            <td>{lifecycle_badge_html(ag['lifecycle'])}</td>
            <td style="text-align:center">{bool_badge(ag['has_dry_run'], '&#10003;')}</td>
            <td style="text-align:center">{bool_badge(ag['has_client_profile'], '&#10003;')}</td>
            <td>{spec_link}</td>
            <td style="color:#64748b;text-align:right">{ag['size_kb']} KB</td>
          </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Agent Catalog — Business Agents Platform</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #0f1117; --card: #161b2e; --border: #1e293b;
      --text: #f1f5f9; --muted: #64748b; --accent: #f97316;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: var(--bg); color: var(--text); font-family: Inter, sans-serif;
             font-size: 15px; line-height: 1.65; padding: 48px 56px; }}
    .header-banner {{
      background: var(--card); border: 1px solid var(--border); border-radius: 8px;
      padding: 20px 24px; margin-bottom: 32px;
      display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;
    }}
    .header-banner .meta {{ font-size: 13px; color: var(--muted); }}
    .header-banner .meta strong {{ color: var(--accent); }}
    .header-banner a {{ color: var(--accent); font-size: 13px; text-decoration: none; }}
    h1 {{ font-size: 28px; font-weight: 700; margin-bottom: 6px; }}
    .sub {{ color: var(--muted); font-size: 14px; margin-bottom: 32px; }}
    .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 8px;
              overflow: hidden; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    thead tr {{ background: rgba(249,115,22,0.1); border-bottom: 1px solid var(--border); }}
    thead th {{ padding: 10px 14px; text-align: left; font-weight: 600; color: var(--accent);
                font-size: 11px; letter-spacing: .05em; text-transform: uppercase; }}
    tbody tr {{ border-bottom: 1px solid var(--border); transition: background .1s; }}
    tbody tr:hover {{ background: rgba(255,255,255,.02); }}
    tbody tr:last-child {{ border-bottom: none; }}
    tbody td {{ padding: 10px 14px; color: #94a3b8; vertical-align: middle; }}
    .back-link {{ display: inline-block; margin-bottom: 24px; color: var(--muted);
                  font-size: 13px; text-decoration: none; }}
    .back-link:hover {{ color: var(--text); }}
    footer {{ margin-top: 48px; padding-top: 20px; border-top: 1px solid var(--border);
               font-size: 12px; color: var(--muted); }}
  </style>
</head>
<body>
  <a class="back-link" href="../index.html">&#8592; Docs Hub</a>

  <h1>Agent Catalog</h1>
  <p class="sub">All discovered pilot agents with lifecycle status, capabilities, and spec links.</p>

  <div class="header-banner">
    <div class="meta">
      Auto-generated by <code>docs/generate.py</code> on <strong>{ts}</strong>
      &nbsp;&middot;&nbsp; <strong>{len(agents)}</strong> agents discovered
      &nbsp;&middot;&nbsp; <strong>{specs_exist}</strong> with specs
    </div>
    <a href="../status.json">View status.json</a>
  </div>

  <div class="card">
    <table>
      <thead>
        <tr>
          <th>Slug</th>
          <th>Description</th>
          <th>Lifecycle</th>
          <th style="text-align:center">Dry-run</th>
          <th style="text-align:center">Client-Profile</th>
          <th>Spec</th>
          <th style="text-align:right">File Size</th>
        </tr>
      </thead>
      <tbody>{rows_html}
      </tbody>
    </table>
  </div>

  <footer>
    Auto-generated by docs/generate.py &middot; {ts} &middot;
    Source: <code>pilot-agents/</code> directory scan
  </footer>
</body>
</html>
"""
    out = AGENTS_DOCS / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"  Wrote {out.relative_to(WORKSPACE)}")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION G — Write docs/agents/[slug].md stubs
# ══════════════════════════════════════════════════════════════════════════════
def section_g_agent_stubs(agents: list[dict]) -> int:
    """Write .md spec stubs for agents that don't have one yet."""
    created = 0
    today = now_date()

    for ag in agents:
        spec_path = AGENTS_DOCS / f"{ag['slug']}.md"
        if spec_path.exists():
            continue  # Already has a spec — don't overwrite

        agent_name = snake_to_readable(ag["slug"])
        content = f"""# {agent_name}
**Slug**: `{ag['slug']}`
**File**: `{ag['file']}`
**Lifecycle**: {ag['lifecycle']} (update after DB check)
**Auto-generated**: {today} | **Last verified**: —

## Purpose
> TODO: Describe what problem this agent solves, for whom, in what context.

## Inputs
- [ ] Data sources it reads
- [ ] Required parameters
- [ ] Optional configuration

## Outputs
```json
{{
  "agent": "{ag['slug']}",
  "run_at": "ISO timestamp",
  "dry_run": true,
  "summary": {{}},
  "recommendations": []
}}
```

## Behavior
> TODO: Step-by-step what the agent does (maps to run theater steps in dashboard)

## HITL Decision Points
> TODO: What requires human approval vs. auto-executes

## Limitations
> TODO: Known gaps, edge cases, things it doesn't handle

## Example Run
```bash
python3 {ag['file']}{"  --dry-run" if ag['has_dry_run'] else ""}
```
> TODO: Paste example output here
"""
        spec_path.write_text(content, encoding="utf-8")
        created += 1

    print(f"  Created {created} agent spec stubs in docs/agents/")
    return created


# ══════════════════════════════════════════════════════════════════════════════
# SECTION H — Write docs/api/reference.html
# ══════════════════════════════════════════════════════════════════════════════
ROUTE_DESCRIPTIONS = {
    "health":                    "Returns server health status and uptime",
    "db_stats":                  "Returns live platform statistics from SQLite DB",
    "get_agents":                "Lists all registered agents with status and metadata",
    "get_agent":                 "Returns detail for a single agent by slug",
    "portfolio":                 "Returns full portfolio view for enterprise dashboard",
    "run_agent":                 "Triggers a dry-run or live run of an agent",
    "get_runs":                  "Returns run history for an agent",
    "get_approvals":             "Lists pending HITL approval items",
    "decide_approval":           "Submit approve/reject decision for an approval item",
    "approval_history":          "Returns completed approval decision history",
    "get_recommendations":       "Returns agent recommendations for a specific run",
    "decide_recommendation":     "Submit decision on a specific recommendation",
    "pending_recommendations":   "Lists all pending (undecided) recommendations",
    "get_inventory":             "Returns live inventory data for CG SKUs",
    "advance_lifecycle":         "Advance an agent blueprint to the next lifecycle stage",
    "enrich_contact":            "Enrich a contact record with AI-generated intelligence",
    "get_contacts":              "Returns CRM contact list",
}

def infer_description(func: str, path: str) -> str:
    """Infer a human-readable description from function name or path."""
    if func in ROUTE_DESCRIPTIONS:
        return ROUTE_DESCRIPTIONS[func]
    # Fall back to path-based inference
    readable = path.replace("/api/", "").replace("/", " › ").replace("-", " ").replace("_", " ")
    return readable.strip().capitalize() or snake_to_readable(func)


def section_h_api_reference(routes: list[dict], ts: str) -> None:
    """Write docs/api/reference.html — the auto-generated API reference."""
    api_routes = [r for r in routes if r["is_api"]]

    METHOD_COLORS = {
        "GET":    ("#1e3a5f", "#60a5fa"),
        "POST":   ("#1a3a2e", "#34d399"),
        "PUT":    ("#2d1b4e", "#a855f7"),
        "DELETE": ("#3a1a1a", "#ef4444"),
    }

    def method_badge(method: str) -> str:
        bg, fg = METHOD_COLORS.get(method, ("#1e293b", "#94a3b8"))
        return (f'<span style="background:{bg};color:{fg};padding:2px 7px;'
                f'border-radius:3px;font-size:11px;font-weight:700;'
                f'letter-spacing:.04em;font-family:JetBrains Mono,monospace">{method}</span>')

    rows_html = ""
    for r in api_routes:
        methods_html = " ".join(method_badge(m) for m in r["methods"])
        desc = infer_description(r["function"], r["path"])
        rows_html += f"""
          <tr>
            <td>{methods_html}</td>
            <td><code style="color:#f1f5f9;font-family:JetBrains Mono,monospace;font-size:12px">{r['path']}</code></td>
            <td style="color:#64748b;font-family:JetBrains Mono,monospace;font-size:12px">{r['function']}</td>
            <td style="color:#94a3b8">{desc}</td>
            <td style="text-align:center;color:#475569">—</td>
          </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>API Reference — Business Agents Platform</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #0f1117; --card: #161b2e; --border: #1e293b;
      --text: #f1f5f9; --muted: #64748b; --accent: #f97316;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: var(--bg); color: var(--text); font-family: Inter, sans-serif;
             font-size: 15px; line-height: 1.65; padding: 48px 56px; }}
    h1 {{ font-size: 28px; font-weight: 700; margin-bottom: 6px; }}
    .sub {{ color: var(--muted); font-size: 14px; margin-bottom: 32px; }}
    .header-banner {{
      background: var(--card); border: 1px solid var(--border); border-radius: 8px;
      padding: 20px 24px; margin-bottom: 32px;
      display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;
    }}
    .header-banner .meta {{ font-size: 13px; color: var(--muted); }}
    .header-banner .meta strong {{ color: var(--accent); }}
    .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 8px;
              overflow: hidden; margin-bottom: 32px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    thead tr {{ background: rgba(249,115,22,0.1); border-bottom: 1px solid var(--border); }}
    thead th {{ padding: 10px 14px; text-align: left; font-weight: 600; color: var(--accent);
                font-size: 11px; letter-spacing: .05em; text-transform: uppercase; }}
    tbody tr {{ border-bottom: 1px solid var(--border); transition: background .1s; }}
    tbody tr:hover {{ background: rgba(255,255,255,.02); }}
    tbody tr:last-child {{ border-bottom: none; }}
    tbody td {{ padding: 10px 14px; vertical-align: middle; }}
    pre {{
      background: #0a0d14; border: 1px solid var(--border); border-radius: 6px;
      padding: 20px 22px; overflow-x: auto; font-family: JetBrains Mono, monospace;
      font-size: 13px; line-height: 1.7; color: #94a3b8; margin-bottom: 20px;
    }}
    .section-label {{ font-size: 11px; font-weight: 700; letter-spacing: .1em;
                       text-transform: uppercase; color: var(--accent); margin-bottom: 8px; }}
    h2 {{ font-size: 20px; font-weight: 700; margin-bottom: 16px; margin-top: 48px; }}
    .back-link {{ display: inline-block; margin-bottom: 24px; color: var(--muted);
                  font-size: 13px; text-decoration: none; }}
    .back-link:hover {{ color: var(--text); }}
    footer {{ margin-top: 48px; padding-top: 20px; border-top: 1px solid var(--border);
               font-size: 12px; color: var(--muted); }}
  </style>
</head>
<body>
  <a class="back-link" href="../index.html">&#8592; Docs Hub</a>

  <h1>API Reference</h1>
  <p class="sub">All endpoints exposed by the Flask server at <code>http://localhost:8500</code></p>

  <div class="header-banner">
    <div class="meta">
      Auto-generated by <code>docs/generate.py</code> on <strong>{ts}</strong>
      &nbsp;&middot;&nbsp; <strong>{len(api_routes)}</strong> API endpoints discovered
    </div>
  </div>

  <div class="card">
    <table>
      <thead>
        <tr>
          <th>Method</th>
          <th>Path</th>
          <th>Function</th>
          <th>Description</th>
          <th style="text-align:center">Auth</th>
        </tr>
      </thead>
      <tbody>{rows_html}
      </tbody>
    </table>
  </div>

  <div class="section-label">Code Sample</div>
  <h2>Calling the API</h2>
  <p style="color:#94a3b8;margin-bottom:16px">The server runs locally at port 8500. All endpoints return JSON. No auth required for prototype builds.</p>

  <pre><span style="color:#64748b">// JavaScript — fetch platform stats</span>
<span style="color:#f97316">const</span> response = <span style="color:#f97316">await</span> fetch(<span style="color:#86efac">'http://localhost:8500/api/db-stats'</span>);
<span style="color:#f97316">const</span> data = <span style="color:#f97316">await</span> response.json();
console.log(data.industries, data.blueprints);</pre>

  <pre><span style="color:#64748b">// JavaScript — trigger an agent dry-run</span>
<span style="color:#f97316">const</span> res = <span style="color:#f97316">await</span> fetch(<span style="color:#86efac">'http://localhost:8500/api/run/cg-replenishment-pr-agent'</span>, {{
  method: <span style="color:#86efac">'POST'</span>,
  headers: {{ <span style="color:#86efac">'Content-Type'</span>: <span style="color:#86efac">'application/json'</span> }},
  body: JSON.stringify({{ dry_run: <span style="color:#60a5fa">true</span> }})
}});
<span style="color:#f97316">const</span> result = <span style="color:#f97316">await</span> res.json();</pre>

  <pre><span style="color:#64748b"># Python — fetch pending approvals</span>
<span style="color:#f97316">import</span> requests
resp = requests.get(<span style="color:#86efac">"http://localhost:8500/api/approvals"</span>)
approvals = resp.json()
<span style="color:#f97316">for</span> item <span style="color:#f97316">in</span> approvals:
    print(item[<span style="color:#86efac">"item_id"</span>], item[<span style="color:#86efac">"decision"</span>])</pre>

  <footer>
    Auto-generated by docs/generate.py &middot; {ts} &middot;
    Source: <code>dashboards/server.py</code> route scan
  </footer>
</body>
</html>
"""
    out = API_DOCS / "reference.html"
    out.write_text(html, encoding="utf-8")
    print(f"  Wrote {out.relative_to(WORKSPACE)}")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION I — Write/Update docs/index.html
# ══════════════════════════════════════════════════════════════════════════════
def section_i_docs_index(status: dict, ts: str) -> None:
    """Create or update docs/index.html — the documentation navigation hub."""
    ps = status["platform_stats"]
    coverage_pct = int(status["overall_coverage"] * 100)

    def status_badge(exists: bool, auto: bool) -> str:
        if exists and auto:
            return '<span style="background:#1a3a2e;color:#22c55e;padding:2px 8px;border-radius:3px;font-size:11px;font-weight:600">AUTO</span>'
        if exists:
            return '<span style="background:#1e3a5f;color:#60a5fa;padding:2px 8px;border-radius:3px;font-size:11px;font-weight:600">MANUAL</span>'
        return '<span style="background:#3a1a1a;color:#ef4444;padding:2px 8px;border-radius:3px;font-size:11px;font-weight:600">MISSING</span>'

    # Build section rows from status
    section_rows = ""
    for s in status["sections"]:
        sid = s["id"]
        fname = s["file"].replace("docs/", "")
        fpath = DOCS_DIR / fname
        exists = s["exists"]
        auto = s.get("auto_generated", False)
        cov = int(s.get("coverage", 0) * 100)
        generated = s.get("last_generated") or "—"
        if isinstance(generated, str) and "T" in generated:
            generated = generated.split("T")[0]
        notes = s.get("notes", "")

        if exists:
            link_html = f'<a href="{fname}" style="color:#f97316;text-decoration:none">{sid}</a>'
        else:
            link_html = f'<span style="color:#475569">{sid}</span>'

        section_rows += f"""
          <tr>
            <td>{link_html}</td>
            <td style="color:#64748b;font-size:12px">{fname}</td>
            <td style="text-align:center">{cov}%</td>
            <td style="color:#64748b">{generated}</td>
            <td>{status_badge(exists, auto)}</td>
            <td style="color:#475569;font-size:12px">{notes}</td>
          </tr>"""

    # Missing sections
    for ms in status.get("missing_sections", []):
        section_rows += f"""
          <tr>
            <td style="color:#475569">{ms}</td>
            <td style="color:#475569;font-size:12px">{ms}</td>
            <td style="text-align:center">0%</td>
            <td style="color:#64748b">—</td>
            <td><span style="background:#3a1a1a;color:#ef4444;padding:2px 8px;border-radius:3px;font-size:11px;font-weight:600">MISSING</span></td>
            <td style="color:#475569;font-size:12px">To be written</td>
          </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Documentation Hub — Business Agents Platform</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #0f1117; --card: #161b2e; --border: #1e293b;
      --text: #f1f5f9; --muted: #64748b; --accent: #f97316;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: var(--bg); color: var(--text); font-family: Inter, sans-serif;
             font-size: 15px; line-height: 1.65; padding: 48px 56px; max-width: 1100px; }}
    h1 {{ font-size: 32px; font-weight: 700; margin-bottom: 6px; }}
    .sub {{ color: var(--muted); font-size: 14px; margin-bottom: 40px; }}
    .badge {{ display: inline-block; background: rgba(249,115,22,.15); color: var(--accent);
               font-size: 11px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase;
               padding: 4px 10px; border-radius: 4px; margin-bottom: 12px; }}
    .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(130px,1fr));
               gap: 12px; margin-bottom: 40px; }}
    .stat {{ background: var(--card); border: 1px solid var(--border); border-radius: 8px;
              padding: 16px; text-align: center; }}
    .stat-value {{ font-size: 26px; font-weight: 700; color: var(--accent); line-height: 1; }}
    .stat-label {{ font-size: 11px; color: var(--muted); margin-top: 4px;
                   text-transform: uppercase; letter-spacing: .05em; }}
    .section-label {{ font-size: 11px; font-weight: 700; letter-spacing: .1em;
                       text-transform: uppercase; color: var(--accent); margin-bottom: 8px; }}
    h2 {{ font-size: 20px; font-weight: 700; margin-bottom: 16px; }}
    .doc-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px,1fr));
                  gap: 16px; margin-bottom: 40px; }}
    .doc-card {{ background: var(--card); border: 1px solid var(--border); border-radius: 8px;
                  padding: 20px; text-decoration: none; color: inherit;
                  transition: border-color .15s; display: block; }}
    .doc-card:hover {{ border-color: var(--accent); }}
    .doc-card .title {{ font-size: 14px; font-weight: 600; color: var(--text); margin-bottom: 6px; }}
    .doc-card .desc {{ font-size: 13px; color: var(--muted); margin-bottom: 12px; }}
    .doc-card .tag {{ font-size: 11px; padding: 2px 6px; border-radius: 3px;
                       font-weight: 600; text-transform: uppercase; letter-spacing: .04em; }}
    .tag-auto {{ background: #1a3a2e; color: #22c55e; }}
    .tag-manual {{ background: #1e3a5f; color: #60a5fa; }}
    .tag-missing {{ background: #3a1a1a; color: #ef4444; }}
    .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 8px;
              overflow: hidden; margin-bottom: 32px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    thead tr {{ background: rgba(249,115,22,0.1); border-bottom: 1px solid var(--border); }}
    thead th {{ padding: 10px 14px; text-align: left; font-weight: 600; color: var(--accent);
                font-size: 11px; letter-spacing: .05em; text-transform: uppercase; }}
    tbody tr {{ border-bottom: 1px solid var(--border); transition: background .1s; }}
    tbody tr:hover {{ background: rgba(255,255,255,.02); }}
    tbody tr:last-child {{ border-bottom: none; }}
    tbody td {{ padding: 10px 14px; color: #94a3b8; vertical-align: middle; }}
    .progress-bar-wrap {{ background: #1e293b; border-radius: 4px; height: 6px; width: 100%; margin-top: 16px; }}
    .progress-bar {{ background: var(--accent); border-radius: 4px; height: 6px; }}
    footer {{ margin-top: 48px; padding-top: 20px; border-top: 1px solid var(--border);
               font-size: 12px; color: var(--muted); }}
  </style>
</head>
<body>
  <div class="badge">Documentation Hub</div>
  <h1>Business Agents Platform</h1>
  <p class="sub">Technical documentation, agent catalog, and API reference. Generated from live codebase.</p>

  <div class="stats">
    <div class="stat"><div class="stat-value">{ps['industries']}</div><div class="stat-label">Industries</div></div>
    <div class="stat"><div class="stat-value">{ps['processes']}</div><div class="stat-label">Processes</div></div>
    <div class="stat"><div class="stat-value">{ps['blueprints']}</div><div class="stat-label">Blueprints</div></div>
    <div class="stat"><div class="stat-value">{ps['agent_actions']}</div><div class="stat-label">Agent Actions</div></div>
    <div class="stat"><div class="stat-value">{ps['agents_discovered']}</div><div class="stat-label">Agents</div></div>
    <div class="stat"><div class="stat-value">{ps['api_endpoints']}</div><div class="stat-label">API Endpoints</div></div>
    <div class="stat"><div class="stat-value">{ps['frameworks']}</div><div class="stat-label">Frameworks</div></div>
    <div class="stat"><div class="stat-value">{coverage_pct}%</div><div class="stat-label">Doc Coverage</div></div>
  </div>

  <div class="section-label">Documentation Sections</div>
  <h2>Available Docs</h2>

  <div class="doc-grid">
    <a class="doc-card" href="architecture.html">
      <div class="title">Architecture Reference</div>
      <div class="desc">System architecture, DB schema, data flow diagrams, and platform overview.</div>
      <span class="tag tag-manual">Manual</span>
    </a>
    <a class="doc-card" href="agents/index.html">
      <div class="title">Agent Catalog</div>
      <div class="desc">All discovered pilot agents with lifecycle status, capabilities, and spec links.</div>
      <span class="tag tag-auto">Auto-generated</span>
    </a>
    <a class="doc-card" href="api/reference.html">
      <div class="title">API Reference</div>
      <div class="desc">All Flask server endpoints with methods, paths, and code samples.</div>
      <span class="tag tag-auto">Auto-generated</span>
    </a>
    <div class="doc-card" style="opacity:0.5;cursor:default">
      <div class="title">Developer Guide</div>
      <div class="desc">How to add agents, seed data, run locally, and extend the platform.</div>
      <span class="tag tag-missing">Missing</span>
    </div>
    <div class="doc-card" style="opacity:0.5;cursor:default">
      <div class="title">Client Guide: Kimre</div>
      <div class="desc">Kimre-specific portal walkthrough, agent run theater, and approval workflow.</div>
      <span class="tag tag-missing">Missing</span>
    </div>
    <a class="doc-card" href="status.json">
      <div class="title">status.json</div>
      <div class="desc">Machine-readable documentation coverage report. Refresh with generate.py.</div>
      <span class="tag tag-auto">Auto-generated</span>
    </a>
  </div>

  <div class="section-label">Coverage Status</div>
  <h2>Documentation Coverage</h2>
  <p style="color:#94a3b8;margin-bottom:8px">Overall documentation coverage: <strong style="color:var(--accent)">{coverage_pct}%</strong></p>
  <div class="progress-bar-wrap"><div class="progress-bar" style="width:{coverage_pct}%"></div></div>

  <div class="card" style="margin-top:24px">
    <table>
      <thead>
        <tr>
          <th>Section</th>
          <th>File</th>
          <th style="text-align:center">Coverage</th>
          <th>Last Updated</th>
          <th>Status</th>
          <th>Notes</th>
        </tr>
      </thead>
      <tbody>{section_rows}
      </tbody>
    </table>
  </div>

  <div class="section-label">Refresh Docs</div>
  <h2>Regenerate Documentation</h2>
  <p style="color:#94a3b8;margin-bottom:16px">Run these commands from the workspace root to regenerate auto-generated docs:</p>
  <pre style="background:#0a0d14;border:1px solid var(--border);border-radius:6px;padding:20px 22px;font-family:JetBrains Mono,monospace;font-size:13px;color:#94a3b8;line-height:1.7;margin-bottom:0"><span style="color:#64748b"># Full regeneration</span>
python3 docs/generate.py

<span style="color:#64748b"># Just the agent catalog</span>
python3 docs/generate.py --agents-only

<span style="color:#64748b"># Just update status.json</span>
python3 docs/generate.py --status</pre>

  <footer>
    Auto-generated by docs/generate.py &middot; {ts} &middot;
    Business Agents Platform Documentation Hub
  </footer>
</body>
</html>
"""
    out = DOCS_DIR / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"  Wrote {out.relative_to(WORKSPACE)}")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(description="Business Agents Platform — Documentation Generator")
    parser.add_argument("--agents-only", action="store_true", help="Only regenerate agents/index.html and stub .md files")
    parser.add_argument("--status", action="store_true", help="Only update status.json (no HTML output)")
    args = parser.parse_args()

    print("Business Agents Platform — Documentation Generator")
    print(f"Workspace: {WORKSPACE}")
    print(f"Timestamp: {now_iso()}")
    print()

    # Always run A and B — needed for all modes
    print("[A] Querying DB stats...")
    db_stats = section_a_db_stats()
    print(f"    {db_stats['industries']} industries, {db_stats['processes']} processes, "
          f"{db_stats['blueprints']} blueprints, {db_stats['agent_actions']} actions")

    print("[B] Discovering agents...")
    agents = section_b_agent_discovery()
    # Enrich agent lifecycle from DB
    lc_map = db_stats.get("_blueprint_lifecycle_by_slug", {})
    for ag in agents:
        ag["lifecycle"] = lc_map.get(ag["slug"], "unknown")
    print(f"    {len(agents)} agents found")

    if args.status:
        print("[C] Discovering API routes (for status.json)...")
        routes = section_c_api_routes()
        print(f"    {len([r for r in routes if r['is_api']])} API routes found")

        print("[D] Parsing frameworks...")
        framework_count, _ = section_d_frameworks()
        print(f"    {framework_count} frameworks found")

        print("[E] Writing docs/status.json...")
        status = section_e_write_status(db_stats, agents, routes, framework_count)
        print()
        print("=== STATUS SUMMARY ===")
        print(json.dumps({
            "platform_stats": status["platform_stats"],
            "overall_coverage": status["overall_coverage"],
            "blueprint_lifecycle": status["blueprint_lifecycle"],
            "missing_sections": status["missing_sections"],
        }, indent=2))
        return

    if args.agents_only:
        ts = now_iso()
        print("[F] Writing docs/agents/index.html...")
        section_f_agents_index(agents, ts)
        print("[G] Writing agent spec stubs...")
        section_g_agent_stubs(agents)
        print()
        print("Done. Agent catalog updated.")
        return

    # Full run
    print("[C] Discovering API routes...")
    routes = section_c_api_routes()
    print(f"    {len([r for r in routes if r['is_api']])} API routes found")

    print("[D] Parsing frameworks...")
    framework_count, _ = section_d_frameworks()
    print(f"    {framework_count} frameworks found")

    ts = now_iso()

    print("[E] Writing docs/status.json...")
    status = section_e_write_status(db_stats, agents, routes, framework_count)

    print("[F] Writing docs/agents/index.html...")
    section_f_agents_index(agents, ts)

    print("[G] Writing agent spec stubs...")
    section_g_agent_stubs(agents)

    print("[H] Writing docs/api/reference.html...")
    section_h_api_reference(routes, ts)

    print("[I] Writing docs/index.html...")
    section_i_docs_index(status, ts)

    print()
    print("=== COMPLETE ===")
    print(f"  {len(agents)} agents cataloged")
    print(f"  {len([r for r in routes if r['is_api']])} API endpoints documented")
    print(f"  {framework_count} frameworks counted")
    print(f"  Overall doc coverage: {int(status['overall_coverage']*100)}%")
    print(f"  Missing sections: {status['missing_sections']}")


if __name__ == "__main__":
    main()
