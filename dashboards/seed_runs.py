#!/usr/bin/env python3
"""
seed_runs.py — Populate business_agents.db with rich historical mock data.

Tables seeded:
  - pilot_runs      (30 runs across 3 agents, past 4 weeks)
  - recommendations (2–4 per run, with realistic decisions for older runs)

Schema (from server.py init_db):
  pilot_runs:
    id, run_at, slug, dry_run, outcome, output_file, summary,
    output_json, duration_secs, triggered_by
  recommendations:
    id, run_id, slug, rec_type, item_id, item_label, urgency,
    recommended_action, detail_json, decision, decided_by,
    decided_at, modified_value

Idempotent: uses INSERT OR IGNORE; skips if table already has
sufficient rows (>5 pilot_runs or >20 recommendations).
"""

import json
import random
import sqlite3
from datetime import datetime, timedelta

DB_PATH = "/Users/keith_ai/Documents/Agentic Projects/dashboards/business_agents.db"

# ── Reproducibility ──────────────────────────────────────────────────────────
random.seed(2026)

# ── Date helpers ─────────────────────────────────────────────────────────────
NOW = datetime(2026, 3, 13, 18, 0, 0)
CUTOFF_RECENT = NOW - timedelta(days=7)


def days_ago(n, hour=None, minute=None):
    """Return ISO datetime string for N days ago."""
    h = hour if hour is not None else random.randint(6, 20)
    m = minute if minute is not None else random.randint(0, 59)
    dt = NOW - timedelta(days=n, hours=0, minutes=0)
    dt = dt.replace(hour=h, minute=m, second=0, microsecond=0)
    return dt.isoformat()


def add_hours(iso_str, hours):
    """Add N hours to an ISO datetime string."""
    dt = datetime.fromisoformat(iso_str)
    dt2 = dt + timedelta(hours=hours)
    return dt2.isoformat()


# ── Output JSON generators ────────────────────────────────────────────────────

MATERIALS_ALL = [
    ("CG-OLV-001", "Olive Oil Extra Virgin 500ml"),
    ("CG-OLV-002", "Olive Oil Extra Virgin 1L"),
    ("CG-OLV-003", "Olive Oil Light 500ml"),
    ("CG-VIN-001", "Balsamic Vinegar 250ml"),
    ("CG-VIN-002", "White Wine Vinegar 500ml"),
    ("CG-PST-001", "Penne Rigate 500g"),
    ("CG-PST-002", "Spaghetti No.12 500g"),
    ("CG-PST-003", "Fusilli 500g"),
    ("CG-TOM-001", "Tomato Passata 500g"),
    ("CG-TOM-002", "Tomato Puree 200g"),
    ("CG-SAL-001", "Sea Salt Fine 500g"),
    ("CG-SAL-002", "Sea Salt Coarse 1kg"),
    ("CG-JAM-001", "Strawberry Preserve 340g"),
    ("CG-JAM-002", "Apricot Jam 370g"),
    ("CG-HON-001", "Acacia Honey 250g"),
    ("CG-NUT-001", "Whole Almonds 200g"),
    ("CG-NUT-002", "Walnut Halves 150g"),
    ("CG-BEV-001", "Sparkling Water 1.5L"),
    ("CG-BEV-002", "Still Water 1.5L"),
    ("CG-CHO-001", "Dark Chocolate 70% 100g"),
]

PRIORITIES = ["HIGH_PRIORITY", "STANDARD", "STANDARD", "STANDARD"]
CONFIDENCES = ["HIGH", "HIGH", "MEDIUM", "LOW"]
ISSUE_TYPES = [
    "contamination_risk",
    "temperature_deviation",
    "pH_out_of_spec",
    "viscosity_deviation",
    "foreign_body_risk",
    "batch_record_incomplete",
]
CAPA_ACTIONS = {
    "contamination_risk":       "Halt line, deep clean, re-test before restart",
    "temperature_deviation":    "Recalibrate thermostat, log deviation",
    "pH_out_of_spec":           "Replace buffer solution, recalibrate, re-test batch",
    "viscosity_deviation":      "Adjust mixing parameters, monitor next 3 batches",
    "foreign_body_risk":        "Isolate batch, full inspection, report to QA manager",
    "batch_record_incomplete":  "Complete records within 2 hours, notify compliance officer",
}
SEVERITIES = ["high", "medium", "medium", "low"]


