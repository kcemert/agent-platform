#!/usr/bin/env python3
"""
seed_clients.py — Seed clients table in business_agents.db

Creates the clients table and seeds all 3 client records.
Idempotent: safe to run multiple times.

Usage: python3 clients/seed_clients.py
"""

import sqlite3
import json
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
DB_PATH   = WORKSPACE / "business-agents" / "business_agents.db"

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS clients (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    slug                  TEXT UNIQUE NOT NULL,
    name                  TEXT NOT NULL,
    industry_code         TEXT,
    size_tier             TEXT,
    business_model        TEXT,
    regulatory_score      INTEGER,
    integration_tier      TEXT,
    data_readiness_score  INTEGER,
    engagement_tier       TEXT,
    pilot_agent_slug      TEXT,
    pilot_year1_value_gbp INTEGER,
    hours_recoverable_wk  INTEGER,
    annual_value_gbp      INTEGER,
    contact_name          TEXT,
    contact_email         TEXT,
    profile_json          TEXT,
    created_at            TEXT DEFAULT (datetime('now'))
);
"""

CLIENTS = [
    {
        "slug": "kimre",
        "name": "Kimre Inc.",
        "industry_code": "MFG",
        "size_tier": "MID",
        "business_model": "ETO",
        "regulatory_score": 4,
        "integration_tier": "T2",
        "data_readiness_score": 14,
        "engagement_tier": "Pilot",
        "pilot_agent_slug": "kimre-material-requisition-agent",
        "pilot_year1_value_gbp": 24000,
        "hours_recoverable_wk": 34,
        "annual_value_gbp": 190000,
        "contact_name": "Mary Gaston",
        "contact_email": "mary@kimre.com",
    },
    {
        "slug": "precisionparts",
        "name": "Precision Parts Co.",
        "industry_code": "MFG",
        "size_tier": "MID",
        "business_model": "MTS",
        "regulatory_score": 3,
        "integration_tier": "T2",
        "data_readiness_score": 17,
        "engagement_tier": "Pilot",
        "pilot_agent_slug": "mfg-inventory-replenishment-agent",
        "pilot_year1_value_gbp": 18000,
        "hours_recoverable_wk": 18,
        "annual_value_gbp": 74000,
        "contact_name": "Sarah Mitchell",
        "contact_email": "s.mitchell@precisionparts.com",
    },
    {
        "slug": "meridianbank",
        "name": "Meridian Community Bank",
        "industry_code": "FS",
        "size_tier": "MID",
        "business_model": "Service",
        "regulatory_score": 5,
        "integration_tier": "T2",
        "data_readiness_score": 19,
        "engagement_tier": "Pilot",
        "pilot_agent_slug": "fs-aml-alert-triage-agent",
        "pilot_year1_value_gbp": 35000,
        "hours_recoverable_wk": 28,
        "annual_value_gbp": 127000,
        "contact_name": "James Whitfield",
        "contact_email": "j.whitfield@meridianbank.com",
    },
]

def seed():
    print(f"Connecting to: {DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(CREATE_TABLE)
    conn.commit()

    existing = {row[0] for row in conn.execute("SELECT slug FROM clients").fetchall()}

    inserted = 0
    for client in CLIENTS:
        if client["slug"] in existing:
            print(f"  ↩ {client['name']} already exists — skipping")
            continue

        # Load full profile JSON if available
        profile_path = Path(__file__).parent / client["slug"] / "profile.json"
        profile_json = None
        if profile_path.exists():
            with open(profile_path) as f:
                profile_json = f.read()

        conn.execute("""
            INSERT INTO clients (slug, name, industry_code, size_tier, business_model,
                regulatory_score, integration_tier, data_readiness_score, engagement_tier,
                pilot_agent_slug, pilot_year1_value_gbp, hours_recoverable_wk, annual_value_gbp,
                contact_name, contact_email, profile_json)
            VALUES (:slug, :name, :industry_code, :size_tier, :business_model,
                :regulatory_score, :integration_tier, :data_readiness_score, :engagement_tier,
                :pilot_agent_slug, :pilot_year1_value_gbp, :hours_recoverable_wk, :annual_value_gbp,
                :contact_name, :contact_email, :profile_json)
        """, {**client, "profile_json": profile_json})
        print(f"  + Seeded: {client['name']}")
        inserted += 1

    conn.commit()
    conn.close()
    print(f"\nDone. {inserted} new clients seeded. Total: {len(CLIENTS)} clients in DB.")

if __name__ == "__main__":
    seed()
