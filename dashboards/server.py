#!/usr/bin/env python3
"""
server.py — Business Agents Platform Dashboard Server (Epic 38)
Run: python3 dashboards/server.py
URL: http://localhost:8500
"""

import json
import os
import sqlite3
import subprocess
import sys
import glob
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent                      # dashboards/
WORKSPACE   = BASE_DIR.parent                             # Agentic Projects/
DB_PATH     = WORKSPACE / "business-agents" / "business_agents.db"
AGENTS_DIR  = WORKSPACE / "pilot-agents"

AGENT_PATHS = {
    "cg-replenishment-pr-agent": str(AGENTS_DIR / "replenishment_agent.py"),
    "cg-demand-forecast-agent":  str(AGENTS_DIR / "demand_forecast_agent.py"),
    "cg-quality-capa-agent":     str(AGENTS_DIR / "quality_capa_agent.py"),
    # ── Kimre Mock Agents ──
    "kimre-rfq-quote-agent":           str(AGENTS_DIR / "kimre" / "rfq_quote_agent.py"),
    "kimre-quality-compliance-agent":  str(AGENTS_DIR / "kimre" / "quality_compliance_agent.py"),
    "kimre-order-notifier-agent":      str(AGENTS_DIR / "kimre" / "order_notifier_agent.py"),
    "kimre-retrofit-reorder-agent":    str(AGENTS_DIR / "kimre" / "retrofit_reorder_agent.py"),
    # ── Platform Agents ──
    "mfg-predictive-maintenance-agent": str(AGENTS_DIR / "mfg-predictive-maintenance-agent.py"),
    "ap-invoice-processing":            str(AGENTS_DIR / "ap-invoice-processing.py"),
    # ── Kimre New Agents ──
    "kimre-marketing-agent":       str(AGENTS_DIR / "kimre" / "marketing_agent.py"),
    "kimre-research-agent":        str(AGENTS_DIR / "kimre" / "research_agent.py"),
    "kimre-business-model-agent":  str(AGENTS_DIR / "kimre" / "business_model_agent.py"),
    # ── Platform Ops Agents ──
    "github-push-agent":           str(AGENTS_DIR / "github_push_agent.py"),
}

PERSONA_MAP = {
    "cg-replenishment-pr-agent": "operations",
    "cg-demand-forecast-agent":  "operations",
    "cg-quality-capa-agent":     "compliance",
    "kimre-rfq-quote-agent":           "sales",
    "kimre-quality-compliance-agent":  "engineering",
    "kimre-order-notifier-agent":      "customer-service",
    "kimre-retrofit-reorder-agent":    "executive",
    "mfg-predictive-maintenance-agent": "operations",
    "ap-invoice-processing":            "finance",
    "kimre-marketing-agent":            "sales",
    "kimre-research-agent":             "sales",
    "kimre-business-model-agent":       "executive",
    "github-push-agent":                "operations",
}

# ── Flask app ───────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder=str(BASE_DIR), static_url_path="")
CORS(app)  # Allow all origins for local prototype