def _pr_number(run_idx, pr_idx):
    return f"PR-2026-{(run_idx * 10 + pr_idx):04d}"


def _qe_number(run_idx, ev_idx):
    return f"QE-2026-{(run_idx * 10 + ev_idx):04d}"


def gen_replenishment_output(run_idx):
    """Generate realistic replenishment agent output JSON."""
    # Pick 2–4 materials that need PRs
    n_prs = random.randint(2, 4)
    chosen = random.sample(MATERIALS_ALL, n_prs)
    prs = []
    high_flags = []
    for i, (mat_id, _) in enumerate(chosen):
        priority = random.choice(PRIORITIES)
        qty = random.randint(200, 800)
        prs.append({
            "pr_number": _pr_number(run_idx, i + 1),
            "material_id": mat_id,
            "quantity": qty,
            "priority": priority,
            "status": "created",
        })
        if priority == "HIGH_PRIORITY":
            high_flags.append(mat_id)

    high_count = len(high_flags)
    return {
        "items_analysed": 20,
        "prs_created": prs,
        "high_priority_flags": high_flags,
        "total_prs": len(prs),
        "high_priority_count": high_count,
    }


def gen_replenishment_output_failed():
    """Minimal output for a failed run."""
    return None


def gen_replenishment_output_partial(run_idx):
    """Partial output for a partial run — fewer PRs, some errors."""
    n_prs = 1
    chosen = random.sample(MATERIALS_ALL, n_prs)
    prs = []
    for i, (mat_id, _) in enumerate(chosen):
        prs.append({
            "pr_number": _pr_number(run_idx, i + 1),
            "material_id": mat_id,
            "quantity": random.randint(100, 300),
            "priority": "STANDARD",
            "status": "created",
        })
    return {
        "items_analysed": 20,
        "prs_created": prs,
        "high_priority_flags": [],
        "total_prs": len(prs),
        "high_priority_count": 0,
        "partial_failure": True,
        "error_detail": "SAP connection timeout on 3 materials — partial PRs created",
    }


def gen_forecast_output(run_idx):
    """Generate realistic demand forecast agent output JSON."""
    n_forecasts = random.randint(4, 6)
    chosen = random.sample(MATERIALS_ALL, n_forecasts)
    forecasts = []
    top_growing = []
    demand_cliffs = []

    for mat_id, desc in chosen:
        conf = random.choice(CONFIDENCES)
        growth = round(random.uniform(-15.0, 20.0), 1)
        cliff = (growth < -10.0) and (conf == "LOW") and random.random() < 0.4
        sma = round(random.uniform(50.0, 300.0), 1)
        projection = round(sma * (1 + growth / 100), 1)

        forecasts.append({
            "material_id": mat_id,
            "description": desc,
            "confidence": conf,
            "growth_rate_pct": growth,
            "demand_cliff": cliff,
            "sma_last4": sma,
            "trend_projection": projection,
        })
        if growth > 10.0:
            top_growing.append(mat_id)
        if cliff:
            demand_cliffs.append(mat_id)

    cliffs_count = len(demand_cliffs)
    return {
        "items_analysed": 20,
        "forecasts": forecasts,
        "top_growing": top_growing[:3],
        "demand_cliffs": demand_cliffs,
        "forecast_horizon_weeks": 4,
    }


def gen_capa_output(run_idx, partial=False):
    """Generate realistic quality CAPA agent output JSON."""
    n_events = random.randint(2, 3) if not partial else 1
    events = []
    lines = ["LINE-01", "LINE-02", "LINE-03", "LINE-04", "LINE-05"]
    auto_resolved = 0

    for i in range(n_events):
        issue = random.choice(ISSUE_TYPES)
        sev = random.choice(SEVERITIES)
        line = random.choice(lines)
        mr_created = sev in ("high", "medium")
        authority = "MEDIUM" if sev == "high" else ("LOW" if sev == "medium" else "INFORMATIONAL")
        events.append({
            "event_id": _qe_number(run_idx, i + 1),
            "line_id": line,
            "severity": sev,
            "issue_type": issue,
            "capa_action": CAPA_ACTIONS[issue],
            "authority": authority,
            "mr_created": mr_created,
        })
        if sev == "low":
            auto_resolved += 1

    return {
        "events_scanned": 12,
        "capa_actions": events,
        "oee_mr_actions": [],
        "total_events": n_events,
        "auto_resolved": auto_resolved,
    }


