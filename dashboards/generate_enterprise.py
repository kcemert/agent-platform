#!/usr/bin/env python3
"""
generate_enterprise.py — Epic 37: Enterprise Portfolio Dashboard
Queries the business_agents.db and generates dashboards/enterprise.html
"""

import sqlite3
import json
from datetime import datetime

DB = "/Users/keith_ai/Documents/Agentic Projects/business-agents/business_agents.db"
OUT = "/Users/keith_ai/Documents/Agentic Projects/dashboards/enterprise.html"

conn = sqlite3.connect(DB)
cur = conn.cursor()

# ── 1. KPI Strip ──────────────────────────────────────────────────────────────
bp_count       = cur.execute("SELECT COUNT(*) FROM agent_blueprints").fetchone()[0]
industry_count = cur.execute("SELECT COUNT(*) FROM industries").fetchone()[0]
function_count = cur.execute("SELECT COUNT(*) FROM functions").fetchone()[0]
action_count   = cur.execute("SELECT COUNT(*) FROM process_agent_actions").fetchone()[0]

# ── 2. Lifecycle stage distribution ──────────────────────────────────────────
lifecycle_raw = cur.execute(
    "SELECT lifecycle_stage, COUNT(*) FROM agent_blueprints GROUP BY lifecycle_stage"
).fetchall()
lifecycle = dict(lifecycle_raw)
# Ordered stages for funnel
STAGES = ["blueprint", "scaffolded", "sandbox", "validated", "pilot_ready", "production"]
lifecycle_ordered = [(s, lifecycle.get(s, 0)) for s in STAGES]

# ── 3. Industry coverage table ────────────────────────────────────────────────
industries = cur.execute("SELECT id, code, name FROM industries ORDER BY name").fetchall()

bp_by_industry_raw = cur.execute("""
    SELECT i.code, i.name,
           COUNT(ab.id) as bp_count,
           MAX(ab.lifecycle_stage) as max_stage
    FROM industries i
    LEFT JOIN agent_blueprints ab ON LOWER(ab.slug) LIKE LOWER(i.code) || '-%'
    GROUP BY i.id ORDER BY i.name
""").fetchall()

proc_by_ind_raw = cur.execute("""
    SELECT i.code, COUNT(ip.process_id) as proc_count
    FROM industries i
    LEFT JOIN industry_processes ip ON ip.industry_id = i.id
    GROUP BY i.id
""").fetchall()
proc_by_ind = {row[0]: row[1] for row in proc_by_ind_raw}

# Hours saved per industry via blueprint slug
bp_hours_raw = cur.execute("""
    SELECT slug, estimated_time_saved_hrs_week FROM agent_blueprints
""").fetchall()

def get_industry_code(slug):
    for ind in industries:
        code = ind[1].lower()
        if slug.lower().startswith(code + "-"):
            return ind[1]
    return None

industry_hours = {}
for slug, hrs in bp_hours_raw:
    code = get_industry_code(slug)
    if code and hrs:
        industry_hours[code] = industry_hours.get(code, 0) + (hrs or 0)

industry_table = []
for row in bp_by_industry_raw:
    code, name, bp_c, max_stage = row
    procs = proc_by_ind.get(code, 0)
    hrs = industry_hours.get(code, 0)
    hrs_display = f"{hrs:.0f}" if hrs > 0 else "—"
    status = max_stage or "blueprint"
    industry_table.append({
        "name": name, "code": code, "blueprints": bp_c,
        "processes": procs, "hrs_saved": hrs_display, "status": status
    })

# ── 4. Value tracking ─────────────────────────────────────────────────────────
value_raw = cur.execute("""
    SELECT metric_type, SUM(delta) as total, unit
    FROM value_tracking GROUP BY metric_type, unit
""").fetchall()
value_map = {row[0]: {"total": row[1], "unit": row[2]} for row in value_raw}

hours_saved   = value_map.get("hours_saved",   {}).get("total", 0)
prs_created   = value_map.get("prs_created",   {}).get("total", 0)
exc_caught    = value_map.get("exceptions_caught", {}).get("total", 0)

# ── 5. Function × Industry heatmap ───────────────────────────────────────────
heatmap_raw = cur.execute("""
    SELECT f.name, i.code, COUNT(paa.id) as action_count
    FROM functions f
    CROSS JOIN industries i
    LEFT JOIN processes p ON p.function_id = f.id
    LEFT JOIN industry_processes ip ON ip.process_id = p.id AND ip.industry_id = i.id
    LEFT JOIN process_agent_actions paa ON paa.process_id = p.id
    GROUP BY f.id, i.id
    ORDER BY f.id, i.code
""").fetchall()

