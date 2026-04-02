---
title: How We Price a Home Run
date: 2026-04-01
description: The statistical engine behind Moonlight Graham auction valuations — how 10 seasons of league history become calibrated dollar values.
tags: [methodology, valuation, interactive]
sidebar: false
---

```js
display(html`<div class="report-nav">
  <a href="/roto-models/" class="back-link">← All Reports</a>
  <span class="report-nav-wordmark">Moonlight Graham</span>
</div>`);
```

```js
// ── Data ──────────────────────────────────────────────────────────────────────
const standings = FileAttachment("data/standings.json").json();
const sweep     = FileAttachment("data/sweep.json").json();
```

```js
// ── Design constants ──────────────────────────────────────────────────────────
const C = {
  bg:  "#faf9f5",
  txt: "#2d2d2d",
  mid: "#666",
  lit: "#999",
  grd: "#ededeb",
  pri: "#3A6EA5",
  sec: "#C1666B",
  acc: "#2A9D8F",
};

const METHOD_COLORS = {
  "pairwise_mean":   "#3A6EA5",
  "pairwise_median": "#2A9D8F",
  "ols":             "#B5892B",
  "robust_reg":      "#C1666B",
};

const METHOD_LABELS = {
  "pairwise_mean":   "Pairwise Mean",
  "pairwise_median": "Pairwise Median",
  "ols":             "OLS Regression",
  "robust_reg":      "Robust Regression",
};

const CAT_META = {
  R:    {label: "Runs Scored",      unit: "runs",    inverse: false, batting: true},
  HR:   {label: "Home Runs",        unit: "HR",      inverse: false, batting: true},
  RBI:  {label: "Runs Batted In",   unit: "RBI",     inverse: false, batting: true},
  SB:   {label: "Stolen Bases",     unit: "SB",      inverse: false, batting: true},
  AVG:  {label: "Batting Average",  unit: "avg pts", inverse: false, batting: true},
  W:    {label: "Pitcher Wins",     unit: "wins",    inverse: false, batting: false},
  SV:   {label: "Saves",            unit: "saves",   inverse: false, batting: false},
  ERA:  {label: "ERA",              unit: "ERA",     inverse: true,  batting: false},
  WHIP: {label: "WHIP",             unit: "WHIP",    inverse: true,  batting: false},
  SO:   {label: "Strikeouts",       unit: "K",       inverse: false, batting: false},
};

// ── Final calibrated denominators (composite model, 2026-03-24 sweep) ──────────
const DENOMS = {
  R:    {denom: 31.82,   ci_low: null,    ci_high: null,    method: "ols",             batting: true},
  HR:   {denom: 12.17,   ci_low: 9.88,    ci_high: 14.68,   method: "pairwise_mean",   batting: true},
  RBI:  {denom: 30.85,   ci_low: null,    ci_high: null,    method: "ols",             batting: true},
  SB:   {denom: 10.36,   ci_low: 8.09,    ci_high: 13.01,   method: "pairwise_mean",   batting: true},
  AVG:  {denom: 0.00306, ci_low: 0.00214, ci_high: 0.00418, method: "pairwise_mean",   batting: true},
  W:    {denom: 3.00,    ci_low: 2.70,    ci_high: 3.60,    method: "pairwise_median", batting: false},
  SV:   {denom: 6.40,    ci_low: null,    ci_high: null,    method: "robust_reg",      batting: false},
  SO:   {denom: 35.68,   ci_low: 25.36,   ci_high: 47.29,   method: "pairwise_mean",   batting: false},
  ERA:  {denom: 0.1013,  ci_low: null,    ci_high: null,    method: "ols",             batting: false},
  WHIP: {denom: 0.01863, ci_low: 0.015,   ci_high: 0.02264, method: "pairwise_mean",   batting: false},
};

// ── Year-over-year denominator estimates (per-year leave-one-out calibration) ──
const YEAR_LEVEL = {
  R:    {"2019":28.62,"2021":37.71,"2022":27.54,"2023":28.11,"2024":40.33,"2025":33.33},
  HR:   {"2015":12.78,"2016":12.96,"2017":13.50,"2018":8.73,"2019":12.78,"2021":17.37,"2022":9.00,"2023":10.44,"2024":10.44,"2025":13.56},
  RBI:  {"2015":29.00,"2016":28.89,"2017":35.19,"2018":26.82,"2019":27.90,"2021":34.92,"2022":25.65,"2023":28.67,"2024":42.89,"2025":34.44},
  SB:   {"2015":7.67,"2016":8.55,"2017":6.75,"2018":6.12,"2019":6.93,"2021":6.39,"2022":8.10,"2023":11.78,"2024":18.00,"2025":14.78},
  AVG:  {"2019":0.00324,"2021":0.00260,"2022":0.00388,"2023":0.00278,"2024":0.00341,"2025":0.00239},
  W:    {"2019":2.16,"2021":2.025,"2022":4.86,"2023":2.33,"2024":3.875,"2025":6.25},
  SV:   {"2015":3.56,"2016":8.19,"2017":5.94,"2018":5.04,"2019":5.13,"2021":6.12,"2022":7.56,"2023":6.67,"2024":6.33,"2025":6.44},
  SO:   {"2019":26.37,"2021":41.90,"2022":34.70,"2023":29.50,"2024":35.75,"2025":47.50},
  ERA:  {"2015":0.0733,"2016":0.0667,"2017":0.1758,"2018":0.1098,"2019":0.0633,"2021":0.0954,"2022":0.1017,"2023":0.1144,"2024":0.1178,"2025":0.1011},
  WHIP: {"2015":0.01744,"2016":0.00844,"2017":0.02756,"2018":0.02034,"2019":0.01811,"2021":0.01485,"2022":0.02484,"2023":0.01778,"2024":0.02111,"2025":0.01633},
};

// ── Composite config: which method was chosen for each category ────────────────
const COMPOSITE = {
  R:    {method: "ols",             supp: false, decay: true,  rate: 0.80, punt: false},
  HR:   {method: "pairwise_mean",   supp: true,  decay: false, rate: 0.85, punt: false},
  RBI:  {method: "ols",             supp: true,  decay: false, rate: 0.85, punt: false},
  SB:   {method: "pairwise_mean",   supp: true,  decay: true,  rate: 0.90, punt: false},
  AVG:  {method: "pairwise_mean",   supp: false, decay: false, rate: 0.85, punt: false},
  W:    {method: "pairwise_median", supp: false, decay: true,  rate: 0.80, punt: true},
  SV:   {method: "robust_reg",      supp: true,  decay: false, rate: 0.85, punt: false},
  SO:   {method: "pairwise_mean",   supp: false, decay: false, rate: 0.85, punt: true},
  ERA:  {method: "ols",             supp: true,  decay: true,  rate: 0.80, punt: false},
  WHIP: {method: "pairwise_mean",   supp: true,  decay: false, rate: 0.85, punt: false},
};
```