# ── Summary builders ──────────────────────────────────────────────────────────

def replenishment_summary(output, outcome):
    if outcome == "failed":
        return "Agent run failed — SAP connection error"
    if outcome == "partial":
        prs = output.get("prs_created", [])
        return f"{len(prs)} PRs created (partial — SAP timeout on remaining items)"
    prs = output.get("prs_created", [])
    hp = output.get("high_priority_count", 0)
    suffix = f", {hp} high priority" if hp else ""
    return f"{len(prs)} PRs created{suffix}"


def forecast_summary(output):
    n = output.get("items_analysed", 20)
    cliffs = len(output.get("demand_cliffs", []))
    top = len(output.get("top_growing", []))
    parts = [f"{n} items forecast"]
    if cliffs:
        parts.append(f"{cliffs} demand cliff{'s' if cliffs > 1 else ''} detected")
    if top:
        parts.append(f"{top} growing SKU{'s' if top > 1 else ''}")
    return ", ".join(parts)


def capa_summary(output, outcome):
    if outcome == "partial":
        actions = output.get("capa_actions", [])
        return f"{len(actions)} CAPA action raised (partial scan — system latency)"
    actions = output.get("capa_actions", [])
    high_sev = sum(1 for a in actions if a.get("severity") == "high")
    suffix = f", {high_sev} high severity" if high_sev else ""
    return f"{len(actions)} CAPA actions raised{suffix}"


# ── Recommendation generators ─────────────────────────────────────────────────

def recs_for_replenishment(run_id, slug, output):
    """Generate recommendations from replenishment output."""
    recs = []
    if not output:
        return recs
    for pr in output.get("prs_created", []):
        mat_id = pr.get("material_id", "")
        priority = pr.get("priority", "STANDARD")
        urgency = "high" if priority == "HIGH_PRIORITY" else "medium"
        qty = pr.get("quantity", 0)
        action = f"Create PO for {qty} units of {mat_id}"
        recs.append({
            "run_id": run_id,
            "slug": slug,
            "rec_type": "pr_order",
            "item_id": mat_id,
            "item_label": mat_id,
            "urgency": urgency,
            "recommended_action": action,
            "detail_json": json.dumps(pr),
            "decided_by": "operations",
        })
    return recs


def recs_for_forecast(run_id, slug, output):
    """Generate recommendations from forecast output."""
    recs = []
    if not output:
        return recs
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
        mat_id = fc.get("material_id", "")
        label = fc.get("description", mat_id)
        growth = fc.get("growth_rate_pct", 0)
        if cliff:
            action = f"Alert: demand cliff detected — review supply plan for {mat_id}"
        elif growth > 10:
            action = f"Monitor: {growth:.1f}% growth trend — consider increasing safety stock"
        elif growth < -10:
            action = f"Monitor: {abs(growth):.1f}% demand decline — review reorder parameters"
        else:
            action = f"Stable: {growth:.1f}% trend — no action required"
        recs.append({
            "run_id": run_id,
            "slug": slug,
            "rec_type": "forecast_signal",
            "item_id": mat_id,
            "item_label": label,
            "urgency": urgency,
            "recommended_action": action,
            "detail_json": json.dumps(fc),
            "decided_by": "operations",
        })
    return recs


def recs_for_capa(run_id, slug, output):
    """Generate recommendations from CAPA output."""
    recs = []
    if not output:
        return recs
    for ca in output.get("capa_actions", []):
        sev = ca.get("severity", "medium").lower()
        urgency = sev if sev in ("low", "medium", "high", "critical") else "medium"
        item_id = ca.get("event_id", ca.get("line_id", ""))
        issue = ca.get("issue_type", "quality_event")
        line = ca.get("line_id", "")
        label = f"{issue.replace('_', ' ').title()} — {line}"
        action = ca.get("capa_action", "Investigate quality event")
        recs.append({
            "run_id": run_id,
            "slug": slug,
            "rec_type": "capa_action",
            "item_id": item_id,
            "item_label": label,
            "urgency": urgency,
            "recommended_action": action,
            "detail_json": json.dumps(ca),
            "decided_by": "compliance",
        })
    return recs


# ── Decision assignment ───────────────────────────────────────────────────────