functions_list = cur.execute("SELECT name FROM functions ORDER BY id").fetchall()
functions_names = [r[0] for r in functions_list]
industries_list = cur.execute("SELECT code FROM industries ORDER BY code").fetchall()
industry_codes  = [r[0] for r in industries_list]

heatmap = {}
for fn, ind, cnt in heatmap_raw:
    heatmap.setdefault(fn, {})[ind] = cnt

conn.close()

# ── Timestamp ─────────────────────────────────────────────────────────────────
generated_at = datetime.now().strftime("%B %d, %Y at %H:%M")

# ══ Build HTML ════════════════════════════════════════════════════════════════

def stage_color(stage):
    colors = {
        "blueprint":  "#6e7681",
        "scaffolded": "#388bfd",
        "sandbox":    "#56d364",
        "validated":  "#d29922",
        "pilot_ready":"#3fb950",
        "production": "#26a641",
    }
    return colors.get(stage, "#6e7681")

def stage_label(stage):
    return stage.replace("_", "-").title()

def rai_coverage_color(fraction):
    if fraction == 1.0:  return "#3fb950"
    if fraction > 0:     return "#d29922"
    return "#f85149"

def rai_icon(fraction):
    if fraction == 1.0: return "&#10003;"
    if fraction > 0:    return "&#9651;"
    return "&#10007;"

# ── Funnel SVG ────────────────────────────────────────────────────────────────
def build_funnel_svg(lifecycle_ordered):
    max_count = max(c for _, c in lifecycle_ordered) or 1
    svg_width  = 900
    svg_height = 110
    seg_w = svg_width // len(lifecycle_ordered)
    bars = []
    for i, (stage, count) in enumerate(lifecycle_ordered):
        color  = stage_color(stage)
        label  = stage_label(stage)
        height = max(8, int((count / max_count) * 80)) if count > 0 else 4
        x      = i * seg_w
        y      = 90 - height
        opacity = "1.0" if count > 0 else "0.25"
        bars.append(f"""
        <g>
          <rect x="{x+4}" y="{y}" width="{seg_w-8}" height="{height}"
                fill="{color}" rx="4" opacity="{opacity}"/>
          <text x="{x + seg_w//2}" y="{y - 5}" text-anchor="middle"
                font-size="13" font-weight="700" fill="{color}"
                opacity="{opacity}">{count}</text>
          <text x="{x + seg_w//2}" y="106" text-anchor="middle"
                font-size="10" fill="#8b949e">{label}</text>
        </g>""")
    return f"""<svg viewBox="0 0 {svg_width} {svg_height}" width="100%" height="{svg_height}px" style="overflow:visible">
      {''.join(bars)}
    </svg>"""

funnel_svg = build_funnel_svg(lifecycle_ordered)

# ── Industry table rows ───────────────────────────────────────────────────────
def status_badge_html(status):
    colors = {
        "sandbox":    ("#56d36420", "#56d364"),
        "blueprint":  ("#6e768120", "#8b949e"),
        "scaffolded": ("#388bfd20", "#388bfd"),
        "validated":  ("#d2992220", "#d29922"),
        "pilot_ready":("#3fb95020", "#3fb950"),
        "production": ("#26a64120", "#26a641"),
    }
    bg, fg = colors.get(status, ("#6e768120", "#8b949e"))
    label = stage_label(status)
    return f'<span class="stage-badge" style="background:{bg};color:{fg};border:1px solid {fg}40">{label}</span>'

ind_rows = ""
for row in industry_table:
    ind_rows += f"""
          <tr>
            <td class="td-name">{row['name']}</td>
            <td class="td-code">{row['code']}</td>
            <td class="td-num">{row['blueprints']}</td>
            <td class="td-num">{row['processes']}</td>
            <td class="td-num">{row['hrs_saved']}</td>
            <td>{status_badge_html(row['status'])}</td>
          </tr>"""

# ── Heatmap table ─────────────────────────────────────────────────────────────
def heat_color(count):
    if count == 0:    return "#161b22"
    if count <= 50:   return "#0e4429"
    if count <= 100:  return "#006d32"
    return "#26a641"