```js
// ── Tooltip (safe DOM construction) ───────────────────────────────────────────
const tt = (() => {
  const div = document.createElement("div");
  div.className = "auction-tooltip";
  document.body.appendChild(div);
  invalidation.then(() => div.remove());
  return div;
})();

function tipRow(label, value, valCls) {
  const row = document.createElement("div"); row.className = "tr";
  const lbl = document.createElement("span"); lbl.className = "tl"; lbl.textContent = label;
  const val = document.createElement("span"); val.className = valCls ? `tv ${valCls}` : "tv"; val.textContent = value;
  row.append(lbl, val);
  return row;
}
function tip(specs, e) {
  tt.replaceChildren(...specs.map(s => {
    if (s.cls === "tr") return tipRow(s.label, s.value, s.valCls);
    const el = document.createElement("div"); el.className = s.cls; el.textContent = s.text;
    if (s.color) el.style.color = s.color;
    return el;
  }));
  tt.style.opacity = "1"; mv(e);
}
function mv(e) {
  const x = e.clientX, y = e.clientY, tw = 230, th = 130;
  tt.style.left = (x + 14 + tw > window.innerWidth  ? x - tw - 14 : x + 14) + "px";
  tt.style.top  = (y + 14 + th > window.innerHeight ? y - th - 14 : y + 14) + "px";
}
function ht() { tt.style.opacity = "0"; }
```

```js
// ── Helpers ───────────────────────────────────────────────────────────────────
function linReg(pts) {
  const n = pts.length;
  if (n < 3) return null;
  const xm = d3.mean(pts, d => d.x);
  const ym = d3.mean(pts, d => d.y);
  const num = d3.sum(pts, d => (d.x - xm) * (d.y - ym));
  const den = d3.sum(pts, d => (d.x - xm) ** 2);
  if (Math.abs(den) < 1e-10) return null;
  const s = num / den;
  const b = ym - s * xm;
  return {slope: s, intercept: b};
}

function fmtStat(cat, v) {
  if (v == null) return "—";
  if (cat === "AVG") return v.toFixed(3);
  if (cat === "ERA" || cat === "WHIP") return v.toFixed(3);
  return d3.format(",")(Math.round(v));
}

function fmtDenom(cat, v) {
  if (cat === "AVG" || cat === "ERA" || cat === "WHIP") return v.toFixed(4);
  return v.toFixed(1);
}

// Pill control factory
function makePills(cats, initial, onChange) {
  const wrap = document.createElement("div");
  wrap.className = "toggle-pill";
  const btns = {};
  cats.forEach(cat => {
    const btn = document.createElement("button");
    btn.className = cat === initial ? "tpill active" : "tpill";
    btn.textContent = cat;
    btn.addEventListener("click", () => {
      Object.values(btns).forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      onChange(cat);
    });
    btns[cat] = btn;
    wrap.appendChild(btn);
  });
  return wrap;
}
```

# How We Price a Home Run

_SGP calibration methodology &middot; Moonlight Graham &middot; March 2026 &middot; Data: 2015–2025 league history_

```js
// ── Stat cards ─────────────────────────────────────────────────────────────────
{
  const cards = [
    {val: "10",    lbl: "Seasons of data"},
    {val: "92",    lbl: "Team-year observations"},
    {val: "10",    lbl: "Scoring categories"},
    {val: "320",   lbl: "Configurations tested"},
    {val: "0.963", lbl: "Rank correlation"},
  ];
  const grid = document.createElement("div"); grid.className = "stat-grid";
  cards.forEach(({val, lbl}) => {
    const card = document.createElement("div"); card.className = "stat-card";
    const v = document.createElement("div"); v.className = "val"; v.textContent = val;
    const l = document.createElement("div"); l.className = "lbl"; l.textContent = lbl;
    card.append(v, l); grid.appendChild(card);
  });
  display(grid);
}
```

<div class="narrative">
In a 10-team rotisserie league, you don't compete on raw statistics. Every week, each team is ranked from 1 to 10 in each of 10 categories — runs, home runs, stolen bases, and seven others. Those rankings accumulate into standings points, and the team with the most points wins the pennant.

This creates a measurement problem on auction day. <strong>How much should you bid on a player projected for 45 home runs?</strong> It depends on how much competitive advantage those 45 home runs actually purchase — and that depends on what the rest of the league looks like. A 45-homer season is worth very differently from a .310 batting average, but both need to be valued in the same currency: dollars.

The engine that converts projected statistics into dollars is called <strong>Standings Gain Points (SGP)</strong>. The SGP denominator for each category answers a single question: <em>how many units of this stat does it take to move up one position in the standings?</em> If the HR denominator is 12, then 12 home runs ≈ one standings point, and you can price home runs accordingly.

This report explains exactly how we measured those exchange rates for Moonlight Graham.
</div>

<hr class="divider">

## Part 1 — Reading the League's History

<p class="section-meta">10 seasons · 2015–2025 · 92 team-years · select a category to explore</p>

<div class="narrative">
The foundation of any SGP calibration is real historical data. We have complete league standings for Moonlight Graham going back to 2015: every team's total in each scoring category and exactly how many standings points they earned.

The scatter below shows this data directly. Each dot is one team in one season. The x-axis shows how much they accumulated in the category, and the y-axis shows how many standings points they earned. The dashed line is the best-fit regression — its slope tells us how many stat units per standings point.

<strong>Primary years</strong> (2019–2025, shown in blue) are the core calibration window. <strong>Supplemental years</strong> (2015–2018, shown in gray) used only 8 of 10 categories and had 11 teams instead of 10 — we use them cautiously for select categories.
</div>

```js
const scatterCat = Mutable("HR");
const setScatterCat = (cat) => { scatterCat.value = cat; };
```

```js
// Category selector
{
  const batting  = ["R","HR","RBI","SB","AVG"];
  const pitching = ["W","SV","ERA","WHIP","SO"];

  const bar = document.createElement("div");
  bar.className = "filter-bar";
  bar.style.marginBottom = "14px";

  function addGroup(label, cats) {
    const lbl = document.createElement("span");
    lbl.className = "filter-label";
    lbl.textContent = label + ":";
    bar.appendChild(lbl);
    const pills = makePills(cats, scatterCat, setScatterCat);
    bar.appendChild(pills);
  }

  addGroup("Batting",  batting);
  addGroup("Pitching", pitching);
  display(bar);
}
```

