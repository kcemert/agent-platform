#!/usr/bin/env python3
"""
Client Engagement Portal Generator — Epic 10
Reads business_agents.db and produces client-portal/index.html
with all data embedded as inline JSON.

Usage:
    python3 client-portal/generate.py
"""

import sqlite3
import json
import os
import sys
from datetime import datetime

# ── Paths ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR   = os.path.dirname(SCRIPT_DIR)
DB_PATH    = os.path.join(ROOT_DIR, "business-agents", "business_agents.db")
OUT_PATH   = os.path.join(SCRIPT_DIR, "index.html")


def dict_row(conn):
    conn.row_factory = sqlite3.Row
    return conn


def fetch_data(db_path: str) -> dict:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    # Functions
    cur.execute("SELECT id, apqc_code, name, type FROM functions ORDER BY id")
    functions = [dict(r) for r in cur.fetchall()]

    # Processes (all 127)
    cur.execute("""
        SELECT id, apqc_code, name, level, function_id, parent_id,
               description, is_universal
        FROM processes
        ORDER BY function_id, apqc_code
    """)
    processes = [dict(r) for r in cur.fetchall()]

    # Industries
    cur.execute("SELECT id, code, name, sector FROM industries ORDER BY id")
    industries = [dict(r) for r in cur.fetchall()]

    # Industry ↔ Process mappings
    cur.execute("""
        SELECT industry_id, process_id, relevance
        FROM industry_processes
    """)
    industry_processes = [dict(r) for r in cur.fetchall()]

    # Build per-process industry map  {process_id: [{industry_id, relevance}]}
    proc_industries: dict[int, list] = {}
    for row in industry_processes:
        pid = row["process_id"]
        proc_industries.setdefault(pid, []).append({
            "industry_id": row["industry_id"],
            "relevance": row["relevance"],
        })

    # Agent capabilities
    cur.execute("""
        SELECT ac.id, ac.process_id, ac.function_id, ac.capability_type_id,
               ac.industry_id, ac.name, ac.authority_level,
               ac.feasibility, ac.value, ac.readiness,
               ct.name AS capability_type_name, ct.slug AS capability_type_slug
        FROM agent_capabilities ac
        LEFT JOIN capability_types ct ON ct.id = ac.capability_type_id
        ORDER BY ac.value DESC, ac.feasibility DESC
    """)
    capabilities = [dict(r) for r in cur.fetchall()]

    # Capability types
    cur.execute("SELECT id, slug, name, description FROM capability_types ORDER BY sort_order")
    capability_types = [dict(r) for r in cur.fetchall()]

    # Agent blueprints
    cur.execute("""
        SELECT id, slug, title, version, status, trigger_type,
               authority_level, authority_scope, business_value,
               estimated_time_saved_hrs_week, kpis, data_inputs, data_outputs,
               decision_logic, escalation_triggers, notes, created_at
        FROM agent_blueprints
        ORDER BY id
    """)
    raw_blueprints = [dict(r) for r in cur.fetchall()]

    # Parse JSON fields in blueprints
    blueprints = []
    for b in raw_blueprints:
        for field in ("kpis", "data_inputs", "data_outputs"):
            if b[field]:
                try:
                    b[field] = json.loads(b[field])
                except (json.JSONDecodeError, TypeError):
                    pass
        blueprints.append(b)

    # Build opportunity score per process:
    # score = max(value) of capabilities mapped to that process
    proc_scores: dict[int, int] = {}
    for cap in capabilities:
        pid = cap["process_id"]
        if pid is not None:
            current = proc_scores.get(pid, 0)
            proc_scores[pid] = max(current, cap["value"] or 0)

    # Attach computed fields to processes
    for p in processes:
        p["opportunity_score"]  = proc_scores.get(p["id"], 0)
        p["industries"]         = proc_industries.get(p["id"], [])

    # Count industries covered — use total industries in the platform
    industries_covered = len(industries)

    # Build per-blueprint system list from data_inputs/data_outputs
    for b in blueprints:
        systems = set()
        for field in ("data_inputs", "data_outputs"):
            val = b.get(field)
            if isinstance(val, list):
                for item in val:
                    if isinstance(item, dict) and item.get("system"):
                        systems.add(item["system"])
        b["systems"] = sorted(systems)

    con.close()

    return {
        "meta": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "process_count": len(processes),
            "blueprint_count": len(blueprints),
            "industries_covered": industries_covered,
        },
        "functions": functions,
        "processes": processes,
        "industries": industries,
        "capabilities": capabilities,
        "capability_types": capability_types,
        "blueprints": blueprints,
    }


def build_html(data: dict) -> str:
    data_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))

    # Function colour palette (12 functions → 12 distinct hues)
    # Mapped by function id 1-12
    FUNC_COLORS = {
        1:  "#6366f1",  # indigo  — Vision & Strategy
        2:  "#8b5cf6",  # violet  — Products & Services
        3:  "#06b6d4",  # cyan    — Market & Sell
        4:  "#22c55e",  # green   — Deliver Physical
        5:  "#84cc16",  # lime    — Deliver Services
        6:  "#f97316",  # orange  — Customer Service
        7:  "#f43f5e",  # rose    — Human Capital
        8:  "#3b82f6",  # blue    — Information Technology
        9:  "#eab308",  # yellow  — Financial Resources
        10: "#14b8a6",  # teal    — Assets
        11: "#a855f7",  # purple  — Risk & Compliance
        12: "#fb923c",  # light-orange — External Relationships
    }

    func_colors_js = json.dumps(FUNC_COLORS)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Business Agents Platform — Client Portal</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet" />
<style>
/* ── Reset & Base ──────────────────────────────────────────────────────── */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

:root {{
  --bg:        #0f1117;
  --card:      #161b2e;
  --border:    #1e293b;
  --text:      #f1f5f9;
  --secondary: #94a3b8;
  --muted:     #64748b;
  --indigo:    #6366f1;
  --cyan:      #06b6d4;
  --orange:    #f97316;
  --green:     #22c55e;
  --yellow:    #eab308;
  --red:       #ef4444;
  --rose:      #f43f5e;
  --radius:    12px;
  --radius-sm: 6px;
}}

html {{ scroll-behavior: smooth; }}
body {{
  font-family: 'Inter', system-ui, sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  font-size: 14px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}}

/* ── Utility ───────────────────────────────────────────────────────────── */
.sr-only {{ position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0,0,0,0); }}
.flex {{ display: flex; }}
.flex-col {{ flex-direction: column; }}
.items-center {{ align-items: center; }}
.gap-2 {{ gap: 8px; }}
.gap-3 {{ gap: 12px; }}
.gap-4 {{ gap: 16px; }}
.gap-6 {{ gap: 24px; }}
.grow {{ flex: 1; }}
.hidden {{ display: none !important; }}
.truncate {{ overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.relative {{ position: relative; }}
.cursor-pointer {{ cursor: pointer; }}

/* ── Header ────────────────────────────────────────────────────────────── */
#header {{
  background: rgba(15,17,23,0.92);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 100;
  padding: 14px 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}}

.logo-mark {{
  width: 36px; height: 36px;
  background: linear-gradient(135deg, var(--indigo), var(--cyan));
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-weight: 800; font-size: 15px; color: white; flex-shrink: 0;
}}

.header-title {{
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.02em;
}}

.header-sub {{
  font-size: 12px;
  color: var(--muted);
  margin-top: 1px;
}}