def fn_short(name):
    shorts = {
        "Develop Vision and Strategy": "Vision & Strategy",
        "Develop and Manage Products and Services": "Products & Services",
        "Market and Sell Products and Services": "Market & Sell",
        "Deliver Physical Products": "Deliver Products",
        "Deliver Services": "Deliver Services",
        "Manage Customer Service": "Customer Service",
        "Develop and Manage Human Capital": "Human Capital",
        "Manage Information Technology": "IT Management",
        "Manage Financial Resources": "Finance",
        "Acquire, Construct, and Manage Assets": "Assets",
        "Manage Enterprise Risk, Compliance, and Resiliency": "Risk & Compliance",
        "Manage External Relationships": "External Rel.",
    }
    return shorts.get(name, name[:20])

heatmap_header = "".join(f'<th class="hm-col">{code}</th>' for code in industry_codes)
heatmap_rows = ""
for fn in functions_names:
    cells = ""
    for code in industry_codes:
        count = heatmap.get(fn, {}).get(code, 0)
        color = heat_color(count)
        cells += f'<td class="hm-cell" title="{fn} × {code}: {count} actions" style="background:{color}"></td>'
    heatmap_rows += f'<tr><td class="hm-fn">{fn_short(fn)}</td>{cells}</tr>'

# ── RAI cards ─────────────────────────────────────────────────────────────────
rai_pillars = [
    {
        "name": "Transparency",
        "fraction": 3/3,
        "note": "All sandbox agents log full reasoning to agent_runs"
    },
    {
        "name": "Oversight",
        "fraction": 3/3,
        "note": "Approval workflow for MEDIUM/HIGH authority actions"
    },
    {
        "name": "Fairness",
        "fraction": 0/3,
        "note": "No fairness metrics yet — planned for Epic 38+"
    },
    {
        "name": "Privacy",
        "fraction": 2/3,
        "note": "Replenishment + CAPA use PII-free data; forecast uses sales data"
    },
    {
        "name": "Accountability",
        "fraction": 3/3,
        "note": "All runs logged with full audit trail in agent_runs"
    },
    {
        "name": "Robustness",
        "fraction": 2/3,
        "note": "Retry / circuit-breaker in replenishment + CAPA agents"
    },
]

rai_cards = ""
for p in rai_pillars:
    frac = p["fraction"]
    color = rai_coverage_color(frac)
    icon  = rai_icon(frac)
    num   = int(frac * 3)
    pct_w = int(frac * 100)
    rai_cards += f"""
          <div class="rai-card">
            <div class="rai-header">
              <span class="rai-icon" style="color:{color}">{icon}</span>
              <span class="rai-name">{p['name']}</span>
              <span class="rai-score" style="color:{color}">{num}/3</span>
            </div>
            <div class="rai-bar-track">
              <div class="rai-bar-fill" style="width:{pct_w}%;background:{color}"></div>
            </div>
            <div class="rai-note">{p['note']}</div>
          </div>"""

# ROI calcs
hourly_rate = 85
value_realized = hours_saved * hourly_rate
projected_10   = value_realized / 3 * 10  # scale from 3 agents
projected_full = value_realized / 3 * bp_count