```js
// Scatter chart (reactive on scatterCat)
{
  const cat  = scatterCat;
  const meta = CAT_META[cat];

  const pts = standings
    .filter(d => d[cat] != null && d[cat + "_pts"] != null)
    .map(d => ({x: d[cat], y: d[cat + "_pts"], team: d.team, year: d.year, era: d.era}));

  if (pts.length === 0) { display(html`<p style="color:#999;font-size:13px;font-style:italic">No data for this category.</p>`); } else {

  const W = 920, iH = 310;
  const m = {t: 20, r: 40, b: 52, l: 58};
  const iW = W - m.l - m.r;

  const xExt = d3.extent(pts, d => d.x);
  const xPad = (xExt[1] - xExt[0]) * 0.07;
  // Inverse categories: flip x so left = better, preserving upward trend
  const xDom = meta.inverse
    ? [xExt[1] + xPad, xExt[0] - xPad]
    : [xExt[0] - xPad, xExt[1] + xPad];

  const x = d3.scaleLinear().domain(xDom).range([0, iW]);
  const y = d3.scaleLinear().domain([0.25, 10.75]).range([iH, 0]);

  const reg = linReg(pts.map(d => ({x: d.x, y: d.y})));

  const svg = d3.create("svg")
    .attr("width", W).attr("height", iH + m.t + m.b)
    .style("background", C.bg);

  const g = svg.append("g").attr("transform", `translate(${m.l},${m.t})`);

  // Horizontal grid lines
  y.ticks(9).forEach(tv => {
    g.append("line")
      .attr("x1", 0).attr("y1", y(tv)).attr("x2", iW).attr("y2", y(tv))
      .attr("stroke", C.grd).attr("stroke-width", 1);
  });

  // Axes
  const xFmt = (cat === "AVG" || cat === "ERA" || cat === "WHIP")
    ? d => d.toFixed(3) : d3.format(",");

  g.append("g").attr("transform", `translate(0,${iH})`)
    .call(d3.axisBottom(x).ticks(6).tickFormat(xFmt))
    .call(ax => {
      ax.select(".domain").attr("stroke", C.grd);
      ax.selectAll(".tick line").attr("stroke", C.grd);
      ax.selectAll("text").attr("fill", C.mid).attr("font-size", 12);
    });

  g.append("g")
    .call(d3.axisLeft(y).ticks(9).tickFormat(d3.format(".0f")))
    .call(ax => {
      ax.select(".domain").attr("stroke", C.grd);
      ax.selectAll(".tick line").attr("stroke", C.grd).attr("x2", iW);
      ax.selectAll("text").attr("fill", C.mid).attr("font-size", 12);
    });

  // Axis labels
  g.append("text")
    .attr("x", iW / 2).attr("y", iH + 42).attr("text-anchor", "middle")
    .attr("fill", C.mid).attr("font-size", 12)
    .text(meta.inverse ? `${meta.label}  ←  lower is better` : meta.label);

  g.append("text")
    .attr("transform", "rotate(-90)")
    .attr("x", -iH / 2).attr("y", -44).attr("text-anchor", "middle")
    .attr("fill", C.mid).attr("font-size", 12)
    .text("Standings Points");

  // Regression line
  if (reg) {
    const xVals = d3.extent(pts, d => d.x);
    g.append("line")
      .attr("x1", x(xVals[0])).attr("y1", y(reg.slope * xVals[0] + reg.intercept))
      .attr("x2", x(xVals[1])).attr("y2", y(reg.slope * xVals[1] + reg.intercept))
      .attr("stroke", C.sec).attr("stroke-width", 2)
      .attr("stroke-dasharray", "6,3").attr("opacity", 0.7);
  }

  // Points
  g.selectAll("circle").data(pts).join("circle")
    .attr("cx", d => x(d.x))
    .attr("cy", d => y(d.y))
    .attr("r", 5)
    .attr("fill",    d => d.era === "primary" ? C.pri : "#b0b0b0")
    .attr("opacity", d => d.era === "primary" ? 0.78 : 0.55)
    .attr("stroke",  d => d.era === "primary" ? "#fff" : "#fff")
    .attr("stroke-width", 0.8)
    .on("mouseover", function(event, d) {
      d3.select(this).attr("r", 8).attr("opacity", 1);
      tip([
        {cls: "th", text: d.team},
        {cls: "tr", label: "Year",     value: d.year},
        {cls: "tr", label: meta.label, value: fmtStat(cat, d.x) + " " + meta.unit},
        {cls: "tr", label: "Pts",      value: d.y.toFixed(1)},
        {cls: "tr", label: "Era",      value: d.era === "primary" ? "Primary" : "Supplemental"},
      ], event);
    })
    .on("mousemove", mv)
    .on("mouseleave", function(e, d) {
      d3.select(this).attr("r", 5).attr("opacity", d.era === "primary" ? 0.78 : 0.55);
      ht();
    });

  // Legend
  const leg = g.append("g").attr("transform", `translate(${iW - 170}, ${iH - 42})`);
  [{fill: C.pri, op: 0.78, lbl: "Primary years (2019–25)"},
   {fill: "#b0b0b0", op: 0.55, lbl: "Supplemental (2015–18)"}].forEach(({fill, op, lbl}, i) => {
    leg.append("circle").attr("cx", 0).attr("cy", i * 17).attr("r", 5)
      .attr("fill", fill).attr("opacity", op).attr("stroke", "#fff").attr("stroke-width", 0.8);
    leg.append("text").attr("x", 10).attr("y", i * 17 + 4)
      .attr("fill", C.mid).attr("font-size", 11).text(lbl);
  });

  // Denominator annotation
  if (DENOMS[cat]) {
    const dv = DENOMS[cat].denom;
    g.append("text")
      .attr("x", iW - 4).attr("y", iH - 7).attr("text-anchor", "end")
      .attr("fill", C.sec).attr("font-size", 11).attr("font-style", "italic")
      .text(`1 pt ≈ ${fmtDenom(cat, dv)} ${meta.unit}`);
  }

  display(svg.node());
  }
}
```

<div class="callout"><strong>Reading the chart:</strong> Each dot is one team in one season. The dashed regression line summarizes the relationship — its slope directly estimates the SGP denominator. A steep slope means larger stat totals are required per standings point; a shallow slope means the category is tightly contested.</div>

<hr class="divider">

## Part 2 — Three Ways to Measure an Exchange Rate

<p class="section-meta">Comparing estimation methods on 320 cross-validated configurations</p>

<div class="narrative">
There isn't one obvious way to compute the exchange rate from historical data. We tested four methods:

