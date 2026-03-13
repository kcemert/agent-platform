#!/usr/bin/env python3
"""
score_client.py — Business Agents Platform · Epic 8
=====================================================
Scores all 127 APQC processes in the database for relevance to a given client
profile exported from the onboarding questionnaire.

Usage:
    python3 client-onboarding/score_client.py client-onboarding/example-client.json

Output:
    client-onboarding/outputs/<company-name>-opportunity-matrix.json
    Summary table printed to stdout.
"""

import json
import os
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

# ── Configuration ────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = SCRIPT_DIR.parent
DB_PATH = WORKSPACE_ROOT / "business-agents" / "business_agents.db"
OUTPUT_DIR = SCRIPT_DIR / "outputs"

# ── Industry name → DB code mapping ──────────────────────────────────────────

INDUSTRY_MAP = {
    "Consumer Goods":     "CG",
    "Manufacturing":      "MFG",
    "Pharmaceutical":     "PHARMA",
    "Financial Services": "FS",
    "Retail":             "RETAIL",
}

# ── System → function_id affinity ────────────────────────────────────────────
# Maps a system category + specific system to the function IDs they most
# strongly support (used for +1 system match bonus).

SYSTEM_FUNCTION_MAP = {
    # ERP systems — span finance, procurement, manufacturing
    "SAP S/4HANA":           [4, 9, 10],
    "Oracle ERP Cloud":      [4, 9, 10],
    "Microsoft Dynamics":    [4, 9, 7],
    # CRM systems — sales, customer service, marketing
    "Salesforce":            [3, 6],
    "SAP CRM":               [3, 6],
    "Microsoft Dynamics CRM":[3, 6],
    # MES — manufacturing execution
    "SAP ME/MII":            [4],
    "Siemens Opcenter":      [4],
    "Rockwell FactoryTalk":  [4],
    # Supply chain planning
    "SAP IBP":               [4],
    "Kinaxis":               [4],
    "o9 Solutions":          [4, 1],
}

# ── Pain point → (function_ids, keyword_tags) mapping ────────────────────────

