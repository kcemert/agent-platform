# Dashboard Component Library — Business Agents Platform
*F21 Artifact: Component Palette — reference for dashboard subagents*
*Last updated: March 2026*

---

## Overview

This document catalogs all reusable UI patterns across the Business Agents Platform dashboards. Every component listed here has a working implementation in at least one existing dashboard. When building a new dashboard, use these patterns — do not invent new CSS classes or JS function signatures.

**Existing dashboard files (read these for implementation reference):**
- `dashboards/operations.html` — SKU table, sparkline panel, decision context cards, impact narrative
- `dashboards/compliance.html` — CAPA queue, evidence drawer, run theater
- `dashboards/finance.html` — run theater (canonical implementation), live approval fetch
- `dashboards/pipeline.html` — stage gate modal, agent cards
- `dashboards/action-queue.html` — role-aware filter, merged recommendation list

---

## 1. KPI Strip

**Purpose:** Shows 4–6 top-line metrics at a glance. Always the first thing on the page.

**CSS classes:** `.kpi-strip`, `.kpi-card`, `.kpi-label`, `.kpi-value`, `.kpi-delta`

**HTML skeleton:**
```html
<div class="kpi-strip">
  <div class="kpi-card">
    <div class="kpi-label">Open RFQs</div>
    <div class="kpi-value" id="kpiOpenRFQs">—</div>
    <div class="kpi-delta" id="kpiOpenRFQsDelta"></div>
  </div>
  <!-- repeat for each KPI -->
</div>
```

**JS pattern:** Populate with `document.getElementById('kpiOpenRFQs').textContent = data.open_rfqs;`

**Data contract:** Any flat object with named numeric fields. Delta shown as `▲ +3` (green) or `▼ -2` (red).

**Kimre variant:** Use `--kimre: #f97316` accent color on KPI values that reflect agent activity.

---

## 2. Impact Narrative Header

**Purpose:** Plain-English summary of what has happened + what needs a decision. Addresses D1 (Narrative Clarity). Named persona + specific numbers — never generic.

**CSS classes:** `.impact-header`, `.impact-text`, `.impact-pill`, `.pill-critical`, `.pill-warning`, `.pill-ok`

**HTML skeleton:**
```html
<div class="impact-header">
  <p class="impact-text" id="impactText">Loading...</p>
  <div class="impact-pills" id="impactPills"></div>
</div>
```

**JS pattern:**
```javascript
document.getElementById('impactText').textContent =
  `Alex has 3 RFQs awaiting scope (oldest 2 days). 2 quotes > 5 days stale need follow-up. Pipeline: £340K.`;
```

**Rule:** Always name the persona. Always include a count of items needing action. Reference the most recent agent run if applicable.

---

## 3. Run Theater Drawer

**Purpose:** The HITL (Human-in-the-Loop) agent execution flow. Animated step-by-step execution → show recommendations → accept/reject each → submit and close.

**CSS classes:** `.run-overlay`, `.run-drawer`, `.run-header`, `.run-steps`, `.log-step`, `.step-icon`, `.rec-list`, `.rec-row`, `.urgency-badge`, `.btn-accept`, `.btn-reject`, `.btn-submit`

**JS functions:**
- `openRunDrawer(slug)` — opens drawer, starts animation
- `closeRunDrawer()` — closes and resets
- `animateSteps(steps)` — animates step list with 600ms delays
- `showRecommendations(result)` — populates rec list from API response
- `decideRec(id, decision)` — marks rec as accepted/rejected
- `submitAndClose()` — POSTs decisions to `/api/recommendations/{id}/decide`, closes drawer

**AGENT_STEPS pattern:**
```javascript
const AGENT_STEPS = {
  'kimre-rfq-quote-agent': [
    'Reading RFQ descriptions...',
    'Matching application to product family...',
    'Selecting model recommendation...',
    'Drafting scope paragraphs...',
    'Flagging clarification gaps...',
    'Generating recommendations...'
  ]
};
```

**API call:** `POST /api/run/{slug}` → returns `{outcome, run_id, recommendations: [{id, rec_type, item_label, urgency, recommended_action}]}`

**Canonical implementation:** `dashboards/finance.html` (most complete version)

---

## 4. Sortable Table + Row Click

**Purpose:** Main data list for the persona's primary entity (quotes, orders, materials, etc.). Sortable by column. Row click opens detail panel.

**CSS classes:** `.agent-table`, `.tbl-header`, `.tbl-row`, `.sort-btn`, `.stage-badge`, `.urgency-dot`

**JS functions:**
- `sortTable(key)` — sorts `allItems` array by key, re-renders
- `renderTable(items)` — renders rows into `#tableBody`
- `openDetailPanel(id)` — opens side panel for given item ID