<ul style="margin: 12px 0 12px 20px; line-height: 2;">
  <li><strong>Pairwise Mean</strong> — sort teams by their category total, compute the gap between each adjacent pair, average all the gaps. Simple and robust to outliers at the extremes.</li>
  <li><strong>Pairwise Median</strong> — same as above but uses the weighted median instead of mean. More resistant to extreme year-to-year swings in one category.</li>
  <li><strong>OLS Regression</strong> — fit a linear regression of standings points on category totals. The coefficient is the denominator. Leverages all data points simultaneously.</li>
  <li><strong>Robust Regression</strong> — like OLS, but uses a Huber loss that automatically down-weights outliers. Best when a few team-years have unusual values.</li>
</ul>

To evaluate which method is best, we used <strong>leave-one-year-out (LOYO) cross-validation</strong>: train on all years except one, then measure how accurately the model predicts the held-out year's denominators. The metric is <em>normalized RMSE</em> (nRMSE) — lower is better.

The strip chart below shows the nRMSE distribution across all 80 configurations per method. Each dot is one test. The vertical line marks each method's mean.
</div>

```js
// Method comparison — strip / dot plot
{
  const methods = sweep.by_method; // sorted by mean nRMSE ascending

  const W = 920, iH = 220;
  const m = {t: 24, r: 40, b: 52, l: 160};
  const iW = W - m.l - m.r;

  const allNrmse = methods.flatMap(d => d.all);
  const xMin = d3.min(allNrmse) * 0.98;
  const xMax = d3.max(allNrmse) * 1.01;
  const x = d3.scaleLinear().domain([xMin, xMax]).range([0, iW]);
  const y = d3.scaleBand()
    .domain(methods.map(d => d.method))
    .range([0, iH]).padding(0.4);

  const svg = d3.create("svg")
    .attr("width", W).attr("height", iH + m.t + m.b)
    .style("background", C.bg);

  const g = svg.append("g").attr("transform", `translate(${m.l},${m.t})`);

  // Vertical grid lines
  x.ticks(6).forEach(tv => {
    g.append("line")
      .attr("x1", x(tv)).attr("y1", 0).attr("x2", x(tv)).attr("y2", iH)
      .attr("stroke", C.grd).attr("stroke-width", 1);
  });

  // Per-method rows
  methods.forEach(md => {
    const ym = y(md.method) + y.bandwidth() / 2;
    const col = METHOD_COLORS[md.method];

    // Range line
    g.append("line")
      .attr("x1", x(md.min)).attr("y1", ym).attr("x2", x(md.max)).attr("y2", ym)
      .attr("stroke", col).attr("stroke-width", 1.5).attr("opacity", 0.3);

    // All dots (jittered vertically)
    md.all.forEach((nv, i) => {
      const jitter = ((i * 7919) % 100) / 100 - 0.5; // deterministic jitter
      g.append("circle")
        .attr("cx", x(nv)).attr("cy", ym + jitter * y.bandwidth() * 0.8)
        .attr("r", 3).attr("fill", col).attr("opacity", 0.35);
    });

    // Mean dot (larger, fully opaque)
    g.append("circle")
      .attr("cx", x(md.mean)).attr("cy", ym)
      .attr("r", 7).attr("fill", col).attr("opacity", 0.95)
      .attr("stroke", "#fff").attr("stroke-width", 1.5);

    // Mean label
    g.append("text")
      .attr("x", x(md.mean) + 11).attr("y", ym + 4)
      .attr("fill", col).attr("font-size", 11).attr("font-weight", "600")
      .text(md.mean.toFixed(4));
  });

  // Y axis (method labels)
  g.append("g")
    .call(d3.axisLeft(y).tickFormat(m => METHOD_LABELS[m]).tickSize(0))
    .call(ax => {
      ax.select(".domain").remove();
      ax.selectAll("text").attr("fill", C.txt).attr("font-size", 13).attr("font-weight", "600").attr("x", -8);
    });

  // X axis
  g.append("g").attr("transform", `translate(0,${iH})`)
    .call(d3.axisBottom(x).ticks(6).tickFormat(d3.format(".3f")))
    .call(ax => {
      ax.select(".domain").attr("stroke", C.grd);
      ax.selectAll(".tick line").attr("stroke", C.grd);
      ax.selectAll("text").attr("fill", C.mid).attr("font-size", 11);
    });

  g.append("text")
    .attr("x", iW / 2).attr("y", iH + 42).attr("text-anchor", "middle")
    .attr("fill", C.mid).attr("font-size", 12)
    .text("Normalized RMSE  (lower = more accurate)");

  // "Better" arrow
  g.append("text")
    .attr("x", 4).attr("y", iH + 42)
    .attr("fill", C.acc).attr("font-size", 11)
    .text("← better");

  display(svg.node());
}
```

<div class="callout"><strong>Key finding:</strong> OLS Regression achieves the lowest mean nRMSE (0.267), followed by Pairwise Mean (0.290). All four methods produce rank correlations above 0.95 with actual standings — the differences are real but small. The tighter spread in OLS also indicates it is more consistent across configurations.</div>

<hr class="divider">

## Part 3 — The 320-Configuration Sweep

<p class="section-meta">Every dot is one tested configuration · hover for details</p>

<div class="narrative">
Choosing a method is only one decision. Each method has additional hyperparameters that affect its behavior:

<ul style="margin: 12px 0 12px 20px; line-height: 2;">
  <li><strong>Supplemental data</strong> (on/off) — whether to include 2015–2018 seasons, which had 11 teams and only 8 categories</li>
  <li><strong>Time decay</strong> (off / 0.80 / 0.85 / 0.90) — whether to down-weight older seasons, and by how much</li>
  <li><strong>Punt detection</strong> (on/off) — whether to exclude team-years where a team deliberately tanked a category</li>
  <li><strong>Replacement buffer</strong> (30 / 40 / 50 / 60 / 70) — how deep into the player pool counts as "replacement level"</li>
</ul>

Combining 4 methods × 2 supplemental × 4 decay options × 2 punt options × 5 buffers = <strong>320 total configurations</strong>. Each was evaluated using LOYO cross-validation across 5 primary seasons (2019, 2021–2024), measuring both prediction accuracy (nRMSE) and how well the resulting valuations rank players relative to their actual standings impact (Spearman rank correlation).

The scatter below plots all 320 experiments. The ideal configuration sits in the bottom-right corner: low prediction error, high rank correlation.
</div>