def assign_decision(run_at_str, rec, idx):
    """
    For runs older than 7 days: 70% approved, 20% rejected, 10% pending.
    For recent runs (last 7 days): 60% pending, 40% approved.
    """
    run_dt = datetime.fromisoformat(run_at_str)
    is_old = run_dt < CUTOFF_RECENT

    r = random.random()
    if is_old:
        if r < 0.70:
            decision = "approved"
        elif r < 0.90:
            decision = "rejected"
        else:
            decision = "pending"
    else:
        if r < 0.60:
            decision = "pending"
        else:
            decision = "approved"

    decided_at = None
    if decision != "pending":
        offset_hours = random.randint(2, 8)
        decided_at = add_hours(run_at_str, offset_hours)

    return decision, decided_at


# ── DB setup ──────────────────────────────────────────────────────────────────

def ensure_tables(conn):
    """Create tables if they don't exist (mirrors server.py init_db)."""
    conn.executescript("""
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


# ── Main seeding ──────────────────────────────────────────────────────────────

def seed():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    ensure_tables(conn)
    cur = conn.cursor()

    # ── Guard: skip if already seeded ────────────────────────────────────────
    pilot_count = cur.execute("SELECT COUNT(*) FROM pilot_runs").fetchone()[0]
    rec_count   = cur.execute("SELECT COUNT(*) FROM recommendations").fetchone()[0]

    if pilot_count > 5:
        print(f"[seed] pilot_runs already has {pilot_count} rows — skipping pilot_runs seed.")
        seed_runs_flag = False
    else:
        print(f"[seed] pilot_runs has {pilot_count} rows — seeding 30 historical runs.")
        seed_runs_flag = True

    if rec_count > 20:
        print(f"[seed] recommendations already has {rec_count} rows — skipping recommendations seed.")
        seed_recs_flag = False
    else:
        print(f"[seed] recommendations has {rec_count} rows — seeding recommendations.")
        seed_recs_flag = True

    if not seed_runs_flag and not seed_recs_flag:
        print("[seed] Nothing to do. DB already seeded.")
        conn.close()
        return

    # ── Build run schedule ────────────────────────────────────────────────────
    # cg-replenishment-pr-agent: 12 runs — 10 success, 1 partial, 1 failed
    # Spread over 4 weeks: roughly 3/week
    replenishment_runs = []
    outcomes_repl = (
        ["success"] * 10 + ["partial"] + ["failed"]
    )
    random.shuffle(outcomes_repl)

    # Spread 12 runs over days 1..28 (at least 1 per ~2.3 days)
    repl_days = sorted(random.sample(range(1, 29), 12))
    for idx, (d, outcome) in enumerate(zip(repl_days, outcomes_repl)):
        run_at = days_ago(d)
        duration_secs = round(random.uniform(2.8, 4.2), 2)
        if outcome == "success":
            output = gen_replenishment_output(idx)
        elif outcome == "partial":
            output = gen_replenishment_output_partial(idx)
        else:
            output = None
        summary = replenishment_summary(output, outcome)
        replenishment_runs.append({
            "slug": "cg-replenishment-pr-agent",
            "run_at": run_at,
            "outcome": outcome,
            "output": output,
            "summary": summary,
            "duration_secs": duration_secs,
        })

    # cg-demand-forecast-agent: 10 runs — all success
    forecast_runs = []
    forecast_days = sorted(random.sample(range(1, 29), 10))
    for idx, d in enumerate(forecast_days):
        run_at = days_ago(d)
        duration_secs = round(random.uniform(3.1, 5.4), 2)
        output = gen_forecast_output(idx)
        summary = forecast_summary(output)
        forecast_runs.append({
            "slug": "cg-demand-forecast-agent",
            "run_at": run_at,
            "outcome": "success",
            "output": output,
            "summary": summary,
            "duration_secs": duration_secs,
        })

    # cg-quality-capa-agent: 8 runs — 7 success, 1 partial
    capa_runs = []
    outcomes_capa = ["success"] * 7 + ["partial"]
    random.shuffle(outcomes_capa)
    capa_days = sorted(random.sample(range(1, 29), 8))
    for idx, (d, outcome) in enumerate(zip(capa_days, outcomes_capa)):
        run_at = days_ago(d)
        duration_secs = round(random.uniform(2.2, 3.8), 2)
        output = gen_capa_output(idx, partial=(outcome == "partial"))
        summary = capa_summary(output, outcome)
        capa_runs.append({
            "slug": "cg-quality-capa-agent",
            "run_at": run_at,
            "outcome": outcome,
            "output": output,
            "summary": summary,
            "duration_secs": duration_secs,
        })

    all_runs = replenishment_runs + forecast_runs + capa_runs
    all_runs.sort(key=lambda r: r["run_at"])

    # ── Insert pilot_runs ─────────────────────────────────────────────────────
    inserted_runs = 0
    run_id_map = {}  # index -> actual DB id

    if seed_runs_flag:
        for i, run in enumerate(all_runs):
            output_json_str = json.dumps(run["output"]) if run["output"] else None
            cur.execute("""
                INSERT OR IGNORE INTO pilot_runs
                    (run_at, slug, dry_run, outcome, output_file, summary, output_json,
                     duration_secs, triggered_by)
                VALUES (?, ?, 1, ?, NULL, ?, ?, ?, 'scheduled')
            """, (
                run["run_at"],
                run["slug"],
                run["outcome"],
                run["summary"],
                output_json_str,
                run["duration_secs"],
            ))
            run_id_map[i] = cur.lastrowid
            inserted_runs += 1

        conn.commit()
        print(f"[seed] Inserted {inserted_runs} pilot_runs rows.")
    else:
        # Still need run IDs if we're going to seed recs
        existing = cur.execute(
            "SELECT id, run_at, slug FROM pilot_runs ORDER BY run_at"
        ).fetchall()
        for i, row in enumerate(existing):
            run_id_map[i] = row["id"]

    # ── Insert recommendations ────────────────────────────────────────────────
    inserted_recs = 0

    if seed_recs_flag:
        # Re-fetch run IDs reliably
        db_runs = cur.execute(
            "SELECT id, run_at, slug, output_json, outcome FROM pilot_runs ORDER BY run_at"
        ).fetchall()

        for db_run in db_runs:
            run_id  = db_run["id"]
            run_at  = db_run["run_at"]
            slug    = db_run["slug"]
            outcome = db_run["outcome"]
            output_str = db_run["output_json"]
            output = json.loads(output_str) if output_str else None

            if slug == "cg-replenishment-pr-agent":
                recs = recs_for_replenishment(run_id, slug, output)
            elif slug == "cg-demand-forecast-agent":
                recs = recs_for_forecast(run_id, slug, output)
            elif slug == "cg-quality-capa-agent":
                recs = recs_for_capa(run_id, slug, output)
            else:
                recs = []

            for idx, rec in enumerate(recs):
                decision, decided_at = assign_decision(run_at, rec, idx)
                cur.execute("""
                    INSERT OR IGNORE INTO recommendations
                        (run_id, slug, rec_type, item_id, item_label, urgency,
                         recommended_action, detail_json, decision, decided_by,
                         decided_at, modified_value)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
                """, (
                    rec["run_id"],
                    rec["slug"],
                    rec["rec_type"],
                    rec["item_id"],
                    rec["item_label"],
                    rec["urgency"],
                    rec["recommended_action"],
                    rec["detail_json"],
                    decision,
                    rec["decided_by"],
                    decided_at,
                ))
                inserted_recs += 1

        conn.commit()
        print(f"[seed] Inserted {inserted_recs} recommendations rows.")

    conn.close()

    # ── Final summary ─────────────────────────────────────────────────────────
    print("\n[seed] Done. Final state:")
    conn2 = sqlite3.connect(DB_PATH)
    rows = conn2.execute(
        "SELECT slug, COUNT(*) as cnt FROM pilot_runs GROUP BY slug ORDER BY slug"
    ).fetchall()
    for r in rows:
        print(f"  pilot_runs  | {r[0]:<40} | {r[1]:>3} runs")

    rows2 = conn2.execute(
        "SELECT decision, COUNT(*) as cnt FROM recommendations GROUP BY decision ORDER BY decision"
    ).fetchall()
    for r in rows2:
        print(f"  recs        | decision={r[0]:<12} | {r[1]:>3}")

    total_recs = conn2.execute("SELECT COUNT(*) FROM recommendations").fetchone()[0]
    print(f"  recs total  | {total_recs}")
    conn2.close()


if __name__ == "__main__":
    seed()