**HTML skeleton:**
```html
<table class="agent-table" id="mainTable">
  <thead>
    <tr>
      <th><button class="sort-btn" onclick="sortTable('stage')">Stage</button></th>
      <th><button class="sort-btn" onclick="sortTable('days_in_stage')">Days ↕</button></th>
      <!-- more columns -->
    </tr>
  </thead>
  <tbody id="tableBody"></tbody>
</table>
```

**Sort state:** `let sortKey = 'days_in_stage'; let sortDir = -1;` (descending by default for urgency)

---

## 5. Detail Side Panel

**Purpose:** Full context for a clicked table row. Slides in from the right. Contains all fields, sub-tables, action buttons, and the HITL decision controls for that item.

**CSS classes:** `.detail-panel`, `.panel-overlay`, `.panel-header`, `.panel-section`, `.panel-section-title`, `.panel-close`

**JS functions:**
- `openPanel(id)` — populates panel with item data, shows overlay
- `closePanel()` — hides panel and overlay
- `decideItem(id, decision)` — handles approve/reject/escalate for item in panel

**HTML skeleton:**
```html
<div class="panel-overlay" id="panelOverlay" onclick="closePanel()"></div>
<div class="detail-panel" id="detailPanel">
  <div class="panel-header">
    <h3 id="panelTitle"></h3>
    <button class="panel-close" onclick="closePanel()">✕</button>
  </div>
  <div id="panelContent"></div>
</div>
```

**Pattern:** Panel content is built dynamically in JS using template literals. Never use a static HTML panel that needs to be hidden/shown per record.

---

## 6. Sparkline SVG

**Purpose:** Mini trend chart showing 12-week or N-period history for a metric. Fits inside a KPI card or table cell.

**JS function:**
```javascript
function buildSparkline(historyArray, w = 80, h = 28, color = '#6366f1') {
  const max = Math.max(...historyArray);
  const min = Math.min(...historyArray);
  const range = max - min || 1;
  const pts = historyArray.map((v, i) => {
    const x = (i / (historyArray.length - 1)) * w;
    const y = h - ((v - min) / range) * h;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');
  return `<svg width="${w}" height="${h}" style="display:block">
    <polyline points="${pts}" fill="none" stroke="${color}" stroke-width="1.5"/>
  </svg>`;
}
```

**Data contract:** Array of numbers (12 weeks of demand, OEE readings, etc.)

**Usage in operations.html:** Called with `demand_history` array from `/api/inventory` response.

---

## 7. Decision Context Card

**Purpose:** Shows a single agent recommendation with full context (item details, cost/risk, edit fields) and Approve / Reject / Escalate buttons. Addresses D3 (Human-in-the-Loop).

**CSS classes:** `.decision-context-card`, `.btn-approve-ctx`, `.btn-reject-ctx`, `.btn-escalate-ctx`, `.decided-badge`

**JS function:**
```javascript
function decideItem(id, decision) {
  const card = document.getElementById(`card-${id}`);
  card.querySelector('.decision-actions').innerHTML =
    `<span class="decided-badge decided-${decision}">${decision.toUpperCase()}</span>`;
  // POST to /api/recommendations/{id}/decide
  fetch(`${API}/api/recommendations/${id}/decide`, {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({decision, decided_by: 'dashboard'})
  });
}
```

**Pattern:** Each recommendation from a run theater becomes a decision context card.

---

## 8. Urgency Badge

**Purpose:** Color-coded urgency indicator. Appears on table rows, rec cards, KPI strip deltas.

**CSS classes:** `.urgency-badge`, `.urgency-critical`, `.urgency-high`, `.urgency-medium`, `.urgency-low`

**CSS:**
```css
.urgency-badge { padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; text-transform: uppercase; }
.urgency-critical { background: rgba(239,68,68,0.15); color: #ef4444; }
.urgency-high     { background: rgba(249,115,22,0.15); color: #f97316; }
.urgency-medium   { background: rgba(245,158,11,0.15); color: #f59e0b; }
.urgency-low      { background: rgba(34,197,94,0.15); color: #22c55e; }
```

---

## 9. Toast Notification

**Purpose:** Brief confirmation after a decision action. Auto-dismisses after N ms.

**JS function:**
```javascript
function showToast(msg, duration = 3000) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), duration);
}
```

**HTML:** `<div id="toast" class="toast"></div>` at the bottom of body.

**CSS:**
```css
.toast { position: fixed; bottom: 24px; right: 24px; background: #22c55e; color: #fff;
  padding: 12px 20px; border-radius: 8px; font-size: 13px; opacity: 0; transition: opacity 0.3s;
  pointer-events: none; z-index: 9999; }
.toast.show { opacity: 1; }
```

---

## 10. Export CSV