```js
// Sweep scatter — all 320 configurations
{
  const configs = sweep.configs;

  const W = 920, iH = 340;
  const m = {t: 24, r: 170, b: 52, l: 64};
  const iW = W - m.l - m.r;

  const xExt = d3.extent(configs, d => d.nrmse);
  const yExt = d3.extent(configs, d => d.rank_corr);
  const xPad = (xExt[1] - xExt[0]) * 0.05;
  const yPad = (yExt[1] - yExt[0]) * 0.05;

  const x = d3.scaleLinear().domain([xExt[0] - xPad, xExt[1] + xPad]).range([0, iW]);
  const y = d3.scaleLinear().domain([yExt[0] - yPad, yExt[1] + yPad]).range([iH, 0]);

  const svg = d3.create("svg")
    .attr("width", W).attr("height", iH + m.t + m.b)
    .style("background", C.bg);

  const g = svg.append("g").attr("transform", `translate(${m.l},${m.t})`);

  // Grid
  x.ticks(6).forEach(tv => {
    g.append("line").attr("x1", x(tv)).attr("y1", 0).attr("x2", x(tv)).attr("y2", iH)
      .attr("stroke", C.grd).attr("stroke-width", 1);
  });
  y.ticks(6).forEach(tv => {
    g.append("line").attr("x1", 0).attr("y1", y(tv)).attr("x2", iW).attr("y2", y(tv))
      .attr("stroke", C.grd).attr("stroke-width", 1);
  });

  // Points
  g.selectAll("circle").data(configs).join("circle")
    .attr("cx", d => x(d.nrmse))
    .attr("cy", d => y(d.rank_corr))
    .attr("r", 4)
    .attr("fill", d => METHOD_COLORS[d.method])
    .attr("opacity", 0.45)
    .attr("stroke", "none")
    .on("mouseover", function(event, d) {
      d3.select(this).attr("r", 7).attr("opacity", 1);
      tip([
        {cls: "th", text: METHOD_LABELS[d.method], color: METHOD_COLORS[d.method]},
        {cls: "tr", label: "nRMSE",         value: d.nrmse.toFixed(4)},
        {cls: "tr", label: "Rank corr",      value: d.rank_corr.toFixed(4)},
        {cls: "tr", label: "Supplemental",   value: d.supp  ? "Yes" : "No"},
        {cls: "tr", label: "Time decay",     value: d.decay ? "Yes" : "No"},
        {cls: "tr", label: "Punt detection", value: d.punt  ? "Yes" : "No"},
      ], event);
    })
    .on("mousemove", mv)
    .on("mouseleave", function() {
      d3.select(this).attr("r", 4).attr("opacity", 0.45);
      ht();
    });

  // Best config marker
  const best = configs.reduce((a, b) => a.nrmse < b.nrmse ? a : b);
  g.append("circle")
    .attr("cx", x(best.nrmse)).attr("cy", y(best.rank_corr))
    .attr("r", 9).attr("fill", "none")
    .attr("stroke", C.txt).attr("stroke-width", 2).attr("stroke-dasharray", "3,2");
  g.append("text")
    .attr("x", x(best.nrmse) + 12).attr("y", y(best.rank_corr) + 4)
    .attr("fill", C.txt).attr("font-size", 11).text("Best overall");

  // Axes
  g.append("g").attr("transform", `translate(0,${iH})`)
    .call(d3.axisBottom(x).ticks(6).tickFormat(d3.format(".3f")))
    .call(ax => {
      ax.select(".domain").attr("stroke", C.grd);
      ax.selectAll(".tick line").attr("stroke", C.grd);
      ax.selectAll("text").attr("fill", C.mid).attr("font-size", 11);
    });

  g.append("g")
    .call(d3.axisLeft(y).ticks(6).tickFormat(d3.format(".3f")))
    .call(ax => {
      ax.select(".domain").attr("stroke", C.grd);
      ax.selectAll(".tick line").attr("stroke", C.grd).attr("x2", iW);
      ax.selectAll("text").attr("fill", C.mid).attr("font-size", 11);
    });

  g.append("text")
    .attr("x", iW / 2).attr("y", iH + 42).attr("text-anchor", "middle")
    .attr("fill", C.mid).attr("font-size", 12)
    .text("Normalized RMSE  ←  lower is better");

  g.append("text")
    .attr("transform", "rotate(-90)")
    .attr("x", -iH / 2).attr("y", -52).attr("text-anchor", "middle")
    .attr("fill", C.mid).attr("font-size", 12)
    .text("Rank Correlation  →  higher is better");

  // Legend
  const lx = iW + 16;
  g.append("text").attr("x", lx).attr("y", 10)
    .attr("fill", C.lit).attr("font-size", 11).attr("font-weight", "600")
    .attr("text-transform", "uppercase").text("METHOD");
  Object.entries(METHOD_LABELS).forEach(([k, v], i) => {
    g.append("circle").attr("cx", lx + 5).attr("cy", 26 + i * 19)
      .attr("r", 5).attr("fill", METHOD_COLORS[k]).attr("opacity", 0.8);
    g.append("text").attr("x", lx + 14).attr("y", 30 + i * 19)
      .attr("fill", C.mid).attr("font-size", 11).text(v);
  });

  display(svg.node());
}
```

<div class="callout"><strong>What the sweep shows:</strong> All 320 configurations land in a narrow band (nRMSE 0.244–0.340, rank correlation 0.954–0.971). The model is well-constrained — the data is sufficient to produce reliable estimates regardless of which reasonable method is used. The best single configuration is OLS Regression with supplemental data, no time decay.</div>

<hr class="divider">

## Part 4 — The Composite Approach

<p class="section-meta">One method isn't best for every category</p>

<div class="narrative">
Although OLS wins overall, the sweep reveals that each scoring category has its own best-performing method. Pitcher wins (W) are notoriously volatile — some teams deliberately stream pitchers to accumulate wins, creating outlier years. Saves (SV) have enough distributional quirks (blown saves, closer injuries, tanking) that a robust estimator outperforms OLS. Batting average benefits from pairwise estimation since each team's lineup has a very different plate-appearance count.

The <strong>composite model</strong> runs each category's calibration independently, using whichever method minimized its nRMSE in cross-validation. This per-category tuning reduces the overall error compared to any single global method.
</div>