.header-badge {{
  background: linear-gradient(135deg, rgba(99,102,241,0.18), rgba(6,182,212,0.14));
  border: 1px solid rgba(99,102,241,0.3);
  border-radius: 20px;
  padding: 6px 16px;
  font-size: 12px;
  font-weight: 600;
  color: #a5b4fc;
  white-space: nowrap;
}}

.header-date {{
  font-size: 12px;
  color: var(--muted);
  white-space: nowrap;
}}

/* ── Tab Nav ───────────────────────────────────────────────────────────── */
#tab-nav {{
  background: rgba(15,17,23,0.95);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 65px;
  z-index: 90;
  padding: 0 32px;
  display: flex;
  gap: 4px;
}}

.tab-btn {{
  padding: 14px 20px;
  font-size: 13px;
  font-weight: 500;
  color: var(--muted);
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s;
  white-space: nowrap;
}}

.tab-btn:hover {{ color: var(--secondary); }}
.tab-btn.active {{
  color: var(--indigo);
  border-bottom-color: var(--indigo);
}}

/* ── Main Content ──────────────────────────────────────────────────────── */
#main {{ padding: 40px 32px; max-width: 1280px; margin: 0 auto; }}
.tab-panel {{ display: none; }}
.tab-panel.active {{ display: block; }}

/* ── Cards ─────────────────────────────────────────────────────────────── */
.card {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px;
}}

.card-sm {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px 20px;
}}

/* ── Stat Cards (Overview) ─────────────────────────────────────────────── */
.stats-row {{
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 32px;
}}

.stat-card {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 28px 24px;
  text-align: center;
  position: relative;
  overflow: hidden;
}}

.stat-card::before {{
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
}}
.stat-card:nth-child(1)::before {{ background: linear-gradient(90deg, var(--indigo), var(--cyan)); }}
.stat-card:nth-child(2)::before {{ background: linear-gradient(90deg, var(--cyan), var(--green)); }}
.stat-card:nth-child(3)::before {{ background: linear-gradient(90deg, var(--green), var(--orange)); }}

.stat-number {{
  font-size: 42px;
  font-weight: 800;
  color: var(--text);
  letter-spacing: -0.03em;
  line-height: 1;
  margin-bottom: 8px;
}}

.stat-number span {{ color: var(--indigo); }}
.stat-label {{
  font-size: 13px;
  color: var(--secondary);
  font-weight: 500;
}}
.stat-sub {{
  font-size: 11px;
  color: var(--muted);
  margin-top: 4px;
}}

/* ── Section Titles ────────────────────────────────────────────────────── */
.section-title {{
  font-size: 18px;
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.02em;
  margin-bottom: 4px;
}}
.section-sub {{
  font-size: 13px;
  color: var(--muted);
  margin-bottom: 24px;
}}

/* ── Feature Grid ──────────────────────────────────────────────────────── */
.feature-grid {{
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 40px;
}}

.feature-card {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px;
}}

.feature-icon {{
  width: 44px; height: 44px;
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 20px;
  margin-bottom: 16px;
}}

.fi-indigo {{ background: rgba(99,102,241,0.15); }}
.fi-cyan   {{ background: rgba(6,182,212,0.15); }}
.fi-green  {{ background: rgba(34,197,94,0.15); }}

.feature-title {{
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 8px;
}}
.feature-desc {{
  font-size: 13px;
  color: var(--secondary);
  line-height: 1.6;
}}

/* ── How It Works ──────────────────────────────────────────────────────── */
.how-steps {{
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0;
  position: relative;
  margin-bottom: 40px;
}}

.how-steps::before {{
  content: '';
  position: absolute;
  top: 32px; left: 12.5%; right: 12.5%;
  height: 1px;
  background: linear-gradient(90deg, var(--indigo), var(--cyan), var(--green), var(--orange));
  z-index: 0;
}}

.step-card {{
  display: flex; flex-direction: column; align-items: center;
  text-align: center;
  padding: 0 16px 24px;
  position: relative; z-index: 1;
}}

.step-num {{
  width: 64px; height: 64px;
  border-radius: 50%;
  background: var(--card);
  border: 2px solid var(--border);
  display: flex; align-items: center; justify-content: center;
  font-size: 26px;
  margin-bottom: 16px;
  position: relative;
}}

.step-card:nth-child(1) .step-num {{ border-color: var(--indigo); box-shadow: 0 0 0 4px rgba(99,102,241,0.1); }}
.step-card:nth-child(2) .step-num {{ border-color: var(--cyan); box-shadow: 0 0 0 4px rgba(6,182,212,0.1); }}
.step-card:nth-child(3) .step-num {{ border-color: var(--green); box-shadow: 0 0 0 4px rgba(34,197,94,0.1); }}
.step-card:nth-child(4) .step-num {{ border-color: var(--orange); box-shadow: 0 0 0 4px rgba(249,115,22,0.1); }}

.step-title {{ font-size: 13px; font-weight: 600; color: var(--text); margin-bottom: 6px; }}
.step-desc  {{ font-size: 12px; color: var(--secondary); line-height: 1.5; }}

/* ── Pilot Results ─────────────────────────────────────────────────────── */
.pilot-row {{
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 40px;
}}

.pilot-card {{
  background: linear-gradient(135deg, rgba(99,102,241,0.08), rgba(6,182,212,0.05));
  border: 1px solid rgba(99,102,241,0.2);
  border-radius: var(--radius);
  padding: 20px 24px;
  display: flex;
  align-items: center;
  gap: 16px;
}}

.pilot-icon {{
  font-size: 28px;
  flex-shrink: 0;
}}

.pilot-value {{
  font-size: 22px;
  font-weight: 800;
  color: var(--text);
  letter-spacing: -0.02em;
}}

.pilot-label {{
  font-size: 12px;
  color: var(--secondary);
  margin-top: 2px;
}}

/* ── Process Explorer ──────────────────────────────────────────────────── */
#process-explorer {{
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 24px;
  align-items: start;
}}

.process-sidebar {{
  position: sticky;
  top: 140px;
}}

.search-box {{
  width: 100%;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text);
  padding: 10px 14px;
  font-size: 13px;
  font-family: inherit;
  margin-bottom: 16px;
  transition: border-color 0.15s;
}}
.search-box:focus {{
  outline: none;
  border-color: var(--indigo);
}}
.search-box::placeholder {{ color: var(--muted); }}

.sidebar-title {{
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
  margin-bottom: 10px;
}}

.func-pill {{
  display: block;
  width: 100%;
  text-align: left;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  border: 1px solid transparent;
  background: none;
  color: var(--secondary);
  font-size: 12px;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.15s;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}}

.func-pill:hover {{ background: rgba(255,255,255,0.04); color: var(--text); }}
.func-pill.active {{
  background: rgba(99,102,241,0.12);
  border-color: rgba(99,102,241,0.3);
  color: var(--text);
}}

.func-dot {{
  width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
}}

.func-pill-count {{
  margin-left: auto;
  font-size: 10px;
  color: var(--muted);
  background: rgba(255,255,255,0.05);
  border-radius: 10px;
  padding: 1px 6px;
}}

/* ── Process Cards ─────────────────────────────────────────────────────── */
.process-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 14px;
}}

.proc-card {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px 18px;
  cursor: pointer;
  transition: border-color 0.15s, transform 0.15s;
}}

