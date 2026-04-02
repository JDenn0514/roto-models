---
title: Moonlight Graham
toc: false
sidebar: false
---

<div class="hub-header">
  <div class="hub-wordmark-block">
    <div class="hub-wordmark">Moonlight Graham</div>
    <div class="hub-league-meta">AL-Only Keeper · <span class="hub-accent">10 Teams</span> · OnRoto</div>
  </div>
  <div class="hub-season-badge">2026 Season</div>
</div>

<p class="hub-intro">Research and analysis for the Moonlight Graham fantasy baseball league — SGP valuation, auction targeting, and post-draft retrospectives.</p>

```js
const reports = await FileAttachment("data/reports.json").json();
const allTags = [...new Set(reports.flatMap((r) => r.tags ?? []))].sort();
```

```js
const tagInput = Inputs.radio(["All", ...allTags], {value: "All"});
const activeTag = Generators.input(tagInput);
```

```js
const filtered =
  activeTag === "All"
    ? reports
    : reports.filter((r) => (r.tags ?? []).includes(activeTag));
```

```js
// Render filter chips — tagInput is a DOM node, must be embedded via html template
display(html`<div class="hub-filter-row">${tagInput}</div>`);
```

```js
display(html`<div class="hub-report-count">${filtered.length} report${filtered.length !== 1 ? "s" : ""}</div>`);
```

```js
function fmtDate(s) {
  const d = new Date(s + "T12:00:00");
  return {
    month: d.toLocaleString("en-US", {month: "short"}).toUpperCase(),
    day: d.getDate(),
    year: d.getFullYear(),
  };
}

display(html`<div class="hub-report-list">
  ${filtered.map((r) => {
    const d = fmtDate(r.date);
    return html`<a href="${r.path}" class="hub-report-entry">
      <div class="hub-entry-date">
        <div class="hub-month">${d.month}</div>
        <div class="hub-day">${d.day}</div>
        <div class="hub-year">${d.year}</div>
      </div>
      <div class="hub-entry-body">
        <div class="hub-entry-title">${r.title}</div>
        <div class="hub-entry-desc">${r.description}</div>
        <div class="hub-entry-tags">${(r.tags ?? []).map(
          (t) => html`<span class="hub-tag hub-tag-${t}">${t}</span>`
        )}</div>
      </div>
      <span class="hub-entry-arrow">→</span>
    </a>`;
  })}
</div>`);
```

<div class="hub-new-prompt">
  <span class="hub-new-icon">+</span>
  <span class="hub-new-text">Add a report: create <code>site/src/my-report.md</code> with frontmatter and push to main.</span>
</div>