```js
// Composite config table
{
  const cats = ["R","HR","RBI","SB","AVG","W","SV","ERA","WHIP","SO"];

  const wrap = document.createElement("div");
  wrap.style.cssText = "overflow-x:auto;margin:16px 0 28px;";

  const table = document.createElement("table");
  table.className = "config-table";

  // Header
  const thead = document.createElement("thead");
  const hrow  = document.createElement("tr");
  ["Category", "Method selected", "Supplemental data", "Time decay", "Punt detection"].forEach(h => {
    const th = document.createElement("th"); th.textContent = h; hrow.appendChild(th);
  });
  thead.appendChild(hrow); table.appendChild(thead);

  // Body
  const tbody = document.createElement("tbody");
  cats.forEach(cat => {
    const cfg = COMPOSITE[cat];
    const col = METHOD_COLORS[cfg.method];
    const tr  = document.createElement("tr");

    // Category label
    const catTd = document.createElement("td");
    catTd.className = "cat-label";
    catTd.style.cssText = `font-weight:700;color:${CAT_META[cat].batting ? C.pri : C.acc};font-family:'IBM Plex Mono',monospace;font-size:12px;`;
    catTd.textContent = cat + " — " + CAT_META[cat].label;
    tr.appendChild(catTd);

    // Method badge
    const methodTd = document.createElement("td");
    const badge    = document.createElement("span");
    badge.className = "method-badge";
    badge.textContent = METHOD_LABELS[cfg.method];
    badge.style.cssText = `display:inline-block;padding:3px 9px;border-radius:4px;font-size:11px;font-weight:600;background:${col}18;color:${col};border:1px solid ${col}40;`;
    methodTd.appendChild(badge); tr.appendChild(methodTd);

    // Boolean cells
    [cfg.supp, cfg.decay, cfg.punt].forEach(v => {
      const td = document.createElement("td");
      td.style.cssText = `text-align:center;font-size:13px;color:${v ? C.acc : C.grd};font-weight:${v ? 700 : 400};`;
      td.textContent = v ? "✓" : "—";
      tr.appendChild(td);
    });

    tbody.appendChild(tr);
  });

  table.appendChild(tbody);
  wrap.appendChild(table);
  display(wrap);
}
```

<hr class="divider">

## Part 5 — The Final Denominators

<p class="section-meta">Calibrated exchange rates with 95% bootstrap confidence intervals</p>

<div class="narrative">
The composite model produces the final SGP denominators used to price every player in the auction. These are the answers to: <em>"how many [stat units] does it take to gain one standings point?"</em>

Categories with available 95% confidence intervals (from 2,000 bootstrap resamples) are shown with error bars. Categories estimated by OLS or Robust Regression use analytical standard errors, which are not yet reported here — those CI bands appear as null.

Bars are normalized to show each denominator as a percentage of the category's typical annual spread in Moonlight Graham, making batting and pitching categories directly comparable.
</div>

```js
// Denominator bar chart — normalized to % of league spread
{
  const cats = ["R","HR","RBI","SB","AVG","W","SV","ERA","WHIP","SO"];

  // Compute mean annual spread from standings data (max - min per year, averaged)
  const catSpread = {};
  cats.forEach(cat => {
    const years = [...new Set(standings.map(d => d.year))];
    const spreads = years.map(yr => {
      const vals = standings.filter(d => d.year === yr && d[cat] != null).map(d => d[cat]);
      if (vals.length < 2) return null;
      // For inverse cats, spread is still max-min (positive)
      return d3.max(vals) - d3.min(vals);
    }).filter(v => v !== null && v > 0);
    catSpread[cat] = d3.mean(spreads);
  });

  // Build bar data
  const bars = cats.map(cat => {
    const d     = DENOMS[cat];
    const spread = catSpread[cat] || 1;
    const pct   = (d.denom / spread) * 100;
    const pctLo = d.ci_low  != null ? (d.ci_low  / spread) * 100 : null;
    const pctHi = d.ci_high != null ? (d.ci_high / spread) * 100 : null;
    return {cat, pct, pctLo, pctHi, denom: d.denom, method: d.method, batting: d.batting};
  });

  const W = 920, iH = 320;
  const m = {t: 20, r: 220, b: 52, l: 68};
  const iW = W - m.l - m.r;

  const yMax = d3.max(bars, d => d.pct) * 1.12;
  const x    = d3.scaleBand().domain(cats).range([0, iW]).padding(0.28);
  const y    = d3.scaleLinear().domain([0, yMax]).range([iH, 0]);

  const svg = d3.create("svg")
    .attr("width", W).attr("height", iH + m.t + m.b)
    .style("background", C.bg);

  const g = svg.append("g").attr("transform", `translate(${m.l},${m.t})`);

  // Grid
  y.ticks(5).forEach(tv => {
    g.append("line").attr("x1", 0).attr("y1", y(tv)).attr("x2", iW).attr("y2", y(tv))
      .attr("stroke", C.grd).attr("stroke-width", 1);
  });

  // Batting / pitching separator
  const sbX = x("AVG") + x.bandwidth() + x.step() * x.paddingInner() / 2;
  g.append("line")
    .attr("x1", sbX).attr("y1", 0).attr("x2", sbX).attr("y2", iH)
    .attr("stroke", C.grd).attr("stroke-width", 1.5).attr("stroke-dasharray", "4,3");
  g.append("text")
    .attr("x", sbX / 2).attr("y", -6).attr("text-anchor", "middle")
    .attr("fill", C.lit).attr("font-size", 10).attr("font-weight", "600")
    .attr("text-transform", "uppercase").text("BATTING");
  g.append("text")
    .attr("x", sbX + (iW - sbX) / 2).attr("y", -6).attr("text-anchor", "middle")
    .attr("fill", C.lit).attr("font-size", 10).attr("font-weight", "600").text("PITCHING");

  // Bars
  bars.forEach(d => {
    const col = d.batting ? C.pri : C.acc;
    const bx  = x(d.cat);
    const bw  = x.bandwidth();

    // Bar
    g.append("rect")
      .attr("x", bx).attr("y", y(d.pct))
      .attr("width", bw).attr("height", iH - y(d.pct))
      .attr("fill", col).attr("opacity", 0.75).attr("rx", 2);

    // CI error bar
    if (d.pctLo != null && d.pctHi != null) {
      const cx = bx + bw / 2;
      g.append("line")
        .attr("x1", cx).attr("y1", y(d.pctLo)).attr("x2", cx).attr("y2", y(d.pctHi))
        .attr("stroke", col).attr("stroke-width", 1.5).attr("opacity", 0.9);
      [-1,1].forEach(side => {
        g.append("line")
          .attr("x1", cx - 4).attr("y1", y(side === -1 ? d.pctLo : d.pctHi))
          .attr("x2", cx + 4).attr("y2", y(side === -1 ? d.pctLo : d.pctHi))
          .attr("stroke", col).attr("stroke-width", 1.5).attr("opacity", 0.9);
      });
    }

    // Value label above bar
    g.append("text")
      .attr("x", bx + bw / 2).attr("y", y(d.pct) - 5).attr("text-anchor", "middle")
      .attr("fill", col).attr("font-size", 10).attr("font-weight", "600")
      .text(fmtDenom(d.cat, d.denom));
  });

  // Axes
  g.append("g")
    .call(d3.axisLeft(y).ticks(5).tickFormat(d => d + "%"))
    .call(ax => {
      ax.select(".domain").attr("stroke", C.grd);
      ax.selectAll(".tick line").attr("stroke", C.grd).attr("x2", iW);
      ax.selectAll("text").attr("fill", C.mid).attr("font-size", 11);
    });

  g.append("g").attr("transform", `translate(0,${iH})`)
    .call(d3.axisBottom(x).tickSize(0))
    .call(ax => {
      ax.select(".domain").attr("stroke", C.grd);
      ax.selectAll("text").attr("fill", C.txt).attr("font-size", 13).attr("font-weight", "600").attr("dy", "1.1em");
    });

  g.append("text")
    .attr("transform", "rotate(-90)")
    .attr("x", -iH / 2).attr("y", -54).attr("text-anchor", "middle")
    .attr("fill", C.mid).attr("font-size", 12)
    .text("Denominator as % of typical league spread");

  // Method legend (right side)
  const lx = iW + 16;
  g.append("text").attr("x", lx).attr("y", 10)
    .attr("fill", C.lit).attr("font-size", 10).attr("font-weight", "600")
    .text("METHOD USED");
  Object.entries(METHOD_LABELS).forEach(([k, v], i) => {
    const col = METHOD_COLORS[k];
    g.append("rect").attr("x", lx).attr("y", 20 + i * 22)
      .attr("width", 10).attr("height", 10).attr("rx", 2)
      .attr("fill", col).attr("opacity", 0.8);
    g.append("text").attr("x", lx + 14).attr("y", 30 + i * 22)
      .attr("fill", C.mid).attr("font-size", 11).text(v);
  });

  // Category method dots
  bars.forEach(d => {
    const bx = x(d.cat);
    const bw = x.bandwidth();
    const col = METHOD_COLORS[d.method];
    g.append("circle")
      .attr("cx", bx + bw / 2).attr("cy", iH + 34)
      .attr("r", 4).attr("fill", col).attr("opacity", 0.85);
  });
  g.append("text")
    .attr("x", iW / 2).attr("y", iH + 50).attr("text-anchor", "middle")
    .attr("fill", C.lit).attr("font-size", 9)
    .text("● = method used for each category");

  display(svg.node());
}
```