.proc-card:hover {{
  border-color: rgba(99,102,241,0.4);
  transform: translateY(-1px);
}}

.proc-card.expanded {{
  grid-column: 1 / -1;
  border-color: var(--indigo);
}}

.proc-func-badge {{
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  padding: 3px 8px;
  border-radius: 4px;
  margin-bottom: 10px;
  opacity: 0.9;
}}

.proc-name {{
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 4px;
  line-height: 1.4;
}}

.proc-code {{
  font-size: 11px;
  color: var(--muted);
  font-family: 'SF Mono', 'Fira Code', monospace;
  margin-bottom: 10px;
}}

.score-stars {{
  display: flex;
  gap: 2px;
}}

.star {{
  width: 12px; height: 12px;
  border-radius: 50%;
  background: var(--border);
}}

.star.filled {{ background: var(--orange); }}
.star.high   {{ background: var(--red); }}
.star.med    {{ background: var(--orange); }}
.star.low    {{ background: var(--green); }}

/* ── Expanded Process Detail ───────────────────────────────────────────── */
.proc-detail {{
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
  display: none;
}}

.proc-detail.open {{ display: block; }}

.detail-grid {{
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 16px;
}}

.detail-section-title {{
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--muted);
  margin-bottom: 8px;
}}

.industry-tag {{
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: rgba(255,255,255,0.05);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 3px 8px;
  font-size: 11px;
  color: var(--secondary);
  margin: 2px;
}}

.cap-chip {{
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: rgba(99,102,241,0.1);
  border: 1px solid rgba(99,102,241,0.2);
  border-radius: 4px;
  padding: 3px 8px;
  font-size: 11px;
  color: #a5b4fc;
  margin: 2px;
}}

/* ── Opportunities ─────────────────────────────────────────────────────── */
.opp-filters {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px 24px;
  margin-bottom: 24px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  align-items: end;
}}

.filter-group label {{
  display: block;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--muted);
  margin-bottom: 8px;
}}

.filter-pills {{
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}}

.filter-pill {{
  padding: 5px 12px;
  border-radius: 20px;
  border: 1px solid var(--border);
  background: none;
  color: var(--secondary);
  font-size: 12px;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.15s;
}}

.filter-pill:hover {{ border-color: var(--indigo); color: var(--text); }}
.filter-pill.active {{
  background: var(--indigo);
  border-color: var(--indigo);
  color: white;
}}

.filter-select {{
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text);
  padding: 8px 12px;
  font-size: 13px;
  font-family: inherit;
  width: 100%;
  cursor: pointer;
}}
.filter-select:focus {{ outline: none; border-color: var(--indigo); }}

.score-range {{
  display: flex;
  align-items: center;
  gap: 10px;
}}

.score-slider {{
  flex: 1;
  accent-color: var(--indigo);
  height: 4px;
  cursor: pointer;
}}

.score-val {{
  font-size: 13px;
  font-weight: 600;
  color: var(--indigo);
  width: 16px;
  text-align: center;
}}

.opp-actions {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}}

.opp-count {{
  font-size: 13px;
  color: var(--muted);
}}

.opp-count strong {{ color: var(--text); }}

.btn-export {{
  padding: 8px 20px;
  background: var(--indigo);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition: opacity 0.15s;
  display: flex; align-items: center; gap: 6px;
}}
.btn-export:hover {{ opacity: 0.85; }}

/* ── Opportunity Cards ─────────────────────────────────────────────────── */
.opp-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 14px;
}}

.opp-card {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 18px 20px;
  transition: border-color 0.15s;
}}

.opp-card:hover {{ border-color: rgba(99,102,241,0.35); }}

.opp-header {{
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 10px;
}}

.opp-name {{
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  line-height: 1.4;
}}

.opp-code {{
  font-size: 11px;
  color: var(--muted);
  font-family: monospace;
}}

.score-badge {{
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}}
.score-5 {{ background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.3); }}
.score-4 {{ background: rgba(249,115,22,0.15); color: #fdba74; border: 1px solid rgba(249,115,22,0.3); }}
.score-3 {{ background: rgba(234,179,8,0.15); color: #fde047; border: 1px solid rgba(234,179,8,0.3); }}
.score-2 {{ background: rgba(34,197,94,0.15); color: #86efac; border: 1px solid rgba(34,197,94,0.3); }}
.score-1 {{ background: rgba(100,116,139,0.15); color: var(--secondary); border: 1px solid var(--border); }}

.opp-meta {{
  font-size: 12px;
  color: var(--secondary);
  margin-bottom: 10px;
}}

.opp-tags {{
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 10px;
}}

.opp-ind-tag {{
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(255,255,255,0.05);
  color: var(--secondary);
  border: 1px solid var(--border);
}}

.blueprint-badge {{
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(34,197,94,0.12);
  color: #86efac;
  border: 1px solid rgba(34,197,94,0.25);
  display: flex; align-items: center; gap: 4px;
}}

/* ── Blueprints ─────────────────────────────────────────────────────────── */
.blueprint-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
}}

.bp-card {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px;
  transition: border-color 0.15s;
}}

.bp-card:hover {{ border-color: rgba(99,102,241,0.35); }}

.bp-header {{
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 14px;
}}

.bp-title {{
  font-size: 15px;
  font-weight: 700;
  color: var(--text);
  line-height: 1.3;
}}

.authority-badge {{
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  flex-shrink: 0;
}}

.auth-low    {{ background: rgba(34,197,94,0.15);  color: #86efac; border: 1px solid rgba(34,197,94,0.3); }}
.auth-medium {{ background: rgba(234,179,8,0.15);  color: #fde047; border: 1px solid rgba(234,179,8,0.3); }}
.auth-high   {{ background: rgba(239,68,68,0.15);  color: #fca5a5; border: 1px solid rgba(239,68,68,0.3); }}

.bp-business-value {{
  font-size: 13px;
  color: var(--secondary);
  line-height: 1.6;
  margin-bottom: 16px;
}}

.bp-metrics-row {{
  display: flex;
  gap: 20px;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: rgba(255,255,255,0.02);
  border-radius: 8px;
  border: 1px solid var(--border);
}}

.bp-metric {{
  text-align: center;
}}

.bp-metric-val {{
  font-size: 20px;
  font-weight: 800;
  color: var(--cyan);
  letter-spacing: -0.02em;
}}

.bp-metric-label {{
  font-size: 11px;
  color: var(--muted);
  margin-top: 2px;
}}

.bp-kpis {{
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 16px;
}}

.kpi-chip {{
  background: rgba(6,182,212,0.1);
  border: 1px solid rgba(6,182,212,0.2);
  border-radius: 4px;
  padding: 3px 10px;
  font-size: 11px;
  color: #67e8f9;
  font-family: 'SF Mono', 'Fira Code', monospace;
}}

.bp-systems {{
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 16px;
}}

.system-chip {{
  background: rgba(99,102,241,0.1);
  border: 1px solid rgba(99,102,241,0.2);
  border-radius: 4px;
  padding: 3px 10px;
  font-size: 11px;
  color: #a5b4fc;
  display: flex;
  align-items: center;
  gap: 4px;
}}

.trigger-row {{
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}}

.trigger-label {{
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--muted);
}}

.trigger-chip {{
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 4px;
  background: rgba(249,115,22,0.1);
  border: 1px solid rgba(249,115,22,0.2);
  color: #fdba74;
  font-weight: 500;
  text-transform: capitalize;
}}

.bp-expand-btn {{
  background: none;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--muted);
  font-size: 12px;
  font-family: inherit;
  padding: 7px 14px;
  cursor: pointer;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  justify-content: center;
  margin-top: 4px;
}}
.bp-expand-btn:hover {{ border-color: var(--indigo); color: var(--text); }}

.bp-io-detail {{
  margin-top: 16px;
  display: none;
}}
.bp-io-detail.open {{ display: block; }}

.io-section {{
  margin-bottom: 12px;
}}

.io-title {{
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--muted);
  margin-bottom: 8px;
}}

.io-item {{
  background: rgba(255,255,255,0.02);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 10px 14px;
  margin-bottom: 6px;
  font-size: 12px;
}}

.io-system {{
  font-weight: 600;
  color: var(--text);
}}
.io-endpoint {{
  color: var(--muted);
  font-family: monospace;
  font-size: 11px;
}}
.io-purpose {{
  color: var(--secondary);
  margin-top: 2px;
}}

/* ── Value Calculator ──────────────────────────────────────────────────── */
.calc-card {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 32px;
  max-width: 700px;
  margin: 0 auto;
}}

.calc-grid {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 24px;
}}

.calc-input-group label {{
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--secondary);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.07em;
}}

.calc-input {{
  width: 100%;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text);
  padding: 12px 16px;
  font-size: 16px;
  font-weight: 600;
  font-family: inherit;
  transition: border-color 0.15s;
}}
.calc-input:focus {{
  outline: none;
  border-color: var(--indigo);
}}

.calc-result {{
  background: linear-gradient(135deg, rgba(99,102,241,0.12), rgba(6,182,212,0.08));
  border: 1px solid rgba(99,102,241,0.25);
  border-radius: var(--radius);
  padding: 28px;
  text-align: center;
}}

.calc-result-label {{
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.09em;
  color: var(--muted);
  margin-bottom: 8px;
}}

.calc-result-value {{
  font-size: 48px;
  font-weight: 800;
  color: var(--text);
  letter-spacing: -0.03em;
  margin-bottom: 4px;
}}

.calc-result-sub {{
  font-size: 13px;
  color: var(--secondary);
}}

.calc-breakdown {{
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-top: 20px;
}}

.calc-br-item {{
  text-align: center;
  padding: 12px;
  background: rgba(255,255,255,0.03);
  border-radius: 8px;
  border: 1px solid var(--border);
}}

.calc-br-val {{
  font-size: 18px;
  font-weight: 700;
  color: var(--cyan);
}}

.calc-br-label {{
  font-size: 11px;
  color: var(--muted);
  margin-top: 4px;
}}

/* ── Empty state ───────────────────────────────────────────────────────── */
.empty-state {{
  text-align: center;
  padding: 60px 24px;
  color: var(--muted);
}}
.empty-icon {{ font-size: 36px; margin-bottom: 12px; }}
.empty-text {{ font-size: 14px; }}

/* ── Footer ────────────────────────────────────────────────────────────── */
#footer {{
  margin-top: 80px;
  padding: 32px;
  border-top: 1px solid var(--border);
  text-align: center;
  color: var(--muted);
  font-size: 12px;
}}

