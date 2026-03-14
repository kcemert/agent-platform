# Stakeholder Enrichment Agent
**Slug**: `stakeholder-enrichment-agent`
**File**: `pilot-agents/stakeholder-enrichment-agent.py`
**Lifecycle**: blueprint (Kimre pilot context — uses 4 hardcoded Kimre contacts in dry-run)
**Last generated**: 2026-03-14 | **Last verified**: 2026-03-14

## Purpose

The Stakeholder Enrichment Agent automates the process of building rich, current contact profiles for key client stakeholders by fetching their LinkedIn data via the Proxycurl API. In pre-sales and account management workflows, teams manually look up contacts on LinkedIn, copy-paste titles, companies, locations, and career summaries into CRM records — a time-consuming process that produces inconsistent data quality and goes stale quickly.

The agent reads LinkedIn profile URLs from either the `contacts` table in `business_agents.db` (live mode) or from DRY_RUN_PROFILES (dry-run mode), calls the Proxycurl REST API to retrieve enriched profile JSON, extracts eight key fields (name, title, company, location, summary, skills, enriched_json, enriched_at), and upserts the enriched record back into the `contacts` table. In dry-run mode, no API calls are made and no DB writes occur — the mock profiles for 4 Kimre Inc. stakeholders (George Pedersen, Mary Gaston, Frank Powers, Chris Pedersen) are used instead.

The agent is the first implementation of profile intelligence for the Kimre client engagement workflow, enabling the sales dashboard to display enriched stakeholder context alongside engagement history.

## Inputs

- **Live mode**:
  - `contacts` table in `business_agents.db`: selects rows where `linkedin_url IS NOT NULL AND linkedin_url != ''`, returning `linkedin_url` and `client_slug` per contact.
  - Proxycurl API: `GET https://nubela.co/proxycurl/api/v2/linkedin?url={linkedin_url}&use_cache=if-present` with `Authorization: Bearer {PROXYCURL_API_KEY}`. Returns a JSON profile object with `full_name`, `headline`, `occupation`, `summary`, `city`, `country_full_name`, `experiences[]`, `skills[]`.
  - Environment variable: `PROXYCURL_API_KEY` (required for live mode; agent exits with error if not set).
- **Dry-run mode**:
  - `DRY_RUN_PROFILES`: 4 hardcoded Kimre contact records, each with `linkedin_url`, `client_slug`, and a `mock_response` dict pre-filled with Kimre-specific profile data:
    - George C. Pedersen (Founder & Chairman, Kimre Inc.)
    - Mary Gaston (President & CLO, Kimre Inc.)
    - Frank Powers (VP of Engineering, Kimre Inc.)
    - Chris Pedersen (Senior Manufacturing Engineer, Kimre Inc.)
- **Flags**:
  - `--dry-run`: Uses DRY_RUN_PROFILES; skips Proxycurl API calls; skips DB writes. Detected via `"--dry-run" in sys.argv` (module-level constant `DRY_RUN`).

## Outputs

```json
{
  "agent": "stakeholder-enrichment-agent",
  "run_at": "2026-03-14T09:00:00+00:00",
  "dry_run": true,
  "profiles_processed": 4,
  "enriched": 4,
  "errors": 0,
  "contacts": [
    {
      "linkedin_url": "https://www.linkedin.com/in/george-c-pedersen-76231910/",
      "client_slug": "kimre",
      "name": "George C. Pedersen",
      "title": "Founder & Chairman of the Board",
      "company": "Kimre Inc.",
      "location": "Miami, United States",
      "summary": "Founded Kimre Inc., a leading manufacturer of mist eliminators...",
      "skills": "Mist Elimination, Industrial Filtration, Chemical Engineering, Manufacturing",
      "enriched_json": "{...full profile JSON...}",
      "enriched_at": "2026-03-14T09:00:00+00:00",
      "status": "enriched",
      "_source": "dry_run"
    }
  ]
}
```

In live mode, `_source` is `"proxycurl"`. Skills are capped at the first 8 items from the `skills[]` array, joined as a comma-separated string. No output file is written to disk (unlike other agents — this agent does not call `write_output`). Run is logged to `pilot_runs` table via `agent_runner.log_to_db`. Output is printed to stdout after the run completes.

## Behavior

1. **Check API key** (live mode only): If `PROXYCURL_API_KEY` environment variable is not set, print error and exit with code 1.
2. **Load profiles to enrich**: Dry-run → use DRY_RUN_PROFILES (4 Kimre contacts). Live → query `contacts` table for rows with non-null `linkedin_url`.
3. **For each profile**:
   a. Dry-run: use `profile_def["mock_response"]` directly; set `_source = "dry_run"`.
   b. Live: call `requests.get(PROXYCURL_API_URL, params={"url": linkedin_url, "use_cache": "if-present"}, headers={"Authorization": "Bearer {key}"}, timeout=30)`. On HTTP error or exception, append an error record and continue.