# ── DB helper ───────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create new tables on startup if they don't exist, seed initial data."""
    conn = get_db()
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS pilot_runs (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            run_at        TEXT NOT NULL DEFAULT (datetime('now')),
            slug          TEXT NOT NULL,
            dry_run       INTEGER DEFAULT 1,
            outcome       TEXT,
            output_file   TEXT,
            summary       TEXT,
            output_json   TEXT,
            duration_secs REAL,
            triggered_by  TEXT DEFAULT 'dashboard'
        );
        CREATE TABLE IF NOT EXISTS approvals (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at     TEXT DEFAULT (datetime('now')),
            decided_at     TEXT,
            item_id        TEXT NOT NULL,
            item_type      TEXT,
            blueprint_slug TEXT,
            decision       TEXT DEFAULT 'pending',
            decided_by     TEXT,
            decision_notes TEXT,
            item_details   TEXT
        );
        CREATE TABLE IF NOT EXISTS recommendations (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id           INTEGER NOT NULL,
            slug             TEXT NOT NULL,
            rec_type         TEXT,
            item_id          TEXT,
            item_label       TEXT,
            urgency          TEXT DEFAULT 'medium',
            recommended_action TEXT,
            detail_json      TEXT,
            decision         TEXT DEFAULT 'pending',
            decided_by       TEXT DEFAULT 'operations',
            decided_at       TEXT,
            modified_value   TEXT
        );
    """)
    conn.commit()
    # Seed 2 CAPA approval items if table is empty
    count = cur.execute("SELECT COUNT(*) FROM approvals").fetchone()[0]
    if count == 0:
        items = [
            ("CAPA-2024-089", "capa", "cg-quality-capa-agent", "pending", None, None, None,
             json.dumps({"title": "Line 3 pH deviation — Batch 2024-441", "severity": "medium", "age_days": 3,
                         "details": "pH reading 6.8 vs spec 7.0-7.4. Root cause: buffer solution expired. Corrective action: Replace buffer, recalibrate."})),
            ("CAPA-2024-091", "capa", "cg-quality-capa-agent", "pending", None, None, None,
             json.dumps({"title": "Viscosity out of spec — Batch 2024-443", "severity": "low", "age_days": 1,
                         "details": "Viscosity 2340 cP vs spec 2200-2500 cP. Near limit. Monitor next batch. No production impact expected."})),
        ]
        cur.executemany("""
            INSERT INTO approvals (item_id, item_type, blueprint_slug, decision, decided_at, decided_by, decision_notes, item_details)
            VALUES (?,?,?,?,?,?,?,?)
        """, items)
        conn.commit()
    conn.close()
    print(f"[server] DB initialized. Tables: pilot_runs, approvals, recommendations. Seeded CAPA items.")

# ── Static file serving ─────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(str(BASE_DIR), "operations.html")

@app.route("/clients/<path:filename>")
def client_files(filename):
    return send_from_directory(str(WORKSPACE / "clients"), filename)

@app.route("/docs/<path:filename>")
def docs_files(filename):
    return send_from_directory(str(WORKSPACE / "docs"), filename)

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(str(BASE_DIR), filename)

# ── API: Health ─────────────────────────────────────────────────────────────
@app.route("/api/health")
def health():
    try:
        conn = get_db()
        bp_count = conn.execute("SELECT COUNT(*) FROM agent_blueprints").fetchone()[0]
        conn.close()
        return jsonify({"status": "ok", "db": "connected", "blueprints": bp_count, "agents": 3})
    except Exception as e:
        return jsonify({"status": "error", "db": str(e)}), 500

# ── API: DB Stats ────────────────────────────────────────────────────────────
@app.route("/api/db-stats")
def db_stats():
    """Return live platform statistics from the DB."""
    try:
        conn = get_db()
        cur = conn.cursor()
        stats = {}

        # Core counts
        stats["industries"]    = cur.execute("SELECT COUNT(*) FROM industries").fetchone()[0]
        stats["processes"]     = cur.execute("SELECT COUNT(*) FROM processes").fetchone()[0]
        stats["blueprints"]    = cur.execute("SELECT COUNT(*) FROM agent_blueprints").fetchone()[0]
        stats["agent_actions"] = cur.execute("SELECT COUNT(*) FROM process_agent_actions").fetchone()[0]
        stats["systems"]       = cur.execute("SELECT COUNT(*) FROM systems").fetchone()[0]
        stats["features"]      = cur.execute("SELECT COUNT(*) FROM features").fetchone()[0]
        stats["pilot_runs"]    = cur.execute("SELECT COUNT(*) FROM pilot_runs").fetchone()[0]
        stats["approvals_pending"] = cur.execute("SELECT COUNT(*) FROM approvals WHERE decision='pending'").fetchone()[0]
        stats["recommendations_pending"] = cur.execute("SELECT COUNT(*) FROM recommendations WHERE decision='pending'").fetchone()[0]

        # Blueprint lifecycle distribution
        lifecycle_rows = cur.execute(
            "SELECT lifecycle_stage, COUNT(*) as cnt FROM agent_blueprints GROUP BY lifecycle_stage"
        ).fetchall()
        stats["blueprint_lifecycle"] = {r["lifecycle_stage"]: r["cnt"] for r in lifecycle_rows}

        # Blueprint size_fit distribution
        size_rows = cur.execute(
            "SELECT size_fit, COUNT(*) as cnt FROM agent_blueprints WHERE size_fit IS NOT NULL GROUP BY size_fit"
        ).fetchall()
        stats["blueprint_size_fit"] = {r["size_fit"]: r["cnt"] for r in size_rows}

        # Industry process coverage
        coverage_rows = cur.execute("""
            SELECT i.code, i.name, COUNT(ip.process_id) as process_count
            FROM industries i
            LEFT JOIN industry_processes ip ON i.id = ip.industry_id
            GROUP BY i.id ORDER BY i.code
        """).fetchall()
        stats["industry_coverage"] = [{"code": r["code"], "name": r["name"], "processes": r["process_count"]} for r in coverage_rows]

        conn.close()
        return jsonify({"status": "ok", "stats": stats, "db_connected": True})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e), "db_connected": False})

# ── API: Agents list ─────────────────────────────────────────────────────────
@app.route("/api/agents")
def agents():
    persona = request.args.get("persona")  # optional filter
    conn = get_db()
    rows = conn.execute("""
        SELECT ab.slug, ab.title, ab.lifecycle_stage, ab.authority_level,
               ab.trigger_type, ab.estimated_time_saved_hrs_week as est_hours_per_week, ab.status,
               ab.lifecycle_notes, ab.business_value as description,
               (SELECT run_at FROM pilot_runs WHERE slug = ab.slug ORDER BY run_at DESC LIMIT 1) as last_run_at,
               (SELECT outcome FROM pilot_runs WHERE slug = ab.slug ORDER BY run_at DESC LIMIT 1) as last_run_outcome,
               (SELECT summary FROM pilot_runs WHERE slug = ab.slug ORDER BY run_at DESC LIMIT 1) as last_run_summary
        FROM agent_blueprints ab
        WHERE ab.lifecycle_stage IN ('sandbox', 'validated', 'pilot_ready', 'production')
        ORDER BY ab.slug
    """).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["persona"] = PERSONA_MAP.get(d["slug"], "operations")
        if persona and d["persona"] != persona:
            continue
        result.append(d)
    return jsonify(result)

# ── API: Agent detail ─────────────────────────────────────────────────────────
@app.route("/api/agents/<slug>")
def agent_detail(slug):
    conn = get_db()
    bp = conn.execute("""
        SELECT * FROM agent_blueprints WHERE slug = ?
    """, (slug,)).fetchone()
    if not bp:
        conn.close()
        return jsonify({"error": f"Agent '{slug}' not found"}), 404
    bp = dict(bp)
    bp["persona"] = PERSONA_MAP.get(slug, "operations")

    # Recent runs from pilot_runs
    runs = [dict(r) for r in conn.execute("""
        SELECT run_at, outcome, summary, duration_secs, dry_run, output_json
        FROM pilot_runs WHERE slug = ? ORDER BY run_at DESC LIMIT 10
    """, (slug,)).fetchall()]

    # Value summary from value_tracking
    value = [dict(r) for r in conn.execute("""
        SELECT metric_type, unit, COUNT(*) as run_count,
               SUM(delta) as total_delta, AVG(delta) as avg_delta
        FROM value_tracking WHERE blueprint_slug = ?
        GROUP BY metric_type
    """, (slug,)).fetchall()]

    # Trend data for sparklines (last 10 values per metric)
    trend_rows = conn.execute("""
        SELECT metric_type, delta, tracked_at
        FROM value_tracking WHERE blueprint_slug = ?
        ORDER BY tracked_at ASC
    """, (slug,)).fetchall()
    trends = {}
    for r in trend_rows:
        m = r["metric_type"]
        if m not in trends:
            trends[m] = []
        trends[m].append(r["delta"])

    # Pending approvals for this agent
    approvals = [dict(r) for r in conn.execute("""
        SELECT id, item_id, item_type, blueprint_slug, decision, created_at, decided_at, item_details
        FROM approvals WHERE blueprint_slug = ? AND decision = 'pending'
        ORDER BY created_at DESC
    """, (slug,)).fetchall()]
    for a in approvals:
        if a["item_details"]:
            a["item_details"] = json.loads(a["item_details"])

    conn.close()
    return jsonify({
        "blueprint": bp,
        "runs": runs,
        "value": value,
        "trends": trends,
        "approvals": approvals,
    })

# ── API: Portfolio (enterprise) ───────────────────────────────────────────────
@app.route("/api/portfolio")
def portfolio():
    conn = get_db()

    # Lifecycle distribution
    lifecycle_dist = {r["lifecycle_stage"]: r["cnt"] for r in conn.execute("""
        SELECT lifecycle_stage, COUNT(*) as cnt FROM agent_blueprints GROUP BY lifecycle_stage
    """).fetchall()}

    # KPI strip
    kpi = {
        "blueprints":    conn.execute("SELECT COUNT(*) FROM agent_blueprints").fetchone()[0],
        "industries":    conn.execute("SELECT COUNT(*) FROM industries").fetchone()[0],
        "functions":     conn.execute("SELECT COUNT(*) FROM functions").fetchone()[0],
        "agent_actions": conn.execute("SELECT COUNT(*) FROM process_agent_actions").fetchone()[0],
    }

    # Industry coverage
    industries = [dict(r) for r in conn.execute("""
        SELECT i.code, i.name,
               COUNT(DISTINCT ab.id) as bp_count,
               COUNT(DISTINCT ip.process_id) as process_count,
               CASE WHEN COUNT(DISTINCT CASE WHEN ab.lifecycle_stage <> 'blueprint' THEN ab.id END) > 0
                    THEN MAX(ab.lifecycle_stage) ELSE 'blueprint' END as top_lifecycle
        FROM industries i
        LEFT JOIN industry_processes ip ON ip.industry_id = i.id
        LEFT JOIN agent_blueprints ab ON ab.slug LIKE LOWER(i.code) || '-%'
        GROUP BY i.id ORDER BY i.name
    """).fetchall()]

    # Value totals from value_tracking
    value_rows = conn.execute("""
        SELECT metric_type, SUM(delta) as total FROM value_tracking GROUP BY metric_type
    """).fetchall()
    value_totals = {r["metric_type"]: r["total"] for r in value_rows}

    # Function x Industry heatmap data
    heatmap = [dict(r) for r in conn.execute("""
        SELECT f.name as function_name, f.id as function_id,
               i.code as industry_code,
               COUNT(paa.id) as action_count
        FROM functions f
        CROSS JOIN industries i
        LEFT JOIN processes p ON p.function_id = f.id
        LEFT JOIN industry_processes ip ON ip.process_id = p.id AND ip.industry_id = i.id
        LEFT JOIN process_agent_actions paa ON paa.process_id = p.id
        GROUP BY f.id, i.id
        ORDER BY f.id, i.code
    """).fetchall()]

    # Authority distribution
    authority_dist = {r["authority_level"]: r["cnt"] for r in conn.execute("""
        SELECT authority_level, COUNT(*) as cnt FROM agent_blueprints GROUP BY authority_level
    """).fetchall()}

    conn.close()
    return jsonify({
        "lifecycle_dist": lifecycle_dist,
        "kpi": kpi,
        "industries": industries,
        "value_totals": value_totals,
        "heatmap": heatmap,
        "authority_dist": authority_dist,
    })

def _extract_recommendations(slug, run_id, output, conn):
    """Parse agent output into individual recommendation rows."""
    if not output:
        return []
    recs = []
    try:
        if slug == "cg-replenishment-pr-agent":
            for pr in output.get("prs_created", []):
                urgency = "high" if pr.get("priority") == "HIGH_PRIORITY" else "medium"
                item_id = pr.get("material_id", "")
                # Try to get label from high_priority_flags
                label = item_id
                for flag in output.get("high_priority_flags", []):
                    if flag.get("material_id") == item_id:
                        label = flag.get("description", item_id)
                        break
                action = f"Create PO for {pr.get('quantity', '?')} units of {item_id}"
                conn.execute("""
                    INSERT INTO recommendations (run_id, slug, rec_type, item_id, item_label, urgency, recommended_action, detail_json)
                    VALUES (?, ?, 'pr_order', ?, ?, ?, ?, ?)
                """, (run_id, slug, item_id, label, urgency, action, json.dumps(pr)))
                recs.append({"item_id": item_id, "item_label": label, "urgency": urgency, "recommended_action": action, "rec_type": "pr_order"})

        elif slug == "cg-demand-forecast-agent":
            for fc in output.get("forecasts", []):
                cliff = fc.get("demand_cliff", False)
                conf = fc.get("confidence", "MEDIUM")
                if cliff:
                    urgency = "critical"
                elif conf == "LOW":
                    urgency = "high"
                elif conf == "MEDIUM":
                    urgency = "medium"
                else:
                    urgency = "low"
                item_id = fc.get("material_id", "")
                label = fc.get("description", item_id)
                growth = fc.get("growth_rate_pct", 0)
                if cliff:
                    action = f"Alert: demand cliff detected — review supply plan for {item_id}"
                elif growth > 10:
                    action = f"Monitor: {growth:.1f}% growth trend — consider increasing safety stock"
                elif growth < -10:
                    action = f"Monitor: {abs(growth):.1f}% demand decline — review reorder parameters"
                else:
                    action = f"Stable: {growth:.1f}% trend — no action required"
                conn.execute("""
                    INSERT INTO recommendations (run_id, slug, rec_type, item_id, item_label, urgency, recommended_action, detail_json)
                    VALUES (?, ?, 'forecast_signal', ?, ?, ?, ?, ?)
                """, (run_id, slug, item_id, label, urgency, action, json.dumps(fc)))
                recs.append({"item_id": item_id, "item_label": label, "urgency": urgency, "recommended_action": action, "rec_type": "forecast_signal"})

        elif slug == "cg-quality-capa-agent":
            for ca in output.get("capa_actions", []):
                sev = ca.get("severity", "medium").lower()
                urgency = sev if sev in ("low", "medium", "high", "critical") else "medium"
                item_id = ca.get("event_id", ca.get("line_id", ""))
                label = f"{ca.get('issue_type', 'Quality event')} — {ca.get('line_id', '')}"
                action = ca.get("capa_action", "Investigate quality event")
                conn.execute("""
                    INSERT INTO recommendations (run_id, slug, rec_type, item_id, item_label, urgency, recommended_action, detail_json)
                    VALUES (?, ?, 'capa_action', ?, ?, ?, ?, ?)
                """, (run_id, slug, item_id, label, urgency, action, json.dumps(ca)))
                recs.append({"item_id": item_id, "item_label": label, "urgency": urgency, "recommended_action": action, "rec_type": "capa_action"})

        elif slug == "kimre-rfq-quote-agent":
            for item in output.get("items", []):
                rec_type = item.get("rec_type", "quote_draft")
                item_id = item.get("rfq_id", "")
                label = f"RFQ {item_id} — {item.get('customer','')} — {item.get('product_family','')}"
                urgency = item.get("urgency", "medium")
                action = f"Scope draft: {item.get('product_family','')}, confidence {item.get('confidence',0.8):.0%}"
                if item.get("gaps"):
                    action += f" — GAPS: {'; '.join(item['gaps'])}"
                conn.execute("INSERT INTO recommendations (run_id, slug, rec_type, item_id, item_label, urgency, recommended_action, detail_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (run_id, slug, rec_type, item_id, label, urgency, action, json.dumps(item)))
                recs.append({"item_id": item_id, "item_label": label, "urgency": urgency, "recommended_action": action, "rec_type": rec_type})

        elif slug == "kimre-quality-compliance-agent":
            for item in output.get("items", []):
                if not item.get("flags"):
                    continue
                rec_type = "compliance_flag"
                urgency = item.get("urgency", "high")
                item_id = item.get("order_id", "")
                label = f"Order {item_id} — {item.get('customer','')} — Compliance Flag"
                action = "; ".join(item.get("flags", ["Compliance check required"]))
                conn.execute("INSERT INTO recommendations (run_id, slug, rec_type, item_id, item_label, urgency, recommended_action, detail_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (run_id, slug, rec_type, item_id, label, urgency, action, json.dumps(item)))
                recs.append({"item_id": item_id, "item_label": label, "urgency": urgency, "recommended_action": action, "rec_type": rec_type})

        elif slug == "kimre-order-notifier-agent":
            for item in output.get("items", []):
                rec_type = item.get("rec_type", "customer_notification")
                item_id = item.get("order_id", "")
                label = f"Order {item_id} — {item.get('customer','')} — {item.get('notification_type','notification').replace('_',' ').title()}"
                urgency = item.get("urgency", "medium")
                action = f"{item.get('notification_type','Notification')}: {item.get('subject','')}"
                conn.execute("INSERT INTO recommendations (run_id, slug, rec_type, item_id, item_label, urgency, recommended_action, detail_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (run_id, slug, rec_type, item_id, label, urgency, action, json.dumps(item)))
                recs.append({"item_id": item_id, "item_label": label, "urgency": urgency, "recommended_action": action, "rec_type": rec_type})

        elif slug == "kimre-retrofit-reorder-agent":
            for item in output.get("items", []):
                rec_type = "reorder_outreach"
                item_id = item.get("account", "").replace(" ", "-").lower()
                label = f"{item.get('account','')} — {item.get('product_purchased','')} — Reorder Opportunity"
                urgency = item.get("urgency", "low")
                action = f"Last order {item.get('months_since',0):.0f}mo ago — outreach draft ready"
                conn.execute("INSERT INTO recommendations (run_id, slug, rec_type, item_id, item_label, urgency, recommended_action, detail_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (run_id, slug, rec_type, item_id, label, urgency, action, json.dumps(item)))
                recs.append({"item_id": item_id, "item_label": label, "urgency": urgency, "recommended_action": action, "rec_type": rec_type})

        elif slug == "mfg-predictive-maintenance-agent":
            for line in output.get("lines_at_risk", []):
                urgency = "critical" if line.get("current_oee", 1.0) < 0.70 else "high"
                item_id = line.get("line_id", "")
                label = f"{line.get('name', item_id)} — OEE {line.get('current_oee',0):.1%}"
                action = f"Maintenance request recommended — OEE {line.get('current_oee',0):.1%}, delta {line.get('week_delta',0):.1%} vs 4wk ago"
                conn.execute("INSERT INTO recommendations (run_id, slug, rec_type, item_id, item_label, urgency, recommended_action, detail_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (run_id, slug, "oee_alert", item_id, label, urgency, action, json.dumps(line)))
                recs.append({"item_id": item_id, "item_label": label, "urgency": urgency, "recommended_action": action, "rec_type": "oee_alert"})

        elif slug == "ap-invoice-processing":
            for item in output.get("items", []):
                if item.get("status") not in ("approval_required", "anomaly"):
                    continue
                rec_type = item.get("rec_type", "invoice_approval")
                item_id = item.get("invoice_id", "")
                label = f"Invoice {item_id} — {item.get('vendor','')} — £{item.get('amount',0):,.0f}"
                urgency = item.get("urgency", "medium")
                action = item.get("reason", "Invoice requires review")
                conn.execute("INSERT INTO recommendations (run_id, slug, rec_type, item_id, item_label, urgency, recommended_action, detail_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (run_id, slug, rec_type, item_id, label, urgency, action, json.dumps(item)))
                recs.append({"item_id": item_id, "item_label": label, "urgency": urgency, "recommended_action": action, "rec_type": rec_type})

        elif slug == "kimre-marketing-agent":
            for item in output.get("items", []):
                rec_type = "marketing_followup"
                # Trade show contacts
                if "contact_id" in item:
                    item_id = item.get("contact_id", "")
                    label = f"{item.get('contact_name', '')} @ {item.get('company', '')} — {item.get('tradeshow', '')}"
                    urgency = item.get("urgency", "medium")
                    action = f"Send follow-up email: {item.get('subject', '')[:80]}"
                # Installed base accounts
                else:
                    item_id = item.get("account_id", "")
                    label = f"{item.get('account_name', '')} — {item.get('product_purchased', '')}"
                    urgency = item.get("urgency", "medium")
                    action = item.get("recommended_action", "Send outreach")
                conn.execute("INSERT INTO recommendations (run_id, slug, rec_type, item_id, item_label, urgency, recommended_action, detail_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (run_id, slug, rec_type, item_id, label, urgency, action, json.dumps(item)))
                recs.append({"item_id": item_id, "item_label": label, "urgency": urgency, "recommended_action": action, "rec_type": rec_type})

        elif slug == "kimre-research-agent":
            for item in output.get("items", []):
                rec_type = "prospect_lead"
                item_id = item.get("facility_id", "")
                label = f"{item.get('facility_name', '')} ({item.get('state', '')}) — {item.get('application', '')}"
                urgency = item.get("urgency", "medium")
                action = item.get("recommended_action", "Prospect follow-up")
                conn.execute("INSERT INTO recommendations (run_id, slug, rec_type, item_id, item_label, urgency, recommended_action, detail_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (run_id, slug, rec_type, item_id, label, urgency, action, json.dumps(item)))
                recs.append({"item_id": item_id, "item_label": label, "urgency": urgency, "recommended_action": action, "rec_type": rec_type})

        elif slug == "kimre-business-model-agent":
            for item in output.get("items", []):
                if item.get("recommendation") not in ("Expand", "Pilot First"):
                    continue
                rec_type = "model_move"
                item_id = item.get("move", "")
                label = item.get("move_label", item_id)
                urgency = item.get("urgency", "medium")
                action = f"{item.get('recommendation', '')} — {label} (score {item.get('composite_score', 0):.2f})"
                conn.execute("INSERT INTO recommendations (run_id, slug, rec_type, item_id, item_label, urgency, recommended_action, detail_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (run_id, slug, rec_type, item_id, label, urgency, action, json.dumps(item)))
                recs.append({"item_id": item_id, "item_label": label, "urgency": urgency, "recommended_action": action, "rec_type": rec_type})

        elif slug == "github-push-agent":
            for item in output.get("recommendations", []):
                rec_type = item.get("rec_type", "git_push")
                item_id = item.get("item_id", "")
                item_label = item.get("item_label", "")
                urgency = item.get("urgency", "medium")
                recommended_action = item.get("recommended_action", "")
                detail_json = json.dumps(item.get("detail", {}))
                conn.execute("INSERT INTO recommendations (run_id, slug, rec_type, item_id, item_label, urgency, recommended_action, detail_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (run_id, slug, rec_type, item_id, item_label, urgency, recommended_action, detail_json))
                recs.append({"item_id": item_id, "item_label": item_label, "urgency": urgency, "recommended_action": recommended_action, "rec_type": rec_type})

    except Exception as e:
        print(f"[recommendations] extraction error: {e}")
    return recs


# ── API: Run agent ────────────────────────────────────────────────────────────
@app.route("/api/run/<slug>", methods=["POST"])
def run_agent(slug):
    if slug not in AGENT_PATHS:
        return jsonify({"error": f"Agent '{slug}' is not a runnable sandbox agent"}), 400

    agent_path = AGENT_PATHS[slug]
    if not Path(agent_path).exists():
        return jsonify({"error": f"Agent script not found: {agent_path}"}), 500

    start = datetime.now()
    try:
        result = subprocess.run(
            [sys.executable, agent_path, "--dry-run"],
            capture_output=True, text=True, timeout=45,
            cwd=str(AGENTS_DIR)
        )
        duration = (datetime.now() - start).total_seconds()
        outcome = "success" if result.returncode == 0 else "failed"

        # Find the most recent output file
        output_json = None
        output_file = None
        outputs_dir = AGENTS_DIR / "outputs"
        if outputs_dir.exists():
            patterns = [
                str(outputs_dir / f"*{slug.replace('cg-', '').replace('-agent', '').replace('-', '_')}*.json"),
                str(outputs_dir / "*.json"),
            ]
            all_files = []
            for pattern in patterns:
                all_files.extend(glob.glob(pattern))
            if all_files:
                latest = max(all_files, key=os.path.getmtime)
                output_file = latest
                try:
                    with open(latest) as f:
                        output_json = json.load(f)
                except Exception:
                    pass

        # Build summary
        summary = _build_summary(slug, output_json, result.stdout)

        # Store in pilot_runs
        conn = get_db()
        cursor = conn.execute("""
            INSERT INTO pilot_runs (slug, dry_run, outcome, output_file, summary, output_json, duration_secs, triggered_by)
            VALUES (?, 1, ?, ?, ?, ?, ?, 'dashboard')
        """, (slug, outcome, output_file, summary, json.dumps(output_json) if output_json else None, duration))
        run_id = cursor.lastrowid
        conn.commit()

        # Extract recommendations
        recs = _extract_recommendations(slug, run_id, output_json, conn)
        conn.commit()
        conn.close()

        return jsonify({
            "outcome": outcome,
            "summary": summary,
            "duration_secs": round(duration, 1),
            "output": output_json,
            "stdout": result.stdout[-500:] if result.stdout else "",
            "run_id": run_id,
            "recommendations_count": len(recs),
            "recommendations": recs,
        })

    except subprocess.TimeoutExpired:
        duration = (datetime.now() - start).total_seconds()
        conn = get_db()
        conn.execute("""
            INSERT INTO pilot_runs (slug, dry_run, outcome, summary, duration_secs, triggered_by)
            VALUES (?, 1, 'failed', 'Agent timed out after 45s', ?, 'dashboard')
        """, (slug, duration))
        conn.commit()
        conn.close()
        return jsonify({"outcome": "failed", "summary": "Agent timed out after 45s", "duration_secs": duration}), 500

    except Exception as e:
        return jsonify({"outcome": "failed", "summary": str(e)}), 500

def _build_summary(slug, output, stdout):
    """Extract a human-readable summary from agent output."""
    if not output:
        if stdout:
            for line in stdout.strip().split("\n"):
                if any(k in line.lower() for k in ["created", "processed", "detected", "exceptions", "forecast"]):
                    return line.strip()[:120]
        return "Run completed"
    try:
        if slug == "cg-replenishment-pr-agent":
            n = len(output.get("prs_created", []))
            return f"{n} PRs created" if n else "No items triggered — all stock healthy"
        elif slug == "cg-demand-forecast-agent":
            n = output.get("items_analysed", output.get("items_forecast", output.get("items_processed", "?")))
            acc = output.get("accuracy_pct", "")
            return f"{n} SKUs forecast" + (f" | Accuracy: {acc}%" if acc else "")
        elif slug == "cg-quality-capa-agent":
            n = str(len(output.get("capa_actions", []))) or output.get("exceptions_detected", "?")
            return f"{n} quality events processed"
        elif slug == "kimre-rfq-quote-agent":
            n = output.get("scope_drafts_generated", 0)
            g = output.get("clarification_needed", 0)
            return f"{n} scope drafts generated" + (f" | {g} need clarification" if g else "")
        elif slug == "kimre-quality-compliance-agent":
            n = output.get("flagged", 0)
            c = output.get("orders_checked", 0)
            return f"{c} orders checked — {n} compliance flags"
        elif slug == "kimre-order-notifier-agent":
            n = output.get("notifications_drafted", 0)
            d = output.get("delay_alerts", 0)
            return f"{n} notifications drafted" + (f" | {d} delay alerts" if d else "")
        elif slug == "kimre-retrofit-reorder-agent":
            n = output.get("reorder_candidates", 0)
            return f"{n} reorder candidates identified"
        elif slug == "mfg-predictive-maintenance-agent":
            n = output.get("maintenance_requests_created", 0)
            r = output.get("lines_analysed", 0)
            return f"{r} lines analysed — {n} maintenance requests created"
        elif slug == "ap-invoice-processing":
            auto = output.get("auto_approved", 0)
            review = output.get("approval_required", 0)
            return f"{auto} auto-approved | {review} require approval"
        elif slug == "kimre-marketing-agent":
            mode = output.get("mode", "trade-show-followup")
            if mode == "installed-base-campaign":
                n = output.get("outreach_flagged", 0)
                t = output.get("accounts_scanned", 0)
                return f"{t} accounts scanned — {n} flagged for outreach"
            else:
                n = output.get("drafts_generated", 0)
                return f"{n} follow-up drafts generated"
        elif slug == "kimre-research-agent":
            n = output.get("leads_identified", 0)
            t = output.get("facilities_scanned", 0)
            return f"{t} facilities scanned — {n} leads identified"
        elif slug == "kimre-business-model-agent":
            top = output.get("top_recommendation", "")
            n = output.get("moves_assessed", 0)
            return f"{n} moves assessed — top: {top}"
        elif slug == "github-push-agent":
            s = output.get("summary", {})
            remote_ok = "configured" if s.get("remote_configured") else "not configured"
            return (f"Git: {s.get('files_to_stage', 0)} files to stage, "
                    f"remote {remote_ok}, "
                    f"{s.get('submodules_registered', 0)} submodules registered")
    except Exception:
        pass
    return "Run completed"

# ── API: Run history ──────────────────────────────────────────────────────────
@app.route("/api/runs/<slug>")
def run_history(slug):
    limit = request.args.get("limit", 10, type=int)
    conn = get_db()
    rows = [dict(r) for r in conn.execute("""
        SELECT run_at, outcome, summary, duration_secs, dry_run
        FROM pilot_runs WHERE slug = ? ORDER BY run_at DESC LIMIT ?
    """, (slug, limit)).fetchall()]
    conn.close()
    return jsonify(rows)

# ── API: Approvals ────────────────────────────────────────────────────────────
@app.route("/api/approvals")
def get_approvals():
    persona = request.args.get("persona")
    status = request.args.get("status", "pending")
    conn = get_db()
    query = "SELECT * FROM approvals WHERE decision = ?"
    params = [status]
    if persona:
        # Map persona to blueprint slugs
        persona_slugs = [s for s, p in PERSONA_MAP.items() if p == persona]
        if persona_slugs:
            placeholders = ",".join("?" * len(persona_slugs))
            query += f" AND blueprint_slug IN ({placeholders})"
            params.extend(persona_slugs)
    query += " ORDER BY created_at DESC"
    rows = [dict(r) for r in conn.execute(query, params).fetchall()]
    conn.close()
    for r in rows:
        if r.get("item_details"):
            try:
                r["item_details"] = json.loads(r["item_details"])
            except Exception:
                pass
    return jsonify(rows)

@app.route("/api/approvals/<int:item_id>/decide", methods=["POST"])
def decide_approval(item_id):
    body = request.get_json() or {}
    decision = body.get("decision")
    decided_by = body.get("decided_by", "unknown")
    notes = body.get("notes", "")
    if decision not in ("approved", "rejected", "info_requested"):
        return jsonify({"error": "decision must be: approved | rejected | info_requested"}), 400
    conn = get_db()
    conn.execute("""
        UPDATE approvals SET decision=?, decided_by=?, decision_notes=?, decided_at=datetime('now')
        WHERE id=?
    """, (decision, decided_by, notes, item_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "id": item_id, "decision": decision})

@app.route("/api/approvals/history")
def approval_history():
    conn = get_db()
    rows = [dict(r) for r in conn.execute("""
        SELECT * FROM approvals WHERE decision <> 'pending' ORDER BY decided_at DESC
    """).fetchall()]
    conn.close()
    return jsonify(rows)

# ── API: Recommendations ──────────────────────────────────────────────────────
@app.route("/api/recommendations/<int:run_id>")
def get_recommendations(run_id):
    conn = get_db()
    rows = [dict(r) for r in conn.execute(
        "SELECT * FROM recommendations WHERE run_id = ? ORDER BY id", (run_id,)
    ).fetchall()]
    conn.close()
    return jsonify(rows)


@app.route("/api/recommendations/<int:rec_id>/decide", methods=["POST"])
def decide_recommendation(rec_id):
    data = request.get_json(force=True) or {}
    decision = data.get("decision", "approved")
    decided_by = data.get("decided_by", "operations")
    modified_value = data.get("modified_value", "")
    conn = get_db()
    conn.execute("""
        UPDATE recommendations
        SET decision = ?, decided_by = ?, decided_at = datetime('now'), modified_value = ?
        WHERE id = ?
    """, (decision, decided_by, modified_value, rec_id))
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "id": rec_id, "decision": decision})


@app.route("/api/recommendations/pending")
def pending_recommendations():
    conn = get_db()
    rows = [dict(r) for r in conn.execute("""
        SELECT r.*, p.run_at, p.slug as agent_slug
        FROM recommendations r
        JOIN pilot_runs p ON p.id = r.run_id
        WHERE r.decision = 'pending'
        ORDER BY p.run_at DESC, r.id
    """).fetchall()]
    conn.close()
    return jsonify(rows)


# ── API: Inventory (SAP mock — 20 CG SKUs) ───────────────────────────────────
@app.route('/api/inventory')
def get_inventory():
    """Mock SAP inventory data for 20 CG SKUs"""
    import random
    random.seed(42)  # deterministic
    skus = [
        {"sku_id": "CG-OLV-001", "name": "Olive Oil Extra Virgin 500ml", "category": "Oils", "supplier": "Bonfiglio SpA", "lead_time_days": 8, "unit_cost": 4.20, "reorder_point": 200, "reorder_qty": 500},
        {"sku_id": "CG-OLV-002", "name": "Olive Oil Extra Virgin 1L", "category": "Oils", "supplier": "Bonfiglio SpA", "lead_time_days": 8, "unit_cost": 7.80, "reorder_point": 150, "reorder_qty": 400},
        {"sku_id": "CG-OLV-003", "name": "Olive Oil Light 500ml", "category": "Oils", "supplier": "Bonfiglio SpA", "lead_time_days": 8, "unit_cost": 3.60, "reorder_point": 180, "reorder_qty": 450},
        {"sku_id": "CG-TOM-001", "name": "Tomato Passata 500g", "category": "Sauces", "supplier": "Mutti SRL", "lead_time_days": 5, "unit_cost": 1.20, "reorder_point": 300, "reorder_qty": 800},
        {"sku_id": "CG-TOM-002", "name": "Tomato Puree 200g", "category": "Sauces", "supplier": "Mutti SRL", "lead_time_days": 5, "unit_cost": 0.80, "reorder_point": 400, "reorder_qty": 1000},
        {"sku_id": "CG-PST-001", "name": "Penne Rigate 500g", "category": "Pasta", "supplier": "De Cecco", "lead_time_days": 4, "unit_cost": 0.95, "reorder_point": 500, "reorder_qty": 1200},
        {"sku_id": "CG-PST-002", "name": "Spaghetti No.12 500g", "category": "Pasta", "supplier": "De Cecco", "lead_time_days": 4, "unit_cost": 0.90, "reorder_point": 500, "reorder_qty": 1200},
        {"sku_id": "CG-PST-003", "name": "Fusilli 500g", "category": "Pasta", "supplier": "De Cecco", "lead_time_days": 4, "unit_cost": 0.92, "reorder_point": 400, "reorder_qty": 1000},
        {"sku_id": "CG-VIN-001", "name": "Balsamic Vinegar 250ml", "category": "Condiments", "supplier": "Ponti", "lead_time_days": 10, "unit_cost": 2.40, "reorder_point": 120, "reorder_qty": 300},
        {"sku_id": "CG-VIN-002", "name": "White Wine Vinegar 500ml", "category": "Condiments", "supplier": "Ponti", "lead_time_days": 10, "unit_cost": 1.10, "reorder_point": 150, "reorder_qty": 350},
        {"sku_id": "CG-SAL-001", "name": "Sea Salt Fine 500g", "category": "Seasonings", "supplier": "Salinera Adriatica", "lead_time_days": 6, "unit_cost": 0.65, "reorder_point": 600, "reorder_qty": 1500},
        {"sku_id": "CG-SAL-002", "name": "Sea Salt Coarse 1kg", "category": "Seasonings", "supplier": "Salinera Adriatica", "lead_time_days": 6, "unit_cost": 0.85, "reorder_point": 400, "reorder_qty": 1000},
        {"sku_id": "CG-JAM-001", "name": "Strawberry Preserve 340g", "category": "Preserves", "supplier": "Wilkin & Sons", "lead_time_days": 12, "unit_cost": 2.10, "reorder_point": 200, "reorder_qty": 500},
        {"sku_id": "CG-JAM-002", "name": "Apricot Jam 370g", "category": "Preserves", "supplier": "Wilkin & Sons", "lead_time_days": 12, "unit_cost": 1.95, "reorder_point": 180, "reorder_qty": 450},
        {"sku_id": "CG-HON-001", "name": "Acacia Honey 250g", "category": "Preserves", "supplier": "Mielizia", "lead_time_days": 7, "unit_cost": 3.80, "reorder_point": 150, "reorder_qty": 350},
        {"sku_id": "CG-NUT-001", "name": "Whole Almonds 200g", "category": "Nuts", "supplier": "Almeria Foods", "lead_time_days": 9, "unit_cost": 2.60, "reorder_point": 200, "reorder_qty": 500},
        {"sku_id": "CG-NUT-002", "name": "Walnut Halves 150g", "category": "Nuts", "supplier": "Almeria Foods", "lead_time_days": 9, "unit_cost": 2.90, "reorder_point": 180, "reorder_qty": 450},
        {"sku_id": "CG-BEV-001", "name": "Sparkling Water 1.5L", "category": "Beverages", "supplier": "San Pellegrino", "lead_time_days": 3, "unit_cost": 0.55, "reorder_point": 800, "reorder_qty": 2000},
        {"sku_id": "CG-BEV-002", "name": "Still Water 1.5L", "category": "Beverages", "supplier": "San Pellegrino", "lead_time_days": 3, "unit_cost": 0.45, "reorder_point": 800, "reorder_qty": 2000},
        {"sku_id": "CG-CHO-001", "name": "Dark Chocolate 70% 100g", "category": "Confectionery", "supplier": "Venchi", "lead_time_days": 11, "unit_cost": 1.80, "reorder_point": 250, "reorder_qty": 600},
    ]

    # Generate realistic stock levels — some critical, some low, most OK
    stock_configs = [
        (320, 8.5),   # OLV-001: OK
        (180, 4.8),   # OLV-002: LOW (below reorder)
        (85, 1.8),    # OLV-003: CRITICAL (< 2 days)
        (450, 9.2),   # TOM-001: OK
        (380, 5.8),   # TOM-002: OK
        (620, 7.9),   # PST-001: OK
        (510, 6.5),   # PST-002: OK
        (290, 4.4),   # PST-003: LOW
        (95, 2.3),    # VIN-001: CRITICAL
        (200, 8.1),   # VIN-002: OK
        (820, 8.3),   # SAL-001: OK
        (250, 3.8),   # SAL-002: LOW
        (310, 9.5),   # JAM-001: OK
        (175, 5.9),   # JAM-002: LOW
        (280, 11.2),  # HON-001: OK
        (220, 6.7),   # NUT-001: OK
        (150, 3.2),   # NUT-002: LOW
        (1200, 9.1),  # BEV-001: OK
        (990, 7.5),   # BEV-002: OK
        (180, 4.3),   # CHO-001: LOW
    ]

    result = []
    for sku, (stock, days_cover) in zip(skus, stock_configs):
        if days_cover < 2.5:
            status = "critical"
        elif stock <= sku["reorder_point"]:
            status = "low"
        else:
            status = "ok"

        # Check if there's a pending recommendation for this SKU
        agent_action = None
        if status in ("critical", "low"):
            agent_action = f"PR raised: {sku['reorder_qty']} units @ £{sku['unit_cost']:.2f}"

        result.append({
            **sku,
            "current_stock": stock,
            "days_cover": round(days_cover, 1),
            "status": status,
            "agent_action": agent_action,
            "arrival_date": "2026-03-22" if agent_action else None,
            "demand_history": [random.randint(40, 120) for _ in range(12)],  # 12 weeks
        })

    # Sort: critical first, then low, then ok
    order = {"critical": 0, "low": 1, "ok": 2}
    result.sort(key=lambda x: order[x["status"]])

    return jsonify({"skus": result, "summary": {
        "total": len(result),
        "critical": sum(1 for s in result if s["status"] == "critical"),
        "low": sum(1 for s in result if s["status"] == "low"),
        "ok": sum(1 for s in result if s["status"] == "ok"),
    }})


# ── API: Lifecycle advance ────────────────────────────────────────────────────
@app.route("/api/agents/<slug>/advance", methods=["POST"])
def advance_lifecycle(slug):
    stages = ["blueprint", "scaffolded", "sandbox", "validated", "pilot_ready", "production"]
    conn = get_db()
    current = conn.execute("SELECT lifecycle_stage FROM agent_blueprints WHERE slug=?", (slug,)).fetchone()
    if not current:
        conn.close()
        return jsonify({"error": "Agent not found"}), 404
    current_stage = current["lifecycle_stage"]
    if current_stage not in stages:
        conn.close()
        return jsonify({"error": f"Unknown stage: {current_stage}"}), 400
    idx = stages.index(current_stage)
    if idx >= len(stages) - 1:
        conn.close()
        return jsonify({"error": "Already at production stage"}), 400
    next_stage = stages[idx + 1]
    conn.execute("UPDATE agent_blueprints SET lifecycle_stage=? WHERE slug=?", (next_stage, slug))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "slug": slug, "from_stage": current_stage, "to_stage": next_stage})

# ── API: Contact Enrichment (Proxycurl) ──────────────────────────────────────
@app.route("/api/enrich-contact", methods=["POST"])
def enrich_contact():
    """Enrich a contact's LinkedIn profile via Proxycurl API."""
    import requests as req_lib
    data = request.get_json() or {}
    linkedin_url = data.get("linkedin_url", "").strip()
    client_slug  = data.get("client_slug", "")
    dry_run      = data.get("dry_run", False)

    if not linkedin_url:
        return jsonify({"error": "linkedin_url required"}), 400

    PROXYCURL_API_KEY = os.environ.get("PROXYCURL_API_KEY", "")
    PROXYCURL_URL = "https://nubela.co/proxycurl/api/v2/linkedin"

    # ── Dry-run / no API key fallback ──
    MOCK_PROFILES = {
        "https://www.linkedin.com/in/george-c-pedersen-76231910/": {
            "full_name": "George C. Pedersen",
            "headline": "Founder & Chairman of the Board at Kimre Inc.",
            "occupation": "Founder & Chairman of the Board",
            "summary": "Founded Kimre Inc., a leading manufacturer of mist eliminators, drift eliminators, and coalescers for industrial separation applications worldwide.",
            "city": "Miami", "country_full_name": "United States",
            "skills": ["Mist Elimination", "Industrial Filtration", "Chemical Engineering", "Manufacturing"],
            "experiences": [{"company": "Kimre Inc.", "title": "Founder & Chairman", "starts_at": {"year": 1973}}]
        },
        "https://www.linkedin.com/in/marygaston/": {
            "full_name": "Mary Gaston",
            "headline": "President & Chief Legal Officer at Kimre Inc.",
            "occupation": "President & Chief Legal Officer",
            "summary": "Leads operations, client relationships, and legal affairs at Kimre Inc. Key decision-maker for agent program expansion.",
            "city": "Miami", "country_full_name": "United States",
            "skills": ["Operations Management", "Legal Affairs", "Strategic Planning", "Client Relations"],
            "experiences": [{"company": "Kimre Inc.", "title": "President & CLO", "starts_at": {"year": 2005}}]
        },
        "https://www.linkedin.com/in/chris-pedersen-56ab407/": {
            "full_name": "Chris Pedersen",
            "headline": "Senior Manufacturing Engineer at Kimre Inc.",
            "occupation": "Senior Manufacturing Engineer",
            "summary": "Hands-on fabrication and process engineering. Specialist in mist eliminator construction and BOM accuracy.",
            "city": "Miami", "country_full_name": "United States",
            "skills": ["Manufacturing Engineering", "BOM Management", "FRP Fabrication", "Process Optimization"],
            "experiences": [{"company": "Kimre Inc.", "title": "Senior Manufacturing Engineer", "starts_at": {"year": 2015}}]
        }
    }

    if dry_run or not PROXYCURL_API_KEY:
        # Use mock data — match by URL or return generic mock
        profile_data = MOCK_PROFILES.get(linkedin_url, {
            "full_name": "Contact",
            "headline": "Team Member at Kimre Inc.",
            "occupation": "Engineering",
            "summary": "Kimre Inc. team member.",
            "city": "Miami", "country_full_name": "United States",
            "skills": [], "experiences": []
        })
        source = "dry_run"
    else:
        try:
            resp = req_lib.get(
                PROXYCURL_URL,
                params={"url": linkedin_url, "use_cache": "if-present"},
                headers={"Authorization": f"Bearer {PROXYCURL_API_KEY}"},
                timeout=30
            )
            if resp.status_code != 200:
                return jsonify({"error": f"Proxycurl returned {resp.status_code}", "detail": resp.text}), 502
            profile_data = resp.json()
            source = "proxycurl"
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Build contact record
    skills_list = profile_data.get("skills", [])
    if isinstance(skills_list, list):
        skills_str = ", ".join(str(s) for s in skills_list[:8])
    else:
        skills_str = ""

    exps = profile_data.get("experiences") or []
    company = exps[0].get("company", "") if exps else ""

    contact = {
        "name":         profile_data.get("full_name", ""),
        "title":        profile_data.get("occupation") or profile_data.get("headline", ""),
        "company":      company,
        "location":     f"{profile_data.get('city','')}, {profile_data.get('country_full_name','')}".strip(", "),
        "summary":      profile_data.get("summary", ""),
        "skills":       skills_str,
        "enriched_at":  datetime.utcnow().isoformat() + "Z",
        "source":       source
    }

    # Store in contacts table (if it exists)
    try:
        conn = get_db()
        conn.execute("""
            UPDATE contacts
            SET name=:name, title=:title, company=:company, location=:location,
                summary=:summary, skills=:skills, enriched_json=:enriched_json, enriched_at=:enriched_at
            WHERE linkedin_url=:linkedin_url
        """, {**contact, "enriched_json": json.dumps(profile_data), "linkedin_url": linkedin_url})
        if conn.total_changes == 0:
            # Insert if not found
            conn.execute("""
                INSERT OR IGNORE INTO contacts (client_slug, name, title, company, linkedin_url, location, summary, skills, enriched_json, enriched_at)
                VALUES (:client_slug, :name, :title, :company, :linkedin_url, :location, :summary, :skills, :enriched_json, :enriched_at)
            """, {**contact, "client_slug": client_slug, "linkedin_url": linkedin_url, "enriched_json": json.dumps(profile_data)})
        conn.commit()
        conn.close()
    except Exception:
        pass  # contacts table may not exist yet; return result anyway

    return jsonify({"success": True, "contact": contact, "source": source})


@app.route("/api/contacts")
def get_contacts():
    """Return all contacts for a client slug."""
    client_slug = request.args.get("client_slug", "")
    try:
        conn = get_db()
        if client_slug:
            rows = conn.execute(
                "SELECT * FROM contacts WHERE client_slug=? ORDER BY name", (client_slug,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM contacts ORDER BY client_slug, name").fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  Business Agents Platform — Dashboard Server")
    print("  http://localhost:8500")
    print("=" * 55)
    init_db()
    app.run(host="0.0.0.0", port=8500, debug=False)
