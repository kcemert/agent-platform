# Client Onboarding Framework — Epic 8

## Files

| File | Purpose |
|---|---|
| `questionnaire.html` | Dark-themed intake form — fill out all five sections and export a client profile JSON |
| `score_client.py` | Reads the exported JSON and scores all 127 APQC processes for that client |
| `onboarding-checklist.html` | Interactive 4-phase engagement checklist with progress tracking and print-to-PDF |
| `example-client.json` | Sample Consumer Goods profile for testing the scorer |
| `outputs/` | Directory where `score_client.py` writes opportunity matrix JSON files |

## Usage

**Step 1 — Complete the questionnaire**
Open `questionnaire.html` in a browser, fill in all five sections, then click **Export to JSON**. Save the downloaded file into the `client-onboarding/` directory.

**Step 2 — Run the opportunity scorer**
```bash
python3 client-onboarding/score_client.py client-onboarding/example-client.json
```
The script prints a ranked summary table to stdout and writes a detailed JSON matrix to `client-onboarding/outputs/<company-name>-opportunity-matrix.json`.

**Step 3 — Work through the checklist**
Open `onboarding-checklist.html` in a browser. Enter the client name at the top, then tick each item as you complete it. Progress is saved in localStorage. Click **Print / PDF** to generate a shareable document.