PAIN_FUNCTION_MAP = {
    "manual_data_reconciliation":    [8, 9],
    "slow_procurement":              [4, 9],
    "poor_forecast_accuracy":        [1, 3, 4],
    "quality_compliance_burden":     [4, 2, 11],
    "limited_production_visibility": [4, 10],
    "talent_gap_analytics":          [7, 8],
    "slow_customer_response":        [6, 3],
    "regulatory_reporting_burden":   [2, 11],
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_profile(path: str) -> dict:
    """Load and validate a client profile JSON file."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        sys.exit(f"[ERROR] Profile file not found: {path}")
    except json.JSONDecodeError as exc:
        sys.exit(f"[ERROR] Invalid JSON in profile: {exc}")

    # Basic structure validation
    if "company" not in data:
        sys.exit("[ERROR] Profile missing 'company' section.")
    return data


def get_db(db_path: Path) -> sqlite3.Connection:
    """Open the SQLite database with row-factory for dict access."""
    if not db_path.exists():
        sys.exit(f"[ERROR] Database not found: {db_path}")
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def get_industry_id(conn: sqlite3.Connection, industry_name: str) -> Optional[int]:
    """Resolve a human-readable industry name to its DB id."""
    code = INDUSTRY_MAP.get(industry_name)
    if not code:
        return None
    row = conn.execute(
        "SELECT id FROM industries WHERE code = ?", (code,)
    ).fetchone()
    return row["id"] if row else None


def fetch_all_processes(conn: sqlite3.Connection) -> List[dict]:
    """Return all 127 processes with function name."""
    rows = conn.execute("""
        SELECT p.id,
               p.apqc_code,
               p.name,
               p.function_id,
               p.level,
               p.is_universal,
               f.name AS function_name
        FROM   processes p
        JOIN   functions f ON p.function_id = f.id
        ORDER  BY p.function_id, p.apqc_code
    """).fetchall()
    return [dict(r) for r in rows]


def fetch_industry_process_ids(conn: sqlite3.Connection, industry_id: int) -> Set[int]:
    """Return set of process IDs linked to a specific industry."""
    rows = conn.execute(
        "SELECT process_id FROM industry_processes WHERE industry_id = ?",
        (industry_id,)
    ).fetchall()
    return {r["process_id"] for r in rows}


def fetch_agent_opportunity_scores(conn: sqlite3.Connection) -> Dict[int, float]:
    """
    Return a dict mapping process_id → max agent opportunity score.
    Score = max(feasibility + value) across all industry entries for that process.
    Scaled to 1-5 by dividing by 2 (raw max is 10).
    """
    rows = conn.execute("""
        SELECT process_id,
               MAX(feasibility + value) AS raw_score
        FROM   process_agent_actions
        GROUP  BY process_id
    """).fetchall()
    result = {}
    for r in rows:
        raw = r["raw_score"] or 0
        # Map raw 0-10 → 0-5, rounded to nearest 0.5
        scaled = round((raw / 10) * 5 * 2) / 2
        result[r["process_id"]] = scaled
    return result


# ── Scoring Engine ────────────────────────────────────────────────────────────

def score_processes(
    processes: List[dict],
    profile: dict,
    industry_process_ids: Set[int],
    agent_opportunity: Dict[int, float],
) -> List[dict]:
    """
    Score every process for the client and return the list sorted by
    composite_score descending.

    Scoring rubric
    ──────────────
    • Industry match  (+3)   Process is linked to the client's industry in industry_processes
    • Function match  (+2)   Client selected this APQC function in scope
    • Pain point match(+1 each) Pain points map to process's function (capped at +4)
    • System match    (+1)   Client has a system that supports the process's function
    • Multiplier             composite * agent_opportunity_score (1-5 scale)
                             Processes with no score data get multiplier = 2.5 (neutral)
    """
    client_functions = set(profile.get("functions_in_scope", []))

    # Build set of all system names the client has
    systems_raw = profile.get("systems", {})
    client_systems: set[str] = set()
    for key in ("erp", "crm", "mes", "supply_chain_planning"):
        for s in systems_raw.get(key, []):
            if s and s.lower() != "none":
                client_systems.add(s)

    # Build set of function IDs supported by client's systems
    system_supported_functions: Set[int] = set()
    for sys_name in client_systems:
        for fid in SYSTEM_FUNCTION_MAP.get(sys_name, []):
            system_supported_functions.add(fid)

    # Build set of function IDs implicated by pain points
    pain_function_boost: Dict[int, int] = {}  # function_id → count of pain points
    for pain in profile.get("pain_points", {}).get("selected", []):
        for fid in PAIN_FUNCTION_MAP.get(pain, []):
            pain_function_boost[fid] = pain_function_boost.get(fid, 0) + 1

    scored = []
    for proc in processes:
        pid = proc["id"]
        fid = proc["function_id"]

        breakdown = {}

        # Industry match
        ind_score = 3 if pid in industry_process_ids else 0
        breakdown["industry_match"] = ind_score

        # Function match
        func_score = 2 if fid in client_functions else 0
        breakdown["function_match"] = func_score

        # Pain point match (cap at 4)
        pain_score = min(pain_function_boost.get(fid, 0), 4)
        breakdown["pain_point_match"] = pain_score

        # System match
        sys_score = 1 if fid in system_supported_functions else 0
        breakdown["system_match"] = sys_score

        # Base score before multiplier
        base = ind_score + func_score + pain_score + sys_score
        breakdown["base_score"] = base

        # Agent opportunity score (1-5 scale; neutral 2.5 if no data)
        ao_score = agent_opportunity.get(pid, 2.5)
        breakdown["agent_opportunity_score"] = ao_score

        # Composite: base × (ao_score / 5) × 10, normalised so max ≈ 100
        # This keeps high-automation processes at the top even with moderate base scores
        composite = round(base * (ao_score / 5) * 10, 2)
        breakdown["composite_score"] = composite

        scored.append({
            "process_id": pid,
            "apqc_code": proc["apqc_code"],
            "process_name": proc["name"],
            "function_id": fid,
            "function_name": proc["function_name"],
            "level": proc["level"],
            "score_breakdown": breakdown,
            "composite_score": composite,
        })

    scored.sort(key=lambda x: (-x["composite_score"], -x["score_breakdown"]["base_score"]))
    return scored


# ── Output Helpers ────────────────────────────────────────────────────────────

def print_summary_table(top30: List[dict], company_name: str) -> None:
    """Print a formatted summary table to stdout."""
    line = "─" * 110
    print(f"\n{'':=<110}")
    print(f"  Business Agents Platform — Opportunity Matrix")
    print(f"  Client: {company_name}")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'':=<110}\n")

    header = (
        f"{'Rank':<5} {'APQC':<10} {'Process Name':<42} {'Function':<34} "
        f"{'Base':>5} {'AO':>4} {'Score':>7}"
    )
    print(header)
    print(line)

    for i, p in enumerate(top30, 1):
        bd = p["score_breakdown"]
        name = p["process_name"][:40] + ("…" if len(p["process_name"]) > 40 else "")
        func = p["function_name"][:32] + ("…" if len(p["function_name"]) > 32 else "")
        print(
            f"  {i:<3} {p['apqc_code']:<10} {name:<42} {func:<34} "
            f"{bd['base_score']:>5} {bd['agent_opportunity_score']:>4} {p['composite_score']:>7.1f}"
        )

    print(f"\n  Showing top {len(top30)} of 127 scored processes.")
    print(f"\n  Score breakdown key:")
    print(f"    Base = Industry match (+3) + Function match (+2) + Pain point match (+1 each, cap 4) + System match (+1)")
    print(f"    AO   = Agent Opportunity Score (1-5 scale from DB)")
    print(f"    Score = Base × (AO/5) × 10\n")


def write_output(top30: List[dict], profile: dict, output_path: Path) -> None:
    """Write the opportunity matrix JSON to disk."""
    output = {
        "meta": {
            "generated_at": datetime.now().isoformat(),
            "scorer_version": "Epic-8-v1",
            "client": profile.get("company", {}).get("name", "Unknown"),
            "industry": profile.get("company", {}).get("industry", "Unknown"),
            "functions_in_scope": profile.get("functions_in_scope", []),
            "systems": profile.get("systems", {}),
            "pain_points": profile.get("pain_points", {}).get("selected", []),
        },
        "scoring_config": {
            "industry_match_points": 3,
            "function_match_points": 2,
            "pain_point_match_points": "1 per pain point (max 4)",
            "system_match_points": 1,
            "composite_formula": "base × (agent_opportunity_score / 5) × 10",
        },
        "opportunity_matrix": top30,
        "total_processes_scored": 127,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(output, fh, indent=2)
    print(f"\n  Output written → {output_path}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit("Usage: python3 score_client.py <client-profile.json>")

    profile_path = sys.argv[1]
    profile = load_profile(profile_path)

    company = profile.get("company", {})
    company_name = company.get("name", "Unknown")
    industry_name = company.get("industry", "")

    print(f"\n[score_client] Loaded profile for: {company_name}")
    print(f"[score_client] Industry: {industry_name}")
    print(f"[score_client] Functions in scope: {profile.get('functions_in_scope', [])}")
    print(f"[score_client] Pain points: {profile.get('pain_points', {}).get('selected', [])}")
    print(f"[score_client] Connecting to database: {DB_PATH}")

    conn = get_db(DB_PATH)

    industry_id = get_industry_id(conn, industry_name)
    if industry_id is None:
        print(f"[WARN] Industry '{industry_name}' not found in DB — industry match scoring disabled.")
        industry_process_ids: set[int] = set()
    else:
        industry_process_ids = fetch_industry_process_ids(conn, industry_id)
        print(f"[score_client] Industry '{industry_name}' → {len(industry_process_ids)} industry-linked processes")

    processes = fetch_all_processes(conn)
    print(f"[score_client] Loaded {len(processes)} processes from database")

    agent_opportunity = fetch_agent_opportunity_scores(conn)
    print(f"[score_client] Agent opportunity scores loaded for {len(agent_opportunity)} processes")

    conn.close()

    # Score all processes
    scored = score_processes(processes, profile, industry_process_ids, agent_opportunity)
    top30 = scored[:30]

    # Print summary table
    print_summary_table(top30, company_name)

    # Write output JSON
    company_slug = re.sub(r"[^a-z0-9]+", "-", company_name.lower()).strip("-")
    output_filename = f"{company_slug}-opportunity-matrix.json"
    output_path = OUTPUT_DIR / output_filename
    write_output(top30, profile, output_path)


if __name__ == "__main__":
    main()