4. **Extract key fields** from the profile JSON:
   - `name` = `full_name`
   - `title` = `occupation` OR `headline` (occupation preferred)
   - `company` = `experiences[0].company` (first experience entry)
   - `location` = `"{city}, {country_full_name}"` (stripped of leading/trailing commas)
   - `summary` = `summary`
   - `skills` = first 8 items of `skills[]` joined by ", "
   - `enriched_json` = full JSON serialized as string
   - `enriched_at` = UTC timestamp
5. **Upsert to DB** (live mode only): INSERT OR REPLACE into `contacts` table using the 10-field schema. Dry-run skips this step.
6. **Accumulate counters**: `enriched_count` (status == "enriched"), `error_count` (status == "error").
7. **Log to DB** via `agent_runner.log_to_db`: outcome = "success" if enriched > 0, "partial" if 0. Tools = `["proxycurl_api"]` (live) or `["dry_run_mock"]` (dry-run).
8. **Print JSON output** to stdout.

## HITL Decision Points

- **All enrichment is fully automated**: Once triggered, the agent enriches all contacts in the input set without asking for human confirmation per record.
- **Data quality review**: After a live run, enriched profiles should be reviewed in the Kimre sales dashboard to verify that the `title` and `company` fields correctly reflect current role (LinkedIn profiles may be outdated).
- **API errors**: Contacts that fail Proxycurl enrichment (HTTP non-200 or network error) are logged with `status = "error"`. A human should investigate failed URLs (profile may be private or URL may be incorrect).
- **PROXYCURL_API_KEY management**: Setting and rotating the API key is a human operation. The agent does not handle key rotation or rate-limit throttling.

## Limitations

- **Requires `requests` library**: The `import requests` is inside `run()` and will raise `ImportError` if the package is not installed. There is no graceful fallback.
- **Live mode requires `contacts` table**: The `contacts` table with `linkedin_url` and `client_slug` columns must exist in `business_agents.db`. No schema migration is included in the agent.
- **Proxycurl API cost**: Each live profile call consumes a Proxycurl API credit. The agent does not check rate limits, credit balance, or implement retry with backoff.
- **Skills capped at 8**: The agent stores only the first 8 skills as a CSV string. The full profile is available in `enriched_json` but not indexed.
- **No output file written to disk**: Unlike other platform agents, this agent does not call `write_output`. Results are printed to stdout and (in live mode) written to DB only.
- **DB path is computed at import time**: `DB_PATH = Path(__file__).parent.parent / "business-agents" / "business_agents.db"` — relative to the agent file location. Moving the file breaks the DB path.
- **`DRY_RUN` is a module-level constant**: It is set at import time from `sys.argv`. Importing the module in a test context where `--dry-run` is not in `sys.argv` will default to live mode.
- **No deduplication of API calls**: If the same `linkedin_url` appears multiple times in the contacts table, it will be fetched and upserted multiple times.

## Example Run

```bash
python3 "pilot-agents/stakeholder-enrichment-agent.py" --dry-run
```

Condensed output:

```
[2026-03-14T09:00:00] === Stakeholder Enrichment Agent starting (dry_run=True) ===
[2026-03-14T09:00:00] Profiles to enrich: 4
[2026-03-14T09:00:00] Processing: https://www.linkedin.com/in/george-c-pedersen-76231910/
[2026-03-14T09:00:00]   Enriched: George C. Pedersen — Founder & Chairman of the Board @ Kimre Inc.
[2026-03-14T09:00:00] Processing: https://www.linkedin.com/in/marygaston/
[2026-03-14T09:00:00]   Enriched: Mary Gaston — President & Chief Legal Officer @ Kimre Inc.
[2026-03-14T09:00:00] Processing: https://www.linkedin.com/in/frank-powers-vp-engineering/
[2026-03-14T09:00:00]   Enriched: Frank Powers — VP of Engineering @ Kimre Inc.
[2026-03-14T09:00:00] Processing: https://www.linkedin.com/in/chris-pedersen-56ab407/
[2026-03-14T09:00:00]   Enriched: Chris Pedersen — Senior Manufacturing Engineer @ Kimre Inc.
[2026-03-14T09:00:00] Enriched 4 profiles, 0 errors
[2026-03-14T09:00:00] === Stakeholder Enrichment Agent complete (0.1s) ===

{
  "agent": "stakeholder-enrichment-agent",
  "run_at": "2026-03-14T09:00:00+00:00",
  "dry_run": true,
  "profiles_processed": 4,
  "enriched": 4,
  "errors": 0,
  "contacts": [...]
}
```