<div class="callout"><strong>Reading the bars:</strong> Each bar shows the denominator as a share of how spread out that category typically is in a Moonlight Graham season. Values cluster around 10–25%, meaning each standings position is worth roughly one-seventh to one-fifth of the category's annual competitive range. Error bars show 95% bootstrap confidence intervals where available. The colored dot below each bar indicates which estimation method was used.</div>

<hr class="divider">

## Part 6 — How Stable Are These Estimates?

<p class="section-meta">Year-over-year denominator variation · select a category</p>

<div class="narrative">
A calibration is only trustworthy if it's stable over time. If the denominator for Home Runs swings wildly from year to year — 5 in 2021, 18 in 2024 — then our estimate is noisy and the resulting dollar values unreliable.

The chart below shows the per-year denominator for each category. Each dot is what we would have estimated using only that single season. The dashed line is the final composite estimate — the value we actually use.

Wide scatter above and below the reference line means the category is volatile; tight scatter means the denominator is consistent and well-measured. Categories like HR and RBI are reassuringly stable; Stolen Bases and Pitcher Wins have grown substantially in recent years as the game evolved.
</div>

```js
const stabCat = Mutable("HR");
const setStabCat = (cat) => { stabCat.value = cat; };
```

```js
// Category selector for stability chart
{
  const batting  = ["R","HR","RBI","SB","AVG"];
  const pitching = ["W","SV","ERA","WHIP","SO"];

  const bar = document.createElement("div");
  bar.className = "filter-bar";
  bar.style.marginBottom = "14px";

  function addGroup(label, cats) {
    const lbl = document.createElement("span");
    lbl.className = "filter-label"; lbl.textContent = label + ":";
    bar.appendChild(lbl);
    const pills = makePills(cats, stabCat, setStabCat);
    bar.appendChild(pills);
  }

  addGroup("Batting",  batting);
  addGroup("Pitching", pitching);
  display(bar);
}
```

