"""
Pattern Registry Loader
Resolves patterns using override hierarchy: defaults -> industry -> client
Part of the Agent Mind implementation.
"""

import json
import os
from pathlib import Path
from typing import Optional

PATTERNS_DIR = Path(__file__).parent


def load_json(path: Path) -> list:
    """Load a JSON pattern file, return empty list if not found."""
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


def load_patterns(industry: Optional[str] = None, client_slug: Optional[str] = None) -> list:
    """
    Load and merge patterns using the override hierarchy:
    1. Platform defaults (always loaded)
    2. Industry-specific patterns (if industry provided)
    3. Client-specific overrides (if client_slug provided)

    Client overrides with same pattern_id supersede defaults.
    """
    # Tier 1: Platform defaults
    patterns = {p["pattern_id"]: p for p in load_json(PATTERNS_DIR / "defaults.json")}

    # Tier 2: Industry-specific
    if industry:
        industry_file = PATTERNS_DIR / "industries" / f"{industry.lower()}.json"
        for p in load_json(industry_file):
            patterns[p["pattern_id"]] = p  # override or add

    # Tier 3: Client-specific
    if client_slug:
        client_file = PATTERNS_DIR / "clients" / f"{client_slug}.json"
        for p in load_json(client_file):
            patterns[p["pattern_id"]] = p  # client overrides all

    return list(patterns.values())


def get_pattern(pattern_id: str, industry: Optional[str] = None, client_slug: Optional[str] = None) -> Optional[dict]:
    """Get a single pattern by ID, respecting the override hierarchy."""
    patterns = load_patterns(industry, client_slug)
    return next((p for p in patterns if p["pattern_id"] == pattern_id), None)


def filter_patterns(
    patterns: list,
    authority_level: Optional[str] = None,
    capability_type: Optional[str] = None,
    min_maturity: int = 1,
    size_fit: Optional[str] = None,
) -> list:
    """Filter a pattern list by criteria."""
    result = patterns
    if authority_level:
        result = [p for p in result if p.get("authority_level") == authority_level]
    if capability_type:
        result = [p for p in result if p.get("capability_type") == capability_type]
    if min_maturity > 1:
        result = [p for p in result if p.get("maturity", 1) >= min_maturity]
    if size_fit:
        result = [p for p in result if size_fit in p.get("size_fit", ["ALL"]) or "ALL" in p.get("size_fit", ["ALL"])]
    return result


def check_authority_gate(pattern: dict, session_context: dict) -> dict:
    """
    Enforce authority level before any pattern executes.
    Returns: {"approved": bool, "action": str, "reason": str}

    This implements F4 (Authority Levels) + F27 (Michael Principle) at code level.
    """
    authority = pattern.get("authority_level", "LOW")

    if authority == "LOW":
        return {"approved": True, "action": "auto_execute", "reason": "LOW authority — fully automated"}

    elif authority == "MEDIUM":
        # Auto-execute but notify process owner
        process_owner = session_context.get("process_owner")
        return {
            "approved": True,
            "action": "execute_and_notify",
            "reason": f"MEDIUM authority — auto-executed, notifying {process_owner or 'process owner'}",
            "notify": process_owner
        }

    elif authority == "HIGH":
        # Always require human approval — no exceptions
        approver = session_context.get("approver") or session_context.get("compliance_officer")
        return {
            "approved": False,
            "action": "draft_for_review",
            "reason": f"HIGH authority — requires human approval from {approver or 'authorized approver'}",
            "approver": approver
        }

    # Unknown authority level = safest default
    return {"approved": False, "action": "block", "reason": "Unknown authority level — blocked by default"}


def log_false_done(pattern_id: str, session_date: str, context: str):
    """
    Log a false-done incident to the pattern registry.
    Called when: agent declares done -> user subsequently corrects or re-requests same output.
    This is the Sacrificial metric (F9) tracker.
    """
    # In a full implementation, this would update the pattern's correction_history
    # and false_done_incidents counter in the registry
    log_entry = {
        "date": session_date,
        "pattern_id": pattern_id,
        "incident_type": "false_done",
        "context": context
    }
    log_path = PATTERNS_DIR / "false_done_log.jsonl"
    with open(log_path, "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    return log_entry


if __name__ == "__main__":
    # Demo: load all patterns for a MFG/MID client
    import sys
    industry = sys.argv[1] if len(sys.argv) > 1 else None
    client = sys.argv[2] if len(sys.argv) > 2 else None

    patterns = load_patterns(industry=industry, client_slug=client)
    print(f"Loaded {len(patterns)} patterns (industry={industry}, client={client})")

    # Show HIGH authority patterns
    high_auth = filter_patterns(patterns, authority_level="HIGH")
    print(f"\nHIGH authority patterns ({len(high_auth)}):")
    for p in high_auth:
        print(f"  [{p['maturity']}] {p['pattern_id']}: {p['name']}")

    # Show mature patterns (level 4+)
    mature = filter_patterns(patterns, min_maturity=4)
    print(f"\nMature patterns (level 4+) ({len(mature)}):")
    for p in mature:
        print(f"  [{p['maturity']}] {p['pattern_id']}")