# ══ Final HTML ════════════════════════════════════════════════════════════════
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Enterprise Portfolio Dashboard — Business Agents Platform</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --bg:      #0d1117;
      --card:    #1c2128;
      --border:  #30363d;
      --text:    #e6edf3;
      --muted:   #8b949e;
      --accent:  #58a6ff;
      --green:   #3fb950;
      --amber:   #d29922;
      --red:     #f85149;
    }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      font-size: 14px;
      line-height: 1.5;
    }}

    /* ── Top Nav ── */
    .top-nav {{
      background: var(--card);
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 32px;
      height: 52px;
      position: sticky;
      top: 0;
      z-index: 100;
    }}
    .nav-brand {{
      font-size: 15px;
      font-weight: 600;
      color: var(--text);
      letter-spacing: -0.01em;
    }}
    .nav-personas {{
      display: flex;
      gap: 4px;
    }}
    .nav-tab {{
      padding: 6px 14px;
      border-radius: 6px;
      font-size: 13px;
      font-weight: 500;
      color: var(--muted);
      text-decoration: none;
      transition: color 0.15s, background 0.15s;
    }}
    .nav-tab:hover {{ color: var(--text); background: rgba(88,166,255,0.1); }}
    .nav-tab.active {{
      color: var(--accent);
      background: rgba(88,166,255,0.12);
      border: 1px solid rgba(88,166,255,0.25);
    }}

    /* ── Page header ── */
    .page-header {{
      padding: 32px 40px 24px;
      border-bottom: 1px solid var(--border);
    }}
    .page-header h1 {{
      font-size: 22px;
      font-weight: 700;
      color: var(--text);
      margin-bottom: 4px;
    }}
    .page-header .subtitle {{
      font-size: 13px;
      color: var(--muted);
    }}

    /* ── KPI Strip ── */
    .kpi-strip {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 1px;
      background: var(--border);
      border-bottom: 1px solid var(--border);
    }}
    .kpi-cell {{
      background: var(--card);
      padding: 24px 32px;
      text-align: center;
    }}
    .kpi-number {{
      font-size: 40px;
      font-weight: 700;
      color: var(--accent);
      letter-spacing: -0.03em;
      line-height: 1;
      margin-bottom: 6px;
    }}
    .kpi-label {{
      font-size: 12px;
      color: var(--muted);
      font-weight: 500;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}

    /* ── Main content ── */
    .main {{ padding: 40px; max-width: 1400px; margin: 0 auto; }}

    /* ── Section ── */
    .section {{
      margin-bottom: 48px;
    }}
    .section-title {{
      font-size: 16px;
      font-weight: 600;
      color: var(--text);
      margin-bottom: 4px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .section-title::before {{
      content: '';
      display: inline-block;
      width: 3px;
      height: 16px;
      background: var(--accent);
      border-radius: 2px;
    }}
    .section-sub {{
      font-size: 12px;
      color: var(--muted);
      margin-bottom: 20px;
      padding-left: 11px;
    }}

    /* ── Card container ── */
    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 24px;
    }}

    /* ── Funnel ── */
    .funnel-caption {{
      margin-top: 16px;
      font-size: 12px;
      color: var(--muted);
      font-style: italic;
      text-align: center;
    }}

    /* ── Industry table ── */
    .ind-table-wrap {{ overflow-x: auto; }}
    table.ind-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    table.ind-table th {{
      text-align: left;
      padding: 10px 16px;
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--muted);
      border-bottom: 1px solid var(--border);
      white-space: nowrap;
    }}
    table.ind-table td {{
      padding: 10px 16px;
      border-bottom: 1px solid rgba(48,54,61,0.5);
      vertical-align: middle;
    }}
    table.ind-table tr:last-child td {{ border-bottom: none; }}
    table.ind-table tr:hover td {{ background: rgba(255,255,255,0.02); }}
    .td-name {{ font-weight: 500; }}
    .td-code {{ color: var(--muted); font-family: monospace; font-size: 12px; }}
    .td-num  {{ text-align: right; color: var(--muted); }}
    .stage-badge {{
      display: inline-block;
      padding: 2px 10px;
      border-radius: 20px;
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.03em;
      text-transform: capitalize;
    }}

    /* ── Value cards ── */
    .value-cards {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
      margin-bottom: 20px;
    }}
    .value-card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 24px;
    }}
    .value-metric {{
      font-size: 36px;
      font-weight: 700;
      color: var(--accent);
      letter-spacing: -0.02em;
      margin-bottom: 4px;
    }}
    .value-label {{
      font-size: 13px;
      font-weight: 600;
      color: var(--text);
      margin-bottom: 6px;
    }}
    .value-note {{
      font-size: 12px;
      color: var(--muted);
    }}

    /* ── ROI block ── */
    .roi-block {{
      background: rgba(88,166,255,0.06);
      border: 1px solid rgba(88,166,255,0.2);
      border-radius: 8px;
      padding: 20px 24px;
    }}
    .roi-line {{
      font-size: 14px;
      color: var(--text);
      margin-bottom: 6px;
    }}
    .roi-line strong {{ color: var(--accent); }}
    .roi-line:last-child {{ margin-bottom: 0; }}
    .roi-note {{
      margin-top: 12px;
      font-size: 12px;
      color: var(--muted);
      font-style: italic;
    }}

    /* ── Heatmap ── */
    .hm-wrap {{ overflow-x: auto; }}
    table.hm-table {{
      border-collapse: collapse;
      font-size: 11px;
    }}
    .hm-fn {{
      padding: 6px 10px;
      color: var(--muted);
      white-space: nowrap;
      font-size: 11px;
      border-right: 1px solid var(--border);
      min-width: 130px;
    }}
    .hm-col {{
      padding: 6px 4px;
      text-align: center;
      color: var(--muted);
      font-weight: 600;
      font-size: 10px;
      letter-spacing: 0.03em;
      border-bottom: 1px solid var(--border);
      min-width: 52px;
    }}
    .hm-cell {{
      width: 52px;
      height: 32px;
      cursor: default;
      transition: opacity 0.15s;
    }}
    .hm-cell:hover {{ opacity: 0.7; }}
    .hm-legend {{
      display: flex;
      align-items: center;
      gap: 16px;
      margin-top: 14px;
      font-size: 11px;
      color: var(--muted);
    }}
    .hm-leg-swatch {{
      display: inline-block;
      width: 16px;
      height: 16px;
      border-radius: 3px;
      vertical-align: middle;
      margin-right: 4px;
    }}

    /* ── RAI pillars ── */
    .rai-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
    }}
    .rai-card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 20px;
    }}
    .rai-header {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 12px;
    }}
    .rai-icon {{
      font-size: 16px;
      font-weight: 700;
      width: 24px;
      text-align: center;
    }}
    .rai-name {{
      font-size: 14px;
      font-weight: 600;
      color: var(--text);
      flex: 1;
    }}
    .rai-score {{
      font-size: 14px;
      font-weight: 700;
    }}
    .rai-bar-track {{
      background: rgba(255,255,255,0.06);
      border-radius: 4px;
      height: 6px;
      margin-bottom: 10px;
    }}
    .rai-bar-fill {{
      height: 100%;
      border-radius: 4px;
      transition: width 0.3s ease;
    }}
    .rai-note {{
      font-size: 11px;
      color: var(--muted);
      line-height: 1.5;
    }}
    .rai-link {{
      display: block;
      margin-top: 16px;
      font-size: 12px;
      color: var(--accent);
      text-decoration: none;
    }}
    .rai-link:hover {{ text-decoration: underline; }}

    /* ── Footer ── */
    .footer {{
      border-top: 1px solid var(--border);
      padding: 20px 40px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 12px;
      color: var(--muted);
      flex-wrap: wrap;
      gap: 12px;
    }}
    .footer a {{
      color: var(--accent);
      text-decoration: none;
    }}
    .footer a:hover {{ text-decoration: underline; }}
    .footer-links {{ display: flex; gap: 24px; align-items: center; }}
  </style>