```js
// Year stability chart (reactive on stabCat)
{
  const cat      = stabCat;
  const meta     = CAT_META[cat];
  const yearData = YEAR_LEVEL[cat];
  const overall  = DENOMS[cat].denom;

  if (!yearData) { display(html`<p style="color:#999;font-size:13px;font-style:italic">No year-level data for this category.</p>`); } else {

  const PRIMARY_YEARS = new Set([2019, 2021, 2022, 2023, 2024, 2025]);

  const pts = Object.entries(yearData).map(([yr, v]) => ({
    year: +yr,
    denom: v,
    era: PRIMARY_YEARS.has(+yr) ? "primary" : "supplemental",
  })).sort((a, b) => a.year - b.year);

  const W = 920, iH = 290;
  const m = {t: 24, r: 48, b: 52, l: 72};
  const iW = W - m.l - m.r;

  const xYears = pts.map(d => d.year);
  const xMin   = d3.min(xYears) - 0.5;
  const xMax   = d3.max(xYears) + 0.5;
  const allVals  = pts.map(d => d.denom).concat([overall]);
  const yPad   = (d3.max(allVals) - d3.min(allVals)) * 0.18;
  const yMin   = Math.max(0, d3.min(allVals) - yPad);
  const yMax   = d3.max(allVals) + yPad;

  const x = d3.scaleLinear().domain([xMin, xMax]).range([0, iW]);
  const y = d3.scaleLinear().domain([yMin, yMax]).range([iH, 0]);

  const svg = d3.create("svg")
    .attr("width", W).attr("height", iH + m.t + m.b)
    .style("background", C.bg);

  const g = svg.append("g").attr("transform", `translate(${m.l},${m.t})`);

  // Grid
  y.ticks(5).forEach(tv => {
    g.append("line").attr("x1", 0).attr("y1", y(tv)).attr("x2", iW).attr("y2", y(tv))
      .attr("stroke", C.grd).attr("stroke-width", 1);
  });

  // 2020 exclusion band
  g.append("rect")
    .attr("x", x(2019.55)).attr("y", 0).attr("width", x(2020.45) - x(2019.55)).attr("height", iH)
    .attr("fill", "#f5f4f0").attr("opacity", 0.8);
  g.append("text")
    .attr("x", x(2020)).attr("y", 14).attr("text-anchor", "middle")
    .attr("fill", C.lit).attr("font-size", 10).text("COVID");

  // Overall estimate reference line
  g.append("line")
    .attr("x1", 0).attr("y1", y(overall)).attr("x2", iW).attr("y2", y(overall))
    .attr("stroke", C.sec).attr("stroke-width", 2).attr("stroke-dasharray", "6,4").attr("opacity", 0.7);

  g.append("text")
    .attr("x", iW + 4).attr("y", y(overall) + 4)
    .attr("fill", C.sec).attr("font-size", 11)
    .text("→ " + fmtDenom(cat, overall));

  // Line connecting primary years
  const primaryPts = pts.filter(d => d.era === "primary");
  if (primaryPts.length > 1) {
    const line = d3.line().x(d => x(d.year)).y(d => y(d.denom)).curve(d3.curveMonotoneX);
    g.append("path")
      .attr("d", line(primaryPts))
      .attr("fill", "none")
      .attr("stroke", C.pri).attr("stroke-width", 1.5).attr("opacity", 0.4);
  }

  // Dots
  pts.forEach(d => {
    const col  = d.era === "primary" ? C.pri : "#aaa";
    const r    = d.era === "primary" ? 7 : 5;
    const fill = d.era === "primary" ? col : "#ccc";

    g.append("circle")
      .attr("cx", x(d.year)).attr("cy", y(d.denom))
      .attr("r", r).attr("fill", fill).attr("stroke", d.era === "primary" ? "#fff" : "#e8e8e8")
      .attr("stroke-width", 1.5).attr("opacity", d.era === "primary" ? 0.9 : 0.7)
      .on("mouseover", function(event) {
        d3.select(this).attr("r", r + 3).attr("opacity", 1);
        tip([
          {cls: "th", text: String(d.year)},
          {cls: "tr", label: "Denominator", value: fmtDenom(cat, d.denom) + " " + meta.unit},
          {cls: "tr", label: "vs. final",   value: (((d.denom - overall) / overall) * 100).toFixed(1) + "% diff", valCls: d.denom > overall ? "pos" : "neg"},
          {cls: "tr", label: "Era",         value: d.era === "primary" ? "Primary" : "Supplemental"},
        ], event);
      })
      .on("mousemove", mv)
      .on("mouseleave", function() {
        d3.select(this).attr("r", r).attr("opacity", d.era === "primary" ? 0.9 : 0.7);
        ht();
      });

    // Year label below dot
    g.append("text")
      .attr("x", x(d.year)).attr("y", iH + 36)
      .attr("text-anchor", "middle")
      .attr("fill", d.era === "primary" ? C.txt : C.lit)
      .attr("font-size", d.era === "primary" ? 11 : 10)
      .attr("font-weight", d.era === "primary" ? "600" : "400")
      .text(d.year);
  });

  // Y axis
  g.append("g")
    .call(d3.axisLeft(y).ticks(5).tickFormat(v => {
      if (cat === "AVG" || cat === "ERA" || cat === "WHIP") return v.toFixed(3);
      return d3.format(".0f")(v);
    }))
    .call(ax => {
      ax.select(".domain").attr("stroke", C.grd);
      ax.selectAll(".tick line").attr("stroke", C.grd).attr("x2", iW);
      ax.selectAll("text").attr("fill", C.mid).attr("font-size", 11);
    });

  // Bottom axis (years via ticks, not labels — labels added manually above)
  g.append("g").attr("transform", `translate(0,${iH})`)
    .call(d3.axisBottom(x).tickValues(xYears).tickFormat("").tickSize(4))
    .call(ax => {
      ax.select(".domain").attr("stroke", C.grd);
      ax.selectAll(".tick line").attr("stroke", C.grd);
    });

  g.append("text")
    .attr("transform", "rotate(-90)")
    .attr("x", -iH / 2).attr("y", -58).attr("text-anchor", "middle")
    .attr("fill", C.mid).attr("font-size", 12)
    .text(`${meta.label} — standings points per ${meta.unit}`);

  // Legend
  [{fill: C.pri, lbl: "Primary year estimate"},
   {fill: "#ccc", lbl: "Supplemental estimate"},
   {fill: C.sec, lbl: "Final composite estimate", dash: true}]
  .forEach(({fill, lbl, dash}, i) => {
    const lx = 12, ly = iH - 52 + i * 18;
    if (dash) {
      g.append("line")
        .attr("x1", lx).attr("y1", ly - 4).attr("x2", lx + 18).attr("y2", ly - 4)
        .attr("stroke", fill).attr("stroke-width", 2).attr("stroke-dasharray", "5,3");
    } else {
      g.append("circle").attr("cx", lx + 5).attr("cy", ly - 4).attr("r", 5)
        .attr("fill", fill).attr("opacity", 0.8);
    }
    g.append("text").attr("x", lx + 22).attr("y", ly)
      .attr("fill", C.mid).attr("font-size", 11).text(lbl);
  });

  display(svg.node());
  }
}
```

<div class="callout"><strong>What to look for:</strong> Stolen bases and pitcher wins show strong upward trends in recent seasons as the game has changed — MLB's base-stealing renaissance (2023–25) has expanded SB denominators from ~7 to ~15. This is why time decay is enabled for those categories in the composite model, to ensure recent patterns carry more weight.</div>

<hr class="divider">

## What the Numbers Mean

```js
// Synthesis box
{
  const box = document.createElement("div");
  box.className = "synthesis";

  const h2 = document.createElement("h2");
  h2.textContent = "From Denominator to Dollar Value";
  box.appendChild(h2);

  const grid = document.createElement("div"); grid.className = "synthesis-grid";

  const items = [
    {
      term: "The denominator converts stats to points",
      def: "Divide any player's projected stat total by the category's denominator to get their expected standings-point contribution: SGP = stat ÷ denominator. A player projected for 30 HR contributes 30 ÷ 12.2 ≈ 2.5 standings points in the HR category.",
    },
    {
      term: "PAR measures value above replacement",
      def: "A replacement-level player (the last rostered player in the league) has some baseline SGP contribution. Points Above Replacement (PAR) = total SGP − replacement SGP. Only positive-PAR players have genuine auction value.",
    },
    {
      term: "Dollar values come from PAR allocation",
      def: "The total salary pool ($2,600) is distributed proportionally to PAR: every dollar buys the same amount of standings points. A player with PAR = 4.0 out of a total positive-PAR pool of 400 commands (4.0 / 400) × $2,600 ≈ $26.",
    },
    {
      term: "Denominators change with the game",
      def: "SGP values are not static. The calibration runs fresh each season. As stolen bases became common again in 2023–25, SB denominators rose — meaning each stolen base is worth less than it was five years ago.",
    },
  ];

  items.forEach(({term, def}) => {
    const item = document.createElement("div"); item.className = "synthesis-item";
    const dt = document.createElement("dt"); dt.textContent = term;
    const dd = document.createElement("dd"); dd.textContent = def;
    item.append(dt, dd); grid.appendChild(item);
  });

  box.appendChild(grid);
  display(box);
}
```