**Purpose:** Download a table's data as a CSV file.

**JS function:**
```javascript
function downloadCSV(rows, filename = 'export.csv') {
  if (!rows.length) return;
  const headers = Object.keys(rows[0]);
  const csv = [headers.join(','), ...rows.map(r => headers.map(h =>
    JSON.stringify(r[h] ?? '')).join(','))].join('\n');
  const a = document.createElement('a');
  a.href = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv);
  a.download = filename;
  a.click();
}
```

---

## 11. Activity Feed / Communication Log

**Purpose:** Chronological log of events/touchpoints for a specific item (order, quote, customer). Used in detail panels.

**CSS classes:** `.feed-list`, `.feed-item`, `.feed-time`, `.feed-text`, `.feed-type-badge`

**HTML skeleton:**
```html
<ul class="feed-list" id="orderFeed">
  <!-- populated dynamically -->
</ul>
```

**JS pattern:**
```javascript
function prependFeedItem(text, type = 'note', timestamp = new Date().toLocaleString()) {
  const li = document.createElement('li');
  li.className = 'feed-item';
  li.innerHTML = `<span class="feed-time">${timestamp}</span>
    <span class="feed-type-badge badge-${type}">${type}</span>
    <span class="feed-text">${text}</span>`;
  document.getElementById('orderFeed').prepend(li);
}
```

---

## 12. Stage Progress Bar (ETO-specific)

**Purpose:** Visual milestone tracker for an ETO project order. Shows current stage highlighted among all stages.

**CSS classes:** `.milestone-bar`, `.milestone-step`, `.milestone-step.active`, `.milestone-step.done`, `.milestone-connector`

**HTML skeleton:**
```html
<div class="milestone-bar">
  <div class="milestone-step done"><span class="step-dot"></span><span class="step-label">BOM</span></div>
  <div class="milestone-connector done"></div>
  <div class="milestone-step active"><span class="step-dot"></span><span class="step-label">Fabrication</span></div>
  <div class="milestone-connector"></div>
  <div class="milestone-step"><span class="step-dot"></span><span class="step-label">QC Check</span></div>
  <!-- more steps -->
</div>
```

**Stages (Kimre):** Received → BOM Created → Materials Pulled → Fabrication → QC Check → Packed → Shipped → Delivered

---

## 13. Kimre Internal Navigation

**Purpose:** Consistent top navigation across all 6 Kimre dashboard pages.

**HTML (include in every Kimre page):**
```html
<nav class="kimre-nav">
  <div class="kimre-nav-inner">
    <span class="kimre-nav-brand">Kimre Inc.</span>
    <div class="kimre-nav-links">
      <a href="./index.html" class="kimre-nav-link">Home</a>
      <a href="./sales.html" class="kimre-nav-link">Sales</a>
      <a href="./engineering.html" class="kimre-nav-link">Engineering</a>
      <a href="./customer-service.html" class="kimre-nav-link">Customer Service</a>
      <a href="./executive.html" class="kimre-nav-link">Executive</a>
      <a href="./quality.html" class="kimre-nav-link">Quality</a>
    </div>
  </div>
</nav>
```

**CSS:**
```css
.kimre-nav { background: var(--card); border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 100; }
.kimre-nav-inner { max-width: 1200px; margin: 0 auto; padding: 0 24px; display: flex; align-items: center; gap: 24px; height: 48px; }
.kimre-nav-brand { font-size: 13px; font-weight: 700; color: var(--kimre); }
.kimre-nav-links { display: flex; gap: 4px; }
.kimre-nav-link { padding: 6px 12px; border-radius: 6px; font-size: 12px; font-weight: 500; color: var(--text-sec); text-decoration: none; transition: all 0.15s; }
.kimre-nav-link:hover, .kimre-nav-link.active { background: var(--orange-dim); color: var(--kimre); }
```

**Active link:** Add `class="kimre-nav-link active"` to the link matching the current page.

---

## Design Token Reference

```css
:root {
  /* Layout */
  --bg:           #0f1117;
  --card:         #161b2e;
  --card-alt:     #1a2035;
  --border:       #1e293b;
  --border-light: #253047;

  /* Text */
  --text:         #f1f5f9;
  --text-sec:     #94a3b8;
  --text-muted:   #64748b;

  /* Brand (Kimre) */
  --kimre:        #f97316;
  --orange-dim:   rgba(249,115,22,0.12);

  /* Semantic colors */
  --green:        #22c55e;
  --red:          #ef4444;
  --amber:        #f59e0b;
  --indigo:       #6366f1;
  --cyan:         #06b6d4;
}
```

**Font:** Inter from Google Fonts — `<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">`

**API base:** `const API = 'http://localhost:8500';` — always with offline fallback.