/* ── Print CSS ─────────────────────────────────────────────────────────── */
@media print {{
  #header, #tab-nav, .opp-filters, .opp-actions, #tab-overview, #tab-processes, #tab-blueprints, #tab-calc {{ display: none !important; }}
  #tab-opps {{ display: block !important; }}
  body {{ background: white; color: #0f172a; }}
  .opp-card {{ border: 1px solid #e2e8f0; break-inside: avoid; margin-bottom: 12px; }}
  .opp-grid {{ display: block; }}
  .opp-name {{ color: #0f172a; }}
  .opp-meta {{ color: #475569; }}
  .score-badge {{ border: 1px solid #e2e8f0; }}
}}

/* ── Responsive ────────────────────────────────────────────────────────── */
@media (max-width: 900px) {{
  #main {{ padding: 24px 16px; }}
  .stats-row, .feature-grid {{ grid-template-columns: 1fr; }}
  .how-steps {{ grid-template-columns: 1fr 1fr; }}
  .how-steps::before {{ display: none; }}
  #process-explorer {{ grid-template-columns: 1fr; }}
  .process-sidebar {{ position: static; }}
  .detail-grid {{ grid-template-columns: 1fr; }}
  .calc-grid {{ grid-template-columns: 1fr; }}
  .pilot-row {{ grid-template-columns: 1fr; }}
  .blueprint-grid {{ grid-template-columns: 1fr; }}
  #header {{ padding: 12px 16px; flex-wrap: wrap; }}
  #tab-nav {{ padding: 0 16px; overflow-x: auto; }}
}}
</style>
</head>
<body>

<!-- ── Header ──────────────────────────────────────────────────────────── -->
<header id="header">
  <div class="flex items-center gap-3">
    <div class="logo-mark">BA</div>
    <div>
      <div class="header-title">Business Agents Platform</div>
      <div class="header-sub">Intelligent Automation Framework</div>
    </div>
  </div>
  <div class="flex items-center gap-4">
    <div id="client-badge" class="header-badge"></div>
    <div class="header-date" id="header-date"></div>
  </div>
</header>

<!-- ── Tab Nav ─────────────────────────────────────────────────────────── -->
<nav id="tab-nav" role="tablist">
  <button class="tab-btn active" data-tab="overview"   role="tab" aria-selected="true">Overview</button>
  <button class="tab-btn"        data-tab="processes"  role="tab" aria-selected="false">Process Explorer</button>
  <button class="tab-btn"        data-tab="opps"       role="tab" aria-selected="false">Opportunities</button>
  <button class="tab-btn"        data-tab="blueprints" role="tab" aria-selected="false">Blueprints</button>
  <button class="tab-btn"        data-tab="calc"       role="tab" aria-selected="false">Value Calculator</button>
</nav>

<!-- ── Main ────────────────────────────────────────────────────────────── -->
<main id="main">

  <!-- ====================================================================
       TAB 1 — OVERVIEW
       ==================================================================== -->
  <section id="tab-overview" class="tab-panel active" role="tabpanel">

    <!-- Stat Cards -->
    <div class="stats-row" id="stat-cards"></div>

    <!-- Feature Grid -->
    <div class="section-title">Why Business Agents Platform</div>
    <div class="section-sub">Purpose-built for enterprise automation — grounded in process science, governed by design.</div>
    <div class="feature-grid">
      <div class="feature-card">
        <div class="feature-icon fi-indigo">🛡️</div>
        <div class="feature-title">Authority-First Design</div>
        <div class="feature-desc">Every agent is classified <strong style="color:#86efac">LOW</strong>, <strong style="color:#fde047">MEDIUM</strong>, or <strong style="color:#fca5a5">HIGH</strong> authority before deployment — so your teams always know exactly what the agent can and cannot do autonomously.</div>
      </div>
      <div class="feature-card">
        <div class="feature-icon fi-cyan">🗺️</div>
        <div class="feature-title">Process-Grounded</div>
        <div class="feature-desc">Every agent maps to an APQC process code from the 12-function taxonomy. No black boxes — each automation traces directly to a named business process your teams already recognize.</div>
      </div>
      <div class="feature-card">
        <div class="feature-icon fi-green">⚡</div>
        <div class="feature-title">Static-First Architecture</div>
        <div class="feature-desc">Zero build toolchain. A single Python script reads your data and produces a pure-static web app — no webpack, no containers, no runtime dependencies. GitHub Pages compatible out of the box.</div>
      </div>
    </div>

    <!-- How It Works -->
    <div class="section-title">How It Works</div>
    <div class="section-sub">From initial discovery to live agents running in production — a four-stage engagement model.</div>
    <div class="how-steps">
      <div class="step-card">
        <div class="step-num">🔍</div>
        <div class="step-title">Discovery</div>
        <div class="step-desc">Map your processes to the APQC taxonomy and score automation opportunities by value and feasibility.</div>
      </div>
      <div class="step-card">
        <div class="step-num">📐</div>
        <div class="step-title">Blueprint</div>
        <div class="step-desc">Define agent logic, authority level, data I/O, and escalation rules before a single line of code is written.</div>
      </div>
      <div class="step-card">
        <div class="step-num">🚀</div>
        <div class="step-title">Pilot</div>
        <div class="step-desc">Deploy in a sandboxed environment, measure KPIs against baseline, and validate authority boundaries with real data.</div>
      </div>
      <div class="step-card">
        <div class="step-num">📈</div>
        <div class="step-title">Expand</div>
        <div class="step-desc">Promote verified agents to production and extend the pattern across functions, industries, and business units.</div>
      </div>
    </div>

    <!-- Pilot Results -->
    <div class="section-title">Live Pilot Results</div>
    <div class="section-sub">Sample outcomes from Consumer Goods pilot — 3 agents, 4-week run.</div>
    <div class="pilot-row">
      <div class="pilot-card">
        <div class="pilot-icon">📋</div>
        <div>
          <div class="pilot-value">4 PRs</div>
          <div class="pilot-label">Purchase Requisitions Auto-Created</div>
        </div>
      </div>
      <div class="pilot-card">
        <div class="pilot-icon">📊</div>
        <div>
          <div class="pilot-value">8 SKUs</div>
          <div class="pilot-label">Demand Forecasts Generated</div>
        </div>
      </div>
      <div class="pilot-card">
        <div class="pilot-icon">⚠️</div>
        <div>
          <div class="pilot-value">5 Alerts</div>
          <div class="pilot-label">Quality Events Reviewed & Triaged</div>
        </div>
      </div>
    </div>

  </section>

  <!-- ====================================================================
       TAB 2 — PROCESS EXPLORER
       ==================================================================== -->
  <section id="tab-processes" class="tab-panel" role="tabpanel">
    <div class="section-title">Process Explorer</div>
    <div class="section-sub">All 127 APQC-mapped processes across 12 business functions. Click any card to expand details.</div>
    <div id="process-explorer">
      <aside class="process-sidebar card-sm">
        <input type="search" class="search-box" id="proc-search" placeholder="Search processes…" autocomplete="off" />
        <div class="sidebar-title">Functions</div>
        <div id="func-pills"></div>
      </aside>
      <div>
        <div class="process-grid" id="process-grid"></div>
      </div>
    </div>
  </section>

  <!-- ====================================================================
       TAB 3 — OPPORTUNITIES
       ==================================================================== -->
  <section id="tab-opps" class="tab-panel" role="tabpanel">
    <div class="section-title">Automation Opportunities</div>
    <div class="section-sub">Scored and filtered automation opportunities across your process landscape.</div>

    <div class="opp-filters">
      <div class="filter-group">
        <label>Industry</label>
        <div class="filter-pills" id="industry-filter-pills"></div>
      </div>
      <div class="filter-group">
        <label>Function</label>
        <select class="filter-select" id="func-filter-select">
          <option value="">All Functions</option>
        </select>
      </div>
      <div class="filter-group">
        <label>Min. Opportunity Score</label>
        <div class="score-range">
          <span style="font-size:12px;color:var(--muted)">1</span>
          <input type="range" class="score-slider" id="score-slider" min="1" max="5" value="1" />
          <span style="font-size:12px;color:var(--muted)">5</span>
          <span class="score-val" id="score-val">1</span>
        </div>
      </div>
      <div class="filter-group">
        <label>Capability Type</label>
        <div class="filter-pills" id="cap-type-filter-pills"></div>
      </div>
    </div>

    <div class="opp-actions">
      <div class="opp-count">Showing <strong id="opp-count-num">0</strong> opportunities</div>
      <button class="btn-export" onclick="window.print()">
        <span>⬇</span> Export to PDF
      </button>
    </div>

    <div class="opp-grid" id="opp-grid"></div>
  </section>

  <!-- ====================================================================
       TAB 4 — BLUEPRINTS
       ==================================================================== -->
  <section id="tab-blueprints" class="tab-panel" role="tabpanel">
    <div class="section-title">Agent Blueprints</div>
    <div class="section-sub">Production-ready agent specifications — fully documented, authority-classified, and sandbox-tested.</div>
    <div class="blueprint-grid" id="blueprint-grid"></div>
  </section>

  <!-- ====================================================================
       TAB 5 — VALUE CALCULATOR
       ==================================================================== -->
  <section id="tab-calc" class="tab-panel" role="tabpanel">
    <div class="section-title">ROI Value Calculator</div>
    <div class="section-sub">Estimate annual savings based on your team's profile and the deployed agent blueprints.</div>
    <div class="calc-card">
      <div class="calc-grid">
        <div class="calc-input-group">
          <label>Number of FTEs in scope</label>
          <input type="number" class="calc-input" id="calc-ftes" value="12" min="1" max="10000" />
        </div>
        <div class="calc-input-group">
          <label>Average fully-loaded salary (USD)</label>
          <input type="number" class="calc-input" id="calc-salary" value="95000" min="1" max="1000000" />
        </div>
        <div class="calc-input-group">
          <label>Hours saved per week (per FTE)</label>
          <input type="number" class="calc-input" id="calc-hrs" value="4.8" min="0.1" max="40" step="0.1" />
        </div>
        <div class="calc-input-group">
          <label>Estimated implementation weeks</label>
          <input type="number" class="calc-input" id="calc-impl" value="8" min="1" max="52" />
        </div>
      </div>
      <div class="calc-result">
        <div class="calc-result-label">Estimated Annual Savings</div>
        <div class="calc-result-value" id="calc-result-val">$0</div>
        <div class="calc-result-sub" id="calc-result-sub">Based on your inputs</div>
        <div class="calc-breakdown">
          <div class="calc-br-item">
            <div class="calc-br-val" id="calc-br-hrs">0</div>
            <div class="calc-br-label">Hours saved / year</div>
          </div>
          <div class="calc-br-item">
            <div class="calc-br-val" id="calc-br-payback">0</div>
            <div class="calc-br-label">Weeks to payback</div>
          </div>
          <div class="calc-br-item">
            <div class="calc-br-val" id="calc-br-roi">0%</div>
            <div class="calc-br-label">First-year ROI</div>
          </div>
        </div>
      </div>
      <p style="margin-top:20px;font-size:12px;color:var(--muted);text-align:center">
        Pre-filled with estimates from the <span id="calc-blueprint-count">3</span> deployed agent blueprints.
        Assumes 48 working weeks/year and $150k average implementation cost.
      </p>
    </div>
  </section>

</main>

<footer id="footer">
  Business Agents Platform &mdash; Client Engagement Portal &mdash; Generated <span id="gen-date"></span>
  <br /><span style="color:var(--border)">Confidential — Prepared for authorized recipients only</span>
</footer>

<!-- ── Embedded Data ─────────────────────────────────────────────────── -->
<script>
const DATA = {data_json};
</script>

<!-- ── App Logic ─────────────────────────────────────────────────────── -->
<script>
(function () {{
  'use strict';

  // ── Constants ──────────────────────────────────────────────────────────
  const FUNC_COLORS = {func_colors_js};

  const FUNC_SHORT = {{
    1: 'Strategy',
    2: 'Products',
    3: 'Sales & Mktg',
    4: 'Deliver',
    5: 'Services',
    6: 'Cust. Service',
    7: 'HR',
    8: 'IT',
    9: 'Finance',
    10: 'Assets',
    11: 'Risk & Compl.',
    12: 'Ext. Relations',
  }};

  // Build lookup maps
  const funcById = Object.fromEntries(DATA.functions.map(f => [f.id, f]));
  const industryById = Object.fromEntries(DATA.industries.map(i => [i.id, i]));
  const capTypeById  = Object.fromEntries(DATA.capability_types.map(c => [c.id, c]));

  // Build process → capability lookup
  const capsByProc = {{}};
  DATA.capabilities.forEach(c => {{
    if (c.process_id) {{
      (capsByProc[c.process_id] = capsByProc[c.process_id] || []).push(c);
    }}
  }});

  // Build process → blueprint lookup (by slug pattern)
  const blueprintProcessSlugs = new Set(DATA.blueprints.map(b => b.slug));

  // ── URL param: client name ─────────────────────────────────────────────
  const params = new URLSearchParams(window.location.search);
  const clientName = params.get('client') || 'Your Organization';
  document.getElementById('client-badge').textContent = 'For: ' + clientName;

  // ── Dates ──────────────────────────────────────────────────────────────
  const now = new Date();
  const dateStr = now.toLocaleDateString('en-US', {{ year: 'numeric', month: 'long', day: 'numeric' }});
  document.getElementById('header-date').textContent = dateStr;
  document.getElementById('gen-date').textContent = dateStr;

  // ── Tab switching ──────────────────────────────────────────────────────
  document.querySelectorAll('.tab-btn').forEach(btn => {{
    btn.addEventListener('click', () => {{
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
    }});
  }});

  // ── Helpers ────────────────────────────────────────────────────────────
  function scoreClass(s) {{
    if (s >= 5) return 'score-5';
    if (s >= 4) return 'score-4';
    if (s >= 3) return 'score-3';
    if (s >= 2) return 'score-2';
    return 'score-1';
  }}

  function scoreLabel(s) {{
    if (s >= 5) return 'Score ' + s + ' — Critical';
    if (s >= 4) return 'Score ' + s + ' — High';
    if (s >= 3) return 'Score ' + s + ' — Medium';
    return 'Score ' + s;
  }}

  function funcColor(fid) {{ return FUNC_COLORS[fid] || '#6366f1'; }}

  function starDots(score, max=5) {{
    let html = '<div class="score-stars">';
    for (let i = 1; i <= max; i++) {{
      let cls = i <= score
        ? (score >= 5 ? 'star high' : score >= 4 ? 'star med' : 'star low')
        : 'star';
      html += `<div class="${{cls}}"></div>`;
    }}
    html += '</div>';
    return html;
  }}

  function formatKpi(k) {{
    return k.replace(/_/g, ' ').replace(/\\b\\w/g, c => c.toUpperCase());
  }}

  function escHtml(s) {{
    if (!s) return '';
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }}

  function formatCurrency(n) {{
    if (n >= 1_000_000) return '$' + (n / 1_000_000).toFixed(1) + 'M';
    if (n >= 1_000)     return '$' + Math.round(n / 1_000) + 'K';
    return '$' + Math.round(n);
  }}

  // ── OVERVIEW ───────────────────────────────────────────────────────────
  (function renderOverview() {{
    const m = DATA.meta;
    document.getElementById('stat-cards').innerHTML = `
      <div class="stat-card">
        <div class="stat-number">127</div>
        <div class="stat-label">Processes Mapped</div>
        <div class="stat-sub">Across 12 APQC business functions</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">${{m.blueprint_count}}</div>
        <div class="stat-label">Agent Blueprints Ready</div>
        <div class="stat-sub">Fully specified, sandbox-tested</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">${{m.industries_covered}}</div>
        <div class="stat-label">Industries Covered</div>
        <div class="stat-sub">Consumer Goods, Pharma, MFG, FS, Retail</div>
      </div>
    `;
    document.getElementById('calc-blueprint-count').textContent = m.blueprint_count;
  }})();

  // ── PROCESS EXPLORER ──────────────────────────────────────────────────
  (function renderProcesses() {{
    let selectedFunc = null;
    let searchTerm   = '';
    let expandedId   = null;

    // Count per function
    const funcCount = {{}};
    DATA.processes.forEach(p => {{
      funcCount[p.function_id] = (funcCount[p.function_id] || 0) + 1;
    }});

    // Render function pills
    const pillContainer = document.getElementById('func-pills');
    const allPill = document.createElement('button');
    allPill.className = 'func-pill active';
    allPill.innerHTML = `<span class="func-dot" style="background:var(--indigo)"></span>All Functions
      <span class="func-pill-count">127</span>`;
    allPill.addEventListener('click', () => {{
      selectedFunc = null;
      document.querySelectorAll('.func-pill').forEach(p => p.classList.remove('active'));
      allPill.classList.add('active');
      render();
    }});
    pillContainer.appendChild(allPill);

    DATA.functions.forEach(f => {{
      const btn = document.createElement('button');
      btn.className = 'func-pill';
      const color = funcColor(f.id);
      btn.innerHTML = `<span class="func-dot" style="background:${{color}}"></span>
        ${{escHtml(f.name.replace(/^Develop and Manage /,'').replace(/^Develop /,'').replace(/^Manage /,'').slice(0,26))}}
        <span class="func-pill-count">${{funcCount[f.id] || 0}}</span>`;
      btn.addEventListener('click', () => {{
        selectedFunc = f.id;
        document.querySelectorAll('.func-pill').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        render();
      }});
      pillContainer.appendChild(btn);
    }});

    // Search
    document.getElementById('proc-search').addEventListener('input', e => {{
      searchTerm = e.target.value.toLowerCase();
      expandedId = null;
      render();
    }});

    function render() {{
      const grid = document.getElementById('process-grid');
      const filtered = DATA.processes.filter(p => {{
        if (selectedFunc !== null && p.function_id !== selectedFunc) return false;
        if (searchTerm && !p.name.toLowerCase().includes(searchTerm) &&
            !(p.apqc_code || '').toLowerCase().includes(searchTerm)) return false;
        return true;
      }});

      if (filtered.length === 0) {{
        grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1">
          <div class="empty-icon">🔍</div>
          <div class="empty-text">No processes match your search.</div>
        </div>`;
        return;
      }}

      grid.innerHTML = filtered.map(p => {{
        const fn    = funcById[p.function_id];
        const color = funcColor(p.function_id);
        const fnShort = fn ? (FUNC_SHORT[p.function_id] || fn.name.slice(0,20)) : '';
        const score = p.opportunity_score;
        const caps  = capsByProc[p.id] || [];
        const expanded = p.id === expandedId;

        // Industry tags for this process
        const indTags = (p.industries || []).map(ip => {{
          const ind = industryById[ip.industry_id];
          return ind ? `<span class="industry-tag">${{escHtml(ind.code)}}</span>` : '';
        }}).join('');

        // Capability chips for detail panel
        const capChips = caps.slice(0, 8).map(c => {{
          const ct = capTypeById[c.capability_type_id];
          return `<span class="cap-chip">${{escHtml(c.name)}}</span>`;
        }}).join('');

        const detailOpen = expanded ? 'open' : '';
        const desc = p.description ? `<div style="font-size:12px;color:var(--secondary);line-height:1.6;margin-bottom:12px">${{escHtml(p.description)}}</div>` : '';

        return `
        <div class="proc-card ${{expanded ? 'expanded' : ''}}" data-id="${{p.id}}" onclick="toggleProc(${{p.id}})">
          <div class="proc-func-badge" style="background:${{color}}1a;color:${{color}};border:1px solid ${{color}}33">
            ${{escHtml(fnShort)}}
          </div>
          <div class="proc-name">${{escHtml(p.name)}}</div>
          <div class="proc-code">${{escHtml(p.apqc_code || '')}}</div>
          <div style="display:flex;justify-content:space-between;align-items:center">
            ${{starDots(score)}}
            ${{score > 0 ? `<span style="font-size:11px;color:var(--muted)">Score ${{score}}</span>` : ''}}
          </div>
          <div class="proc-detail ${{detailOpen}}">
            ${{desc}}
            <div class="detail-grid">
              <div>
                <div class="detail-section-title">Industries</div>
                ${{indTags || '<span style="font-size:12px;color:var(--muted)">Universal</span>'}}
              </div>
              <div>
                <div class="detail-section-title">Agent Capabilities</div>
                ${{capChips || '<span style="font-size:12px;color:var(--muted)">No capabilities mapped</span>'}}
              </div>
              <div>
                <div class="detail-section-title">Level ${{p.level}} Process</div>
                <div style="font-size:12px;color:var(--secondary)">
                  APQC: ${{escHtml(p.apqc_code || 'N/A')}}<br/>
                  Function: ${{escHtml(fn ? fn.name : '')}}<br/>
                  ${{p.is_universal ? '🌐 Universal' : '🏭 Industry-specific'}}
                </div>
              </div>
            </div>
          </div>
        </div>`;
      }}).join('');
    }}

    window.toggleProc = function(id) {{
      expandedId = expandedId === id ? null : id;
      render();
      if (expandedId !== null) {{
        const el = document.querySelector(`[data-id="${{id}}"]`);
        if (el) el.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
      }}
    }};

    render();
  }})();

  // ── OPPORTUNITIES ─────────────────────────────────────────────────────
  (function renderOpportunities() {{
    let selIndustries = new Set();
    let selFunc       = '';
    let minScore      = 1;
    let selCapType    = '';

    // Populate function select
    const funcSel = document.getElementById('func-filter-select');
    DATA.functions.forEach(f => {{
      const opt = document.createElement('option');
      opt.value = f.id;
      opt.textContent = f.name;
      funcSel.appendChild(opt);
    }});
    funcSel.addEventListener('change', e => {{ selFunc = e.target.value; render(); }});

    // Industry pills
    const indPills = document.getElementById('industry-filter-pills');
    DATA.industries.forEach(ind => {{
      const btn = document.createElement('button');
      btn.className = 'filter-pill';
      btn.textContent = ind.code;
      btn.title = ind.name;
      btn.addEventListener('click', () => {{
        if (selIndustries.has(ind.id)) {{
          selIndustries.delete(ind.id);
          btn.classList.remove('active');
        }} else {{
          selIndustries.add(ind.id);
          btn.classList.add('active');
        }}
        render();
      }});
      indPills.appendChild(btn);
    }});

    // Score slider
    const slider   = document.getElementById('score-slider');
    const scoreVal = document.getElementById('score-val');
    slider.addEventListener('input', e => {{
      minScore = parseInt(e.target.value);
      scoreVal.textContent = minScore;
      render();
    }});

    // Capability type pills
    const capPills = document.getElementById('cap-type-filter-pills');
    DATA.capability_types.forEach(ct => {{
      const btn = document.createElement('button');
      btn.className = 'filter-pill';
      btn.textContent = ct.name;
      btn.addEventListener('click', () => {{
        if (selCapType === ct.slug) {{
          selCapType = '';
          btn.classList.remove('active');
        }} else {{
          selCapType = ct.slug;
          document.querySelectorAll('#cap-type-filter-pills .filter-pill').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
        }}
        render();
      }});
      capPills.appendChild(btn);
    }});

    // Build blueprint process IDs set (simple heuristic: processes with blueprint coverage)
    const bpProcessNames = new Set(DATA.blueprints.map(b => b.title.toLowerCase()));

    function hasBlueprintForProcess(proc) {{
      // Check if any blueprint slug contains a fragment of the process name
      const name = proc.name.toLowerCase();
      return DATA.blueprints.some(b => {{
        const btitle = b.title.toLowerCase();
        const words = name.split(' ').filter(w => w.length > 4);
        return words.some(w => btitle.includes(w));
      }});
    }}

    function render() {{
      // Gather candidates: processes with opportunity score >= minScore
      const candidates = DATA.processes.filter(p => {{
        if (p.opportunity_score < minScore) return false;
        if (p.opportunity_score === 0) return false;
        if (selFunc && p.function_id !== parseInt(selFunc)) return false;

        if (selIndustries.size > 0) {{
          const procInds = new Set((p.industries || []).map(ip => ip.industry_id));
          const hasMatch = [...selIndustries].some(id => procInds.has(id));
          if (!hasMatch && !p.is_universal) return false;
        }}

        if (selCapType) {{
          const caps = capsByProc[p.id] || [];
          const hasCapType = caps.some(c => {{
            const ct = capTypeById[c.capability_type_id];
            return ct && ct.slug === selCapType;
          }});
          if (!hasCapType) return false;
        }}

        return true;
      }}).sort((a, b) => b.opportunity_score - a.opportunity_score);

      document.getElementById('opp-count-num').textContent = candidates.length;
      const grid = document.getElementById('opp-grid');

      if (candidates.length === 0) {{
        grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1">
          <div class="empty-icon">🎯</div>
          <div class="empty-text">No opportunities match the current filters.</div>
        </div>`;
        return;
      }}

      grid.innerHTML = candidates.map(p => {{
        const fn    = funcById[p.function_id];
        const score = p.opportunity_score;
        const indTags = (p.industries || []).map(ip => {{
          const ind = industryById[ip.industry_id];
          return ind ? `<span class="opp-ind-tag">${{escHtml(ind.name)}}</span>` : '';
        }}).join('');
        const hasBp = hasBlueprintForProcess(p);
        const caps = capsByProc[p.id] || [];
        const primaryCap = caps[0];
        const capTypeName = primaryCap ? (capTypeById[primaryCap.capability_type_id] || {{}}).name || '' : '';

        return `
        <div class="opp-card">
          <div class="opp-header">
            <div>
              <div class="opp-name">${{escHtml(p.name)}}</div>
              <div class="opp-code">${{escHtml(p.apqc_code || '')}}</div>
            </div>
            <div class="score-badge ${{scoreClass(score)}}">${{scoreLabel(score)}}</div>
          </div>
          <div class="opp-meta">
            ${{escHtml(fn ? fn.name : '')}}
            ${{capTypeName ? ' &middot; ' + escHtml(capTypeName) : ''}}
          </div>
          ${{indTags ? `<div class="opp-tags">${{indTags}}</div>` : ''}}
          ${{hasBp ? `<div class="opp-tags">
            <span class="blueprint-badge">✓ Blueprint Available</span>
          </div>` : ''}}
        </div>`;
      }}).join('');
    }}

    render();
  }})();

  // ── BLUEPRINTS ────────────────────────────────────────────────────────
  (function renderBlueprints() {{
    const grid = document.getElementById('blueprint-grid');

    grid.innerHTML = DATA.blueprints.map((b, idx) => {{
      const authClass = 'auth-' + b.authority_level;
      const authLabel = b.authority_level.toUpperCase();

      const kpis = Array.isArray(b.kpis) ? b.kpis : [];
      const kpiHtml = kpis.map(k =>
        `<span class="kpi-chip">${{escHtml(formatKpi(k))}}</span>`
      ).join('');

      const sysHtml = (b.systems || []).map(s =>
        `<span class="system-chip">⚙ ${{escHtml(s)}}</span>`
      ).join('');

      const triggerIcon = {{
        scheduled: '🕐', event: '⚡', threshold: '📊', manual: '👤'
      }}[b.trigger_type] || '▶';

      // Build I/O detail HTML
      function renderIO(items, isInput) {{
        if (!Array.isArray(items)) return '<em style="color:var(--muted);font-size:12px">N/A</em>';
        return items.map(item => {{
          const endpoint = item.endpoint || item.description || '';
          const purpose  = item.purpose || '';
          return `<div class="io-item">
            <span class="io-system">${{escHtml(item.system || '')}}</span>
            ${{endpoint ? `<div class="io-endpoint">${{escHtml(endpoint)}}</div>` : ''}}
            ${{purpose  ? `<div class="io-purpose">${{escHtml(purpose)}}</div>` : ''}}
          </div>`;
        }}).join('');
      }}

      const inputHtml  = renderIO(b.data_inputs, true);
      const outputHtml = renderIO(b.data_outputs, false);

      const hrs = b.estimated_time_saved_hrs_week;

      return `
      <div class="bp-card">
        <div class="bp-header">
          <div class="bp-title">${{escHtml(b.title)}}</div>
          <div class="authority-badge ${{authClass}}">${{authLabel}}</div>
        </div>
        <div class="bp-business-value">${{escHtml(b.business_value || '')}}</div>
        ${{hrs ? `
        <div class="bp-metrics-row">
          <div class="bp-metric" style="flex:1">
            <div class="bp-metric-val">${{hrs}}</div>
            <div class="bp-metric-label">hrs saved / week</div>
          </div>
          <div class="bp-metric" style="flex:1">
            <div class="bp-metric-val">${{Math.round(hrs * 48)}}</div>
            <div class="bp-metric-label">hrs saved / year</div>
          </div>
          <div class="bp-metric" style="flex:1">
            <div class="bp-metric-val">${{b.version}}</div>
            <div class="bp-metric-label">Version</div>
          </div>
        </div>` : ''}}
        ${{kpiHtml ? `<div class="bp-kpis">${{kpiHtml}}</div>` : ''}}
        ${{sysHtml ? `<div class="bp-systems">${{sysHtml}}</div>` : ''}}
        <div class="trigger-row">
          <span class="trigger-label">Trigger:</span>
          <span class="trigger-chip">${{triggerIcon}} ${{escHtml(b.trigger_type)}}</span>
          ${{b.authority_scope ? `<span style="font-size:11px;color:var(--muted);margin-left:4px;flex:1" title="${{escHtml(b.authority_scope)}}">&nbsp;&mdash; ${{escHtml(b.authority_scope.slice(0,60))}}${{b.authority_scope.length > 60 ? '…' : ''}}</span>` : ''}}
        </div>
        <button class="bp-expand-btn" onclick="toggleBpIO(${{idx}})">
          <span id="bp-expand-icon-${{idx}}">▼</span> View Data Inputs &amp; Outputs
        </button>
        <div class="bp-io-detail" id="bp-io-${{idx}}">
          <div class="io-section">
            <div class="io-title">Data Inputs</div>
            ${{inputHtml}}
          </div>
          <div class="io-section">
            <div class="io-title">Data Outputs</div>
            ${{outputHtml}}
          </div>
        </div>
      </div>`;
    }}).join('');
  }})();

  window.toggleBpIO = function(idx) {{
    const panel = document.getElementById('bp-io-' + idx);
    const icon  = document.getElementById('bp-expand-icon-' + idx);
    const open  = panel.classList.toggle('open');
    icon.textContent = open ? '▲' : '▼';
  }};

  // ── VALUE CALCULATOR ──────────────────────────────────────────────────
  (function setupCalc() {{
    const IMPL_COST = 150_000;
    const WEEKS_PER_YEAR = 48;

    function calc() {{
      const ftes   = parseFloat(document.getElementById('calc-ftes').value)   || 0;
      const salary = parseFloat(document.getElementById('calc-salary').value) || 0;
      const hrs    = parseFloat(document.getElementById('calc-hrs').value)    || 0;
      const impl   = parseFloat(document.getElementById('calc-impl').value)   || 0;

      const hourlyRate    = salary / (WEEKS_PER_YEAR * 40);
      const hrsPerYear    = ftes * hrs * WEEKS_PER_YEAR;
      const annualSavings = hrsPerYear * hourlyRate;
      const paybackWeeks  = annualSavings > 0 ? Math.round(IMPL_COST / (annualSavings / WEEKS_PER_YEAR)) : 0;
      const roi           = annualSavings > 0 ? Math.round(((annualSavings - IMPL_COST) / IMPL_COST) * 100) : 0;

      document.getElementById('calc-result-val').textContent  = formatCurrency(annualSavings);
      document.getElementById('calc-result-sub').textContent  =
        `Across ${{ftes}} FTEs saving ${{hrs}} hrs/week each`;
      document.getElementById('calc-br-hrs').textContent      = Math.round(hrsPerYear).toLocaleString();
      document.getElementById('calc-br-payback').textContent  = paybackWeeks + ' wks';
      document.getElementById('calc-br-roi').textContent      = roi + '%';
    }}

    ['calc-ftes', 'calc-salary', 'calc-hrs', 'calc-impl'].forEach(id => {{
      document.getElementById(id).addEventListener('input', calc);
    }});

    calc();
  }})();

}})();
</script>
</body>
</html>"""

    return html


def main():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}", file=sys.stderr)
        sys.exit(1)

    print(f"Reading database: {DB_PATH}")
    data = fetch_data(DB_PATH)

    print(f"  {data['meta']['process_count']} processes")
    print(f"  {len(data['functions'])} functions")
    print(f"  {len(data['industries'])} industries")
    print(f"  {len(data['capabilities'])} capabilities")
    print(f"  {data['meta']['blueprint_count']} blueprints")
    print(f"  {data['meta']['industries_covered']} industries covered")

    html = build_html(data)

    os.makedirs(SCRIPT_DIR, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = os.path.getsize(OUT_PATH) / 1024
    print(f"\nWrote {OUT_PATH} ({size_kb:.1f} KB)")
    print("Open with:  open client-portal/index.html")
    print("or:         python3 -m http.server 8080 --directory client-portal/")


if __name__ == "__main__":
    main()