</head>
<body>

<!-- ── Top Nav ── -->
<nav class="top-nav">
  <div class="nav-brand">&#9889; Business Agents Platform</div>
  <div class="nav-personas">
    <a href="operations.html" class="nav-tab">Operations</a>
    <a href="finance.html" class="nav-tab">Finance</a>
    <a href="compliance.html" class="nav-tab">Compliance</a>
    <a href="enterprise.html" class="nav-tab active">Enterprise &#8599;</a>
  </div>
</nav>

<!-- ── Page Header ── -->
<div class="page-header">
  <h1>Enterprise Portfolio Dashboard</h1>
  <div class="subtitle">C-suite rollup &mdash; lifecycle funnel, industry coverage, value realized, and responsible AI coverage across all {bp_count} blueprints</div>
</div>

<!-- ── KPI Strip ── -->
<div class="kpi-strip">
  <div class="kpi-cell">
    <div class="kpi-number">{bp_count}</div>
    <div class="kpi-label">Total Blueprints</div>
  </div>
  <div class="kpi-cell">
    <div class="kpi-number">{industry_count}</div>
    <div class="kpi-label">Industries Covered</div>
  </div>
  <div class="kpi-cell">
    <div class="kpi-number">{function_count}</div>
    <div class="kpi-label">Functions Covered</div>
  </div>
  <div class="kpi-cell">
    <div class="kpi-number">{action_count:,}</div>
    <div class="kpi-label">Agent Actions</div>
  </div>
</div>

