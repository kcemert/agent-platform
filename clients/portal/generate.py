#!/usr/bin/env python3
"""
generate.py — Client Portal Generator

Reads a client's profile.json and generates a portal index.html from a template.
Currently used for documentation/reference; Kimre, PrecisionParts, and MeridianBank
portals are hand-crafted. This tool generates a basic portal for new clients.

Usage:
  python3 clients/portal/generate.py --slug kimre
  python3 clients/portal/generate.py --slug newclient --name "New Client Inc"
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

WORKSPACE    = Path(__file__).parent.parent.parent
CLIENTS_DIR  = WORKSPACE / "clients"

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{name} — Agent Platform Engagement Portal</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --bg: #0f1117; --card: #161b2e; --border: #1e293b;
      --text: #f1f5f9; --text-sec: #94a3b8; --text-muted: #64748b;
      --accent: {accent}; --accent-dim: {accent}22;
    }}
    body {{ font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); font-size: 14px; line-height: 1.6; }}
    .container {{ max-width: 1100px; margin: 0 auto; padding: 0 24px; }}
    .header {{ background: var(--card); border-bottom: 1px solid var(--border); padding: 40px 0; }}
    .header h1 {{ font-size: 28px; font-weight: 800; color: var(--accent); }}
    .header .sub {{ color: var(--text-sec); margin-top: 4px; }}
    .badge {{ display: inline-block; padding: 3px 10px; border-radius: 4px; font-size: 11px; font-weight: 600; background: var(--accent-dim); color: var(--accent); margin-right: 8px; }}
    section {{ padding: 48px 0; border-bottom: 1px solid var(--border); }}
    h2 {{ font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; color: var(--text-muted); margin-bottom: 24px; }}
    .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 24px; }}
    .profile-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }}
    .profile-item label {{ font-size: 11px; color: var(--text-muted); display: block; margin-bottom: 4px; }}
    .profile-item .val {{ font-size: 16px; font-weight: 600; color: var(--text); }}
    .agent-list {{ display: flex; flex-direction: column; gap: 12px; }}
    .agent-card {{ background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 16px; display: flex; justify-content: space-between; align-items: center; }}
    .agent-rank {{ font-size: 11px; color: var(--text-muted); }}
    .agent-name {{ font-weight: 600; }}
    .agent-value {{ color: var(--accent); font-weight: 700; }}
    .cta {{ display: inline-block; background: var(--accent); color: #fff; padding: 12px 24px; border-radius: 8px; font-weight: 600; text-decoration: none; margin-top: 24px; }}
  </style>
</head>
<body>
<header class="header">
  <div class="container">
    <h1>{name}</h1>
    <p class="sub">{tagline} &mdash; {location}</p>
    <div style="margin-top:16px">
      <span class="badge">{industry_code}</span>
      <span class="badge">{size_tier}</span>
      <span class="badge">{engagement_tier}</span>
    </div>
  </div>
</header>

<main class="container">
  <section>
    <h2>Company Profile (F20)</h2>
    <div class="profile-grid">
      <div class="profile-item"><label>Industry</label><div class="val">{industry_code}</div></div>
      <div class="profile-item"><label>Size Tier</label><div class="val">{size_tier}</div></div>
      <div class="profile-item"><label>Business Model</label><div class="val">{business_model}</div></div>
      <div class="profile-item"><label>Regulatory Score</label><div class="val">{regulatory_score}/5</div></div>
      <div class="profile-item"><label>Integration Tier</label><div class="val">{integration_tier}</div></div>
      <div class="profile-item"><label>Data Readiness</label><div class="val">{data_readiness_score}/25</div></div>
      <div class="profile-item"><label>Engagement Tier</label><div class="val">{engagement_tier}</div></div>
      <div class="profile-item"><label>Annual Value</label><div class="val">£{annual_value_gbp:,}</div></div>
    </div>
  </section>

  <section>
    <h2>Agent Opportunities</h2>
    <div class="agent-list">
      {agent_cards}
    </div>
  </section>

  <section>
    <h2>Recommended Pilot</h2>
    <div class="card">
      <p style="color:var(--text-sec)">Pilot agent: <strong style="color:var(--text)">{pilot_name}</strong></p>
      <p style="margin-top:8px;color:var(--text-sec)">Timeline: <strong style="color:var(--text)">{pilot_weeks} weeks</strong> &nbsp;|&nbsp; Year 1 value: <strong style="color:var(--accent)">£{pilot_value:,}</strong></p>
    </div>
  </section>

  <section>
    <h2>Next Steps</h2>
    <div class="card">
      <p>Contact: <strong>{contact_name}</strong> &lt;<a href="mailto:{contact_email}" style="color:var(--accent)">{contact_email}</a>&gt;</p>
      <a class="cta" href="mailto:{contact_email}?subject=Agent Platform — Next Steps">Schedule Working Session &rarr;</a>
    </div>
  </section>
</main>

<footer style="padding:40px 0;text-align:center;color:var(--text-muted);font-size:12px">
  Generated {generated_at} · Business Agents Platform
</footer>
</body>
</html>"""

ACCENT_MAP = {
    "CG":     "#f97316",
    "MFG":    "#6366f1",
    "FS":     "#22c55e",
    "PHARMA": "#a855f7",
    "RETAIL": "#06b6d4",
    "HEALTH": "#ef4444",
}

def generate(slug: str):
    profile_path = CLIENTS_DIR / slug / "profile.json"
    if not profile_path.exists():
        print(f"Error: profile.json not found at {profile_path}")
        sys.exit(1)

    with open(profile_path) as f:
        p = json.load(f)

    accent = ACCENT_MAP.get(p.get("industry_code", ""), "#6366f1")

    agent_cards = ""
    for a in p.get("agents", []):
        status_color = "#22c55e" if a.get("status") == "pilot_ready" else "#64748b"
        agent_cards += f"""<div class="agent-card">
          <div>
            <div class="agent-rank">Rank {a['rank']}</div>
            <div class="agent-name">{a['name']}</div>
          </div>
          <div class="agent-value">£{a.get('value_gbp_annual', 0):,}/yr</div>
          <div style="color:{status_color};font-size:11px;font-weight:600">{a.get('status','blueprint').upper()}</div>
        </div>"""

    pilot = p.get("pilot_agent", {})
    output = TEMPLATE.format(
        name=p["name"], tagline=p.get("tagline",""), location=p.get("location",""),
        industry_code=p.get("industry_code",""), size_tier=p.get("size_tier",""),
        business_model=p.get("business_model",""), regulatory_score=p.get("regulatory_score",0),
        integration_tier=p.get("integration_tier",""), data_readiness_score=p.get("data_readiness_score",0),
        engagement_tier=p.get("engagement_tier",""), annual_value_gbp=p.get("annual_value_gbp",0),
        agent_cards=agent_cards, pilot_name=pilot.get("name",""),
        pilot_weeks=pilot.get("timeline_weeks",0), pilot_value=pilot.get("year1_value_gbp",0),
        contact_name=p.get("contact",{}).get("name",""), contact_email=p.get("contact",{}).get("email",""),
        accent=accent, generated_at=datetime.now().strftime("%Y-%m-%d"),
    )

    out_path = CLIENTS_DIR / slug / "index.html"
    with open(out_path, "w") as f:
        f.write(output)
    print(f"Generated: {out_path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", required=True)
    args = parser.parse_args()
    generate(args.slug)

if __name__ == "__main__":
    main()