<!-- ── Main ── -->
<main class="main">

  <!-- ── Section 1: Lifecycle Funnel ── -->
  <section class="section">
    <div class="section-title">Platform Lifecycle Funnel</div>
    <div class="section-sub">Blueprint maturity progression &mdash; {bp_count} blueprints across 6 stages</div>
    <div class="card">
      {funnel_svg}
      <div class="funnel-caption">
        Platform is at early sandbox stage. Target: 5 agents at pilot-ready by Q3 2026.
      </div>
    </div>
  </section>

  <!-- ── Section 2: Industry Coverage Table ── -->
  <section class="section">
    <div class="section-title">Industry Coverage</div>
    <div class="section-sub">{industry_count} industries &mdash; blueprint count, process coverage, and deployment status</div>
    <div class="card ind-table-wrap">
      <table class="ind-table">
        <thead>
          <tr>
            <th>Industry</th>
            <th>Code</th>
            <th style="text-align:right">Blueprints</th>
            <th style="text-align:right">Processes</th>
            <th style="text-align:right">Est. Hrs Saved/wk</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {ind_rows}
        </tbody>
      </table>
    </div>
  </section>

  <!-- ── Section 3: Value Realized ── -->
  <section class="section">
    <div class="section-title">Value Realized</div>
    <div class="section-sub">Live tracking from {3} sandbox agents &mdash; Consumer Goods pilot (10-week run)</div>

    <div class="value-cards">
      <div class="value-card">
        <div class="value-metric">{hours_saved:.1f}<span style="font-size:20px;color:var(--muted)"> hrs</span></div>
        <div class="value-label">Hours Saved</div>
        <div class="value-note">Across 3 sandbox agents, 10-week pilot</div>
      </div>
      <div class="value-card">
        <div class="value-metric">{int(prs_created)}<span style="font-size:20px;color:var(--muted)"> PRs</span></div>
        <div class="value-label">Purchase Requisitions Created</div>
        <div class="value-note">Automated purchase requisitions, replenishment agent</div>
      </div>
      <div class="value-card">
        <div class="value-metric">{int(exc_caught)}<span style="font-size:20px;color:var(--muted)"> alerts</span></div>
        <div class="value-label">Exceptions Caught</div>
        <div class="value-note">Quality deviations detected, CAPA agent</div>
      </div>
    </div>

    <div class="roi-block">
      <div class="roi-line"><strong>{hours_saved:.1f} hours</strong> &times; $85/hr = <strong>${value_realized:,.0f}</strong> value realized</div>
      <div class="roi-line">Projected at 10 agents: <strong>${projected_10:,.0f}/year</strong></div>
      <div class="roi-line">Projected at full platform ({bp_count} agents): <strong>${projected_full:,.0f}/year</strong></div>
      <div class="roi-note">(Value tracking active for CG pilot agents. Expand to all deployed agents in future iterations.)</div>
    </div>
  </section>

  <!-- ── Section 4: Function Coverage Heatmap ── -->
  <section class="section">
    <div class="section-title">Function &times; Industry Coverage Heatmap</div>
    <div class="section-sub">{function_count} functions &times; {industry_count} industries &mdash; cell intensity = agent action count at intersection</div>
    <div class="card hm-wrap">
      <table class="hm-table">
        <thead>
          <tr>
            <th class="hm-fn" style="border-bottom:1px solid var(--border)"></th>
            {heatmap_header}
          </tr>
        </thead>
        <tbody>
          {heatmap_rows}
        </tbody>
      </table>
      <div class="hm-legend">
        <span><span class="hm-leg-swatch" style="background:#161b22"></span>0</span>
        <span><span class="hm-leg-swatch" style="background:#0e4429"></span>1&ndash;50</span>
        <span><span class="hm-leg-swatch" style="background:#006d32"></span>51&ndash;100</span>
        <span><span class="hm-leg-swatch" style="background:#26a641"></span>101+</span>
      </div>
    </div>
  </section>

  <!-- ── Section 5: Responsible AI Coverage ── -->
  <section class="section">
    <div class="section-title">Responsible AI Coverage</div>
    <div class="section-sub">Six-pillar RAI framework coverage across 3 deployed sandbox agents</div>
    <div class="rai-grid">
      {rai_cards}
    </div>
    <a href="../office-skills/outputs/responsible-ai/index.html" class="rai-link">
      View Full Responsible AI Framework &#8594;
    </a>
  </section>

</main>

<!-- ── Footer ── -->
<footer class="footer">
  <div class="footer-links">
    <a href="operations.html">&larr; Back to Operations Dashboard</a>
    <a href="../index.html">View Platform Index &rarr;</a>
  </div>
  <div>Generated: {generated_at} &nbsp;|&nbsp; Business Agents Platform &mdash; Internal use only</div>
</footer>

</body>
</html>
"""

with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)

size_kb = len(html.encode("utf-8")) / 1024
print(f"enterprise.html written: {size_kb:.1f} KB")
print(f"KPIs: {bp_count} blueprints, {industry_count} industries, {function_count} functions, {action_count} actions")
print(f"Lifecycle: {dict(lifecycle_raw)}")
print(f"Value: hours_saved={hours_saved}, prs_created={prs_created}, exceptions_caught={exc_caught}")
print(f"ROI: ${value_realized:,.0f} realized, ${projected_10:,.0f} at 10 agents, ${projected_full:,.0f} at full platform")
