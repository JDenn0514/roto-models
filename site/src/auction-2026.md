---
title: 2026 Moonlight Graham Auction Analysis
date: 2026-04-01
description: Full post-draft breakdown — value vs. price, team spending patterns, position inflation, and the Gusteroids surplus story.
tags: [auction, interactive]
---

```js
display(html`<div class="report-nav">
  <a href="/roto-models/" class="back-link">← All Reports</a>
  <span class="report-nav-wordmark">Moonlight Graham</span>
</div>`);
```

```js
// ── Data ──────────────────────────────────────────────────────────────────
const DATA = FileAttachment("data/auction.json").json();
```

```js
// ── Design constants ──────────────────────────────────────────────────────
const TC = {
  "Dancing With Dingos": "#457B9D",
  "Gusteroids":          "#C1666B",
  "HAMMERHEADS":         "#2A9D8F",
  "Kerry & Mitch":       "#D4A373",
  "Kosher Hogs":         "#7B6D8D",
  "Mean Machine":        "#8FB996",
  "On a Bender":         "#E07A5F",
  "R&R":                 "#3A6EA5",
  "Shrooms":             "#5F7A4A",
  "Thunder & Lightning": "#B5892B",
};
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
```

```js
// ── Tooltip (safe DOM construction — no innerHTML) ────────────────────────
const tt = (() => {
  const div = document.createElement("div");
  div.className = "auction-tooltip";
  document.body.appendChild(div);
  invalidation.then(() => div.remove());
  return div;
})();

// Build a tooltip row element
function tipRow(label, value, valCls) {
  const row = document.createElement("div");
  row.className = "tr";
  const lbl = document.createElement("span");
  lbl.className = "tl";
  lbl.textContent = label;
  const val = document.createElement("span");
  val.className = valCls ? `tv ${valCls}` : "tv";
  val.textContent = value;
  row.append(lbl, val);
  return row;
}

// Show tooltip: specs = array of {cls, text, color?, label?, value?, valCls?}
function tip(specs, e) {
  tt.replaceChildren(...specs.map(s => {
    if (s.cls === "tr") return tipRow(s.label, s.value, s.valCls);
    const el = document.createElement("div");
    el.className = s.cls;
    el.textContent = s.text;
    if (s.color) el.style.color = s.color;
    return el;
  }));
  tt.style.opacity = "1";
  mv(e);
}
function mv(e) {
  const x = e.clientX, y = e.clientY, tw = 240, th = 140;
  tt.style.left = (x + 14 + tw > window.innerWidth  ? x - tw - 14 : x + 14) + "px";
  tt.style.top  = (y + 14 + th > window.innerHeight ? y - th - 14 : y + 14) + "px";
}
function ht() { tt.style.opacity = "0"; }
```

```js
// ── Value helpers ─────────────────────────────────────────────────────────
function fs(v) {
  if (v == null) return "—";
  return v >= 0 ? `+$${v.toFixed(1)}` : `-$${Math.abs(v).toFixed(1)}`;
}
function sc(v)       { return v == null ? "" : v >= 0 ? "pos" : "neg"; }
function gv(d, mode) { return mode === "single" ? d.dollar_value      : d.split_dollar_value; }
function gs(d, mode) { return mode === "single" ? d.surplus            : d.split_surplus; }

// Stable per-player jitter for spending chart (avoids jumpy re-renders)
function stableJitter(str) {
  let h = 0;
  for (let i = 0; i < str.length; i++) h = Math.imul(31, h) + str.charCodeAt(i) | 0;
  return ((Math.abs(h) % 1000) / 1000) - 0.5;
}
```

```js
// ── Input factories ───────────────────────────────────────────────────────
// Creates a single-pool / split-pool toggle pill
function makeToggle() {
  const wrap = document.createElement("div");
  wrap.className = "filter-bar";
  wrap.style.marginBottom = "8px";

  const lbl = document.createElement("span");
  lbl.className = "filter-label";
  lbl.textContent = "Valuation model:";
  wrap.appendChild(lbl);

  const pill = document.createElement("div");
  pill.className = "toggle-pill";

  ["Single Pool", "Split Pool"].forEach((label, i) => {
    const btn = document.createElement("button");
    btn.className = i === 0 ? "tpill active" : "tpill";
    btn.textContent = label;
    btn.dataset.v = i === 0 ? "single" : "split";
    btn.addEventListener("click", () => {
      pill.querySelectorAll(".tpill").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      wrap.value = btn.dataset.v;
      wrap.dispatchEvent(new Event("input", {bubbles: true}));
    });
    pill.appendChild(btn);
  });

  wrap.appendChild(pill);
  wrap.value = "single";
  return wrap;
}

// Creates team-colored filter chips (empty Set = show all)
function makeTeamChips() {
  const chips = {};
  let selected = new Set();

  const wrap = document.createElement("div");
  wrap.className = "filter-bar";

  const lbl = document.createElement("span");
  lbl.className = "filter-label";
  lbl.textContent = "Highlight team:";
  wrap.appendChild(lbl);

  const row = document.createElement("span");
  wrap.appendChild(row);

  const resetLink = document.createElement("span");
  resetLink.className = "reset-link";
  resetLink.textContent = "Reset";
  resetLink.style.display = "none";
  wrap.appendChild(resetLink);

  Object.entries(TC).forEach(([team, color]) => {
    const chip = document.createElement("span");
    chip.className = "team-chip";

    const dot = document.createElement("span");
    dot.style.cssText = `width:9px;height:9px;border-radius:50%;background:${color};display:inline-block;flex-shrink:0`;
    const name = document.createElement("span");
    name.textContent = team;
    chip.append(dot, name);

    chip.addEventListener("click", () => {
      if (selected.size === 0) selected.add(team);
      else if (selected.has(team)) selected.delete(team);
      else selected.add(team);
      sync();
    });

    chips[team] = chip;
    row.appendChild(chip);
  });

  resetLink.addEventListener("click", () => { selected.clear(); sync(); });

  function sync() {
    const none = selected.size === 0;
    resetLink.style.display = none ? "none" : "inline";
    Object.entries(chips).forEach(([t, c]) =>
      c.classList.toggle("dimmed", !none && !selected.has(t))
    );
    wrap.value = new Set(selected);
    wrap.dispatchEvent(new Event("input", {bubbles: true}));
  }

  wrap.value = new Set();
  return wrap;
}
```

# Moonlight Graham 2026 Auction Analysis

_AL-only keeper league &middot; 10 teams &middot; $260/team budget &middot; March 2026 &middot; Valuations: ATC projections via SGP model_

```js
{
  const players  = DATA.players;
  const total    = d3.sum(players, d => d.price);
  const avg      = d3.mean(players, d => d.price);
  const topPrice = d3.max(players, d => d.price);
  const topName  = players.find(d => d.price === topPrice)?.player?.split(" ").slice(-1)[0] ?? "";
  const oneDollar = players.filter(d => d.price === 1).length;

  const cards = [
    {val: String(players.length),            lbl: "Players Auctioned"},
    {val: `$${total.toLocaleString()}`,       lbl: "Total Auction Spend"},
    {val: `$${avg.toFixed(2)}`,               lbl: "Average Price Paid"},
    {val: `$${topPrice}`,                     lbl: `Top Sale · ${topName}`},
    {val: String(oneDollar),                  lbl: "$1 Nominations Won"},
  ];

  const grid = document.createElement("div");
  grid.className = "stat-grid";
  cards.forEach(c => {
    const card = document.createElement("div");
    card.className = "stat-card";
    const valEl = document.createElement("div");
    valEl.className = "val";
    valEl.textContent = c.val;
    const lblEl = document.createElement("div");
    lblEl.className = "lbl";
    lblEl.textContent = c.lbl;
    card.append(valEl, lblEl);
    grid.appendChild(card);
  });
  display(grid);
}
```

<hr class="chart-divider">

## Price vs. Model Value — All 119 Players

<p class="section-meta">Hover any dot for details · Click team chips to filter · Toggle shifts pitcher dot positions</p>

<div class="narrative">
Every auctioned player sits on this chart. The diagonal is <strong>fair value</strong> — points above it cost
more than the model predicted; points below were bargains. No team finished in positive territory:
every dot cluster sits above the line on balance, which is the structural signature of keeper league
inflation — all ten teams arrive with their full $260 budgets but compete over a reduced player pool
after keepers are removed.
<br><br>
The two valuation models tell materially different stories here.
Under <strong>single pool</strong>, hitter and pitcher model values share the same $/PAR rate, so the
scatter looks balanced — pitchers and hitters both cluster near the line with similar scatter.
Switch to <strong>split pool</strong> and the picture reorganizes: <em>pitcher dots shift left</em>
(their model values fall ~23%, to $3.11/PAR) while <em>hitter dots shift right</em> (their values
rise ~25%, to $5.06/PAR). The effect is that the same price paid now looks like an overpay for most
pitchers and better value for most hitters.
<br><br>
The biggest bargains were pitchers under single pool — <strong>Tanner Bibee</strong> (+$9.5),
<strong>Sonny Gray</strong> (+$7.0), <strong>Ranger Suárez</strong> (+$6.8) — but their surpluses
shrink substantially under split pool (+$4.4, +$0.9, +$1.9), suggesting the market was closer to
correctly pricing these pitchers than single pool implies. The steepest overpays —
<strong>José Ramírez</strong> (-$15.6), <strong>Maikel Garcia</strong> (-$14.3),
<strong>Wyatt Langford</strong> (-$13.4) — are on the hitting side and are relatively stable across
both models, reinforcing that the top-of-market premium on elite hitters is a real, model-independent phenomenon.
</div>

```js
const scatterMode = view(makeToggle());
```
```js
const selectedTeams = view(makeTeamChips());
```

```js
{
  const W = Math.min(width, 900);
  const m = {t: 20, r: 30, b: 50, l: 58};
  const iW = W - m.l - m.r, iH = 500 - m.t - m.b;

  const pd   = DATA.players.filter(d => d.dollar_value != null);
  const maxV = Math.max(d3.max(pd, d => d.dollar_value), d3.max(pd, d => d.price)) + 5;
  const x    = d3.scaleLinear().domain([0, maxV]).range([0, iW]);
  const y    = d3.scaleLinear().domain([0, maxV]).range([iH, 0]);
  const none = selectedTeams.size === 0;

  const svg = d3.create("svg").attr("width", W).attr("height", iH + m.t + m.b).style("background", C.bg);
  const g   = svg.append("g").attr("transform", `translate(${m.l},${m.t})`);

  g.selectAll(".gy").data(y.ticks(6)).join("line")
    .attr("x1", 0).attr("x2", iW).attr("y1", d => y(d)).attr("y2", d => y(d))
    .attr("stroke", C.grd).attr("stroke-width", 0.5);

  g.append("line")
    .attr("x1", x(0)).attr("y1", y(0)).attr("x2", x(maxV)).attr("y2", y(maxV))
    .attr("stroke", C.lit).attr("stroke-width", 1.3).attr("stroke-dasharray", "5 4").attr("opacity", 0.55);
  g.append("text")
    .attr("x", x(maxV) - 4).attr("y", y(maxV) + 14)
    .attr("text-anchor", "end").attr("fill", C.lit).attr("font-size", 10).text("fair value");

  g.selectAll(".sdot").data(pd).join("circle").attr("class", "sdot")
    .attr("cx", d => x(gv(d, scatterMode)))
    .attr("cy", d => y(d.price))
    .attr("r",       d => none || selectedTeams.has(d.team) ? 5.5 : 3.5)
    .attr("fill",    d => none || selectedTeams.has(d.team) ? TC[d.team] : "#c8c8c8")
    .attr("opacity", d => none || selectedTeams.has(d.team) ? 0.8 : 0.18)
    .attr("stroke", "#faf9f5").attr("stroke-width", 0.8).style("cursor", "pointer")
    .on("mouseover", function(e, d) {
      d3.select(this).attr("r", 8).attr("stroke", C.txt).attr("stroke-width", 1.5);
      const sv = gs(d, scatterMode);
      tip([
        {cls: "tp", text: d.player},
        {cls: "tm", text: d.team, color: TC[d.team]},
        {cls: "tr", label: "Price paid",   value: `$${d.price}`},
        {cls: "tr", label: "Model value",  value: `$${gv(d, scatterMode)}`},
        {cls: "tr", label: "Surplus",      value: fs(sv), valCls: sc(sv)},
        {cls: "tr", label: "Position",     value: d.position},
        {cls: "tr", label: "Nom #",        value: `#${d.nom}`},
      ], e);
    })
    .on("mousemove", mv)
    .on("mouseout", function() {
      d3.select(this).attr("r", none || selectedTeams.has(this.__data__.team) ? 5.5 : 3.5)
        .attr("stroke", "#faf9f5").attr("stroke-width", 0.8);
      ht();
    });

  g.append("g").attr("transform", `translate(0,${iH})`)
    .call(d3.axisBottom(x).ticks(7).tickFormat(d => `$${d}`))
    .call(a => a.select(".domain").remove())
    .call(a => a.selectAll(".tick line").remove())
    .call(a => a.selectAll(".tick text").attr("fill", C.lit).attr("font-size", 11));
  g.append("g")
    .call(d3.axisLeft(y).ticks(6).tickFormat(d => `$${d}`))
    .call(a => a.select(".domain").remove())
    .call(a => a.selectAll(".tick line").remove())
    .call(a => a.selectAll(".tick text").attr("fill", C.lit).attr("font-size", 11));

  g.append("text").attr("x", iW / 2).attr("y", iH + 42)
    .attr("text-anchor", "middle").attr("fill", C.mid).attr("font-size", 12)
    .text(scatterMode === "single"
      ? "ATC Model Value — Single Pool ($)"
      : "ATC Model Value — Split Pool 61/39 ($)");
  g.append("text").attr("transform", "rotate(-90)").attr("x", -iH / 2).attr("y", -46)
    .attr("text-anchor", "middle").attr("fill", C.mid).attr("font-size", 12).text("Price Paid ($)");

  display(svg.node());
}
```

<hr class="chart-divider">

## Position Market Inflation

<p class="section-meta">Price paid ÷ model value by position · 1.0× = fair value · Toggle changes the model baseline</p>

<div class="narrative">
This is where the choice of valuation model has the most dramatic effect on conclusions — and where
the most strategically important insight lives.
<br><br>
Under <strong>single pool</strong>, starting pitchers appear to be the league's biggest bargain at
<strong>0.76×</strong>: the market paid only 76 cents for every dollar of projected SP value. But this
reading is largely an artifact of the model. Single pool assigns the same $/PAR rate to everyone,
implicitly treating the auction as if half the budget should go to pitching — when in reality, this
league has historically allocated only 39–47% to pitching. The model inflates SP values to the point
where the market looks cheap by comparison.
<br><br>
Switch to <strong>split pool</strong> and that story evaporates. SPs go from 0.76× to <strong>0.99×</strong>
— essentially fair value. The market priced starting pitchers correctly all along; it was the
single-pool model that was mispriced, not the auction. This is a meaningful corrective: teams who
felt they were "stealing" starters this year were largely paying what the market said those starters were worth.
<span class="callout">
  <strong>The real market inefficiency is relief pitching.</strong> Under split pool, RPs jump to
  <strong>2.09×</strong> — the most overpriced position in the league by a wide margin. The market
  consistently pays a steep premium for save upside that neither valuation model captures well. A
  closer projected for 30 saves goes for far more than his underlying run-prevention stats would justify.
  This finding is robust: RP is expensive in both models (1.61× single, 2.09× split), but the true
  magnitude of the premium only becomes visible under split pool.
</span>
<strong>Catchers (1.32× split)</strong> and <strong>outfielders (1.35× split)</strong> remain above
fair value in both models, though the premiums look more moderate under split pool. Catcher scarcity
in an AL-only format is a structural feature that won't change; OF demand reflects the position's
outsized counting-stat contribution. The second baseman market (1.08× split) was the most efficiently
priced position in the league — nearly no premium above model in either framework.
<br><br>
<em>The broader implication:</em> single-pool valuation systematically understates the cost of pitching
and overstates the cost of hitting relative to how the market actually behaves. Teams setting targets
using single-pool models are likely setting pitcher ceilings too high and hitter ceilings too low.
Split-pool targets, calibrated to historical spending, will produce more accurate bid guidance.
</div>

```js
const positionMode = view(makeToggle());
```

```js
{
  const mc = document.createElement("div");
  mc.className = "mode-callout";

  const single = document.createElement("div");
  single.className = "mode-callout-box mc-single";
  single.style.opacity = positionMode === "single" ? "1" : "0.38";
  const st = document.createElement("div");
  st.className = "mct";
  st.textContent = "Single Pool — Key Ratios";
  single.appendChild(st);
  single.appendChild(document.createTextNode("SP: 0.76× (apparent bargain) · RP: 1.61× · OF: 1.69× · C: 1.65× · 2B: 1.35×"));

  const split = document.createElement("div");
  split.className = "mode-callout-box mc-split";
  split.style.opacity = positionMode === "split" ? "1" : "0.38";
  const splt = document.createElement("div");
  splt.className = "mct";
  splt.textContent = "Split Pool 61/39 — Key Ratios";
  split.appendChild(splt);
  split.appendChild(document.createTextNode("SP: 0.99× (fair value) · RP: 2.09× (most expensive) · OF: 1.35× · C: 1.32× · 2B: 1.08×"));

  mc.append(single, split);
  display(mc);
}
```

```js
{
  const posOrder  = ["C", "OF", "RP", "3B", "1B", "SS", "2B", "SP"];
  const posLabels = {C:"Catcher",OF:"Outfield",RP:"Relief Pitcher","3B":"Third Base","1B":"First Base",SS:"Shortstop","2B":"Second Base",SP:"Starting Pitcher"};
  const norm = positionMode === "single" ? DATA.positionNorm : DATA.positionNormSplit;

  const pd = posOrder.map(p => ({
    pos: p, label: posLabels[p],
    ratio: norm[p]?.ratio ?? 1,
    count: norm[p]?.count ?? 0,
  })).sort((a, b) => b.ratio - a.ratio);

  const W = Math.min(width, 900);
  const m = {t: 14, r: 80, b: 24, l: 135};
  const iW = W - m.l - m.r, iH = 300 - m.t - m.b;

  const x = d3.scaleLinear().domain([0.5, 2.3]).range([0, iW]);
  const y = d3.scaleBand().domain(pd.map(d => d.label)).range([0, iH]).padding(0.35);

  const svg = d3.create("svg").attr("width", W).attr("height", iH + m.t + m.b).style("background", C.bg);
  const g   = svg.append("g").attr("transform", `translate(${m.l},${m.t})`);

  g.selectAll(".gx").data(x.ticks(6)).join("line")
    .attr("x1", d => x(d)).attr("x2", d => x(d)).attr("y1", 0).attr("y2", iH)
    .attr("stroke", C.grd).attr("stroke-width", 0.5);

  g.append("line").attr("x1", x(1)).attr("x2", x(1)).attr("y1", -10).attr("y2", iH)
    .attr("stroke", C.mid).attr("stroke-width", 1).attr("stroke-dasharray", "3 3").attr("opacity", 0.45);
  g.append("text").attr("x", x(1)).attr("y", -14).attr("text-anchor", "middle")
    .attr("fill", C.mid).attr("font-size", 10).text("1.0×");

  g.selectAll(".pseg").data(pd).join("line").attr("class", "pseg")
    .attr("x1", x(1)).attr("x2", d => x(d.ratio))
    .attr("y1", d => y(d.label) + y.bandwidth() / 2).attr("y2", d => y(d.label) + y.bandwidth() / 2)
    .attr("stroke", d => d.ratio >= 1 ? C.sec : C.acc).attr("stroke-width", 2.2).attr("opacity", 0.75);

  g.selectAll(".pdot").data(pd).join("circle").attr("class", "pdot")
    .attr("cx", d => x(d.ratio)).attr("cy", d => y(d.label) + y.bandwidth() / 2).attr("r", 8)
    .attr("fill", d => d.ratio >= 1 ? C.sec : C.acc).style("cursor", "pointer")
    .on("mouseover", (e, d) => tip([
      {cls: "tp", text: d.label},
      {cls: "tr", label: "Market ratio", value: `${d.ratio.toFixed(2)}×`},
      {cls: "tr", label: "Players",      value: String(d.count)},
    ], e))
    .on("mousemove", mv).on("mouseout", ht);

  g.selectAll(".plbl").data(pd).join("text").attr("class", "plbl")
    .attr("x", d => x(d.ratio) + (d.ratio >= 1 ? 13 : -13))
    .attr("y", d => y(d.label) + y.bandwidth() / 2 + 4)
    .attr("text-anchor", d => d.ratio >= 1 ? "start" : "end")
    .attr("fill", C.mid).attr("font-size", 11).attr("font-weight", 600)
    .text(d => `${d.ratio.toFixed(2)}×`);

  g.append("g").call(d3.axisLeft(y).tickSize(0))
    .call(a => a.select(".domain").remove())
    .call(a => a.selectAll(".tick text").attr("fill", C.mid).attr("font-size", 12));
  g.append("g").attr("transform", `translate(0,${iH})`)
    .call(d3.axisBottom(x).ticks(6).tickFormat(d => `${d}×`))
    .call(a => a.select(".domain").remove())
    .call(a => a.selectAll(".tick line").remove())
    .call(a => a.selectAll(".tick text").attr("fill", C.lit).attr("font-size", 10));

  display(svg.node());
}
```

<hr class="chart-divider">

## Full Budget Picture — Keepers + Auction

<p class="section-meta">Each team's $260 cap: keeper salary + auction spend + remaining · Hover for detail · Unaffected by valuation model</p>

<div class="narrative">
This chart captures actual dollars committed — it doesn't change with the valuation model because
it reflects what teams actually spent, not what a model says things were worth. It's the clearest
view of each team's strategic constraints heading into the season.
<br><br>
<strong>Mean Machine</strong> committed $170 to keepers before the auction began — more than two-thirds
of their entire budget — limiting their open-market activity to just $85 across 9 players. This wasn't
a failure of execution; it reflects a deliberate multi-year strategy of building through keeper
contracts. <strong>Thunder &amp; Lightning</strong> ($150) and <strong>R&amp;R</strong> ($157) were
similarly constrained, playing a roster-maintenance game rather than a roster-building one.
<br><br>
<strong>Gusteroids</strong> had the most auction flexibility with just $66 committed to keepers,
leaving $194 available — nearly three times Mean Machine's auction budget. That flexibility is
visible throughout this analysis: 12 players acquired, $181 spent, the heaviest auction activity
of any team. <strong>Kerry &amp; Mitch</strong> also ran an aggressive auction ($170 spent, $71 in
keepers), ending with just $19 remaining — the tightest final cap in the league and a sign they
were comfortable with their roster at close.
<br><br>
The keeper vs. auction tradeoff has an important interaction with the valuation model question.
Keeper contracts are priced at their original draft value (often years ago), not at current market
rates. Teams with heavy keeper books are locking in historical prices — which may be excellent or
poor deals depending on how those players have developed. That context isn't captured in this chart
but is worth keeping in mind when comparing teams with very different keeper-to-auction ratios.
</div>

```js
{
  const teams = Object.entries(DATA.teamSummary)
    .map(([n, s]) => ({name: n, keeper: s.keeper_total, auction: s.auction_total,
                        remaining: s.remaining, kcount: s.keeper_count, acount: s.count}))
    .sort((a, b) => (b.keeper + b.auction) - (a.keeper + a.auction));

  const W = Math.min(width, 900);
  const m = {t: 10, r: 80, b: 22, l: 158};
  const iW = W - m.l - m.r, iH = 330 - m.t - m.b;

  const x = d3.scaleLinear().domain([0, 260]).range([0, iW]);
  const y = d3.scaleBand().domain(teams.map(d => d.name)).range([0, iH]).padding(0.27);

  const svg = d3.create("svg").attr("width", W).attr("height", iH + m.t + m.b).style("background", C.bg);
  const g   = svg.append("g").attr("transform", `translate(${m.l},${m.t})`);

  [65, 130, 195, 260].forEach(v => {
    g.append("line").attr("x1", x(v)).attr("x2", x(v)).attr("y1", 0).attr("y2", iH)
      .attr("stroke", C.grd).attr("stroke-width", 0.5);
  });

  g.selectAll(".bk").data(teams).join("rect").attr("class", "bk")
    .attr("x", 0).attr("y", d => y(d.name)).attr("width", d => x(d.keeper)).attr("height", y.bandwidth())
    .attr("fill", C.pri).attr("opacity", 0.75).attr("rx", 2);
  g.selectAll(".ba").data(teams).join("rect").attr("class", "ba")
    .attr("x", d => x(d.keeper)).attr("y", d => y(d.name)).attr("width", d => x(d.auction)).attr("height", y.bandwidth())
    .attr("fill", C.sec).attr("opacity", 0.75);
  g.selectAll(".br").data(teams).join("rect").attr("class", "br")
    .attr("x", d => x(d.keeper + d.auction)).attr("y", d => y(d.name))
    .attr("width", d => x(Math.max(0, d.remaining))).attr("height", y.bandwidth())
    .attr("fill", C.lit).attr("opacity", 0.18).attr("rx", 2);

  g.selectAll(".bo").data(teams).join("rect").attr("class", "bo")
    .attr("x", 0).attr("y", d => y(d.name)).attr("width", iW).attr("height", y.bandwidth())
    .attr("fill", "transparent").style("cursor", "pointer")
    .on("mouseover", (e, d) => tip([
      {cls: "tp", text: d.name},
      {cls: "tr", label: "Keepers",   value: `$${d.keeper} (${d.kcount})`},
      {cls: "tr", label: "Auction",   value: `$${d.auction} (${d.acount})`},
      {cls: "tr", label: "Remaining", value: `$${d.remaining}`},
    ], e))
    .on("mousemove", mv).on("mouseout", ht);

  g.selectAll(".btlbl").data(teams).join("text").attr("class", "btlbl")
    .attr("x", d => x(d.keeper + d.auction) + 6).attr("y", d => y(d.name) + y.bandwidth() / 2 + 4)
    .attr("fill", C.mid).attr("font-size", 11).attr("font-weight", 600)
    .text(d => `$${d.keeper + d.auction}`);

  g.append("g").call(d3.axisLeft(y).tickSize(0))
    .call(a => a.select(".domain").remove())
    .call(a => a.selectAll(".tick text").attr("fill", C.mid).attr("font-size", 12));
  g.append("g").attr("transform", `translate(0,${iH})`)
    .call(d3.axisBottom(x).tickValues([0, 65, 130, 195, 260]).tickFormat(d => `$${d}`))
    .call(a => a.select(".domain").remove())
    .call(a => a.selectAll(".tick line").remove())
    .call(a => a.selectAll(".tick text").attr("fill", C.lit).attr("font-size", 10));

  display(svg.node());
}
```

<div class="budget-legend">
  <span><span class="swatch" style="background:#3A6EA5;opacity:.75"></span> Keeper salary</span>
  <span><span class="swatch" style="background:#C1666B;opacity:.75"></span> Auction spend</span>
  <span><span class="swatch" style="background:#999;opacity:.3"></span> Remaining cap</span>
</div>

<hr class="chart-divider">

## Team Value Report Card

<p class="section-meta">Total model surplus across all auction acquisitions · Keepers excluded · Toggle changes the model baseline</p>

<div class="narrative">
No team finished positive in either model — keeper inflation ensures the market collectively overpays.
But the two frameworks produce meaningfully different team rankings, and the gap between them reveals
which teams ran pitching-heavy strategies and which ran balanced or hitting-heavy ones.
<br><br>
Under <strong>single pool</strong>, <strong>Gusteroids</strong> executed the most efficient auction
in the league at -$10.3. That ranking is driven largely by their pitching acquisitions: Gilbert, Kirby,
Pepiot, and Suárez all showed surplus against single-pool SP values. Switch to <strong>split pool</strong>
and Gusteroids drops to <strong>#6 at -$23.4</strong>, because pitcher model values fall ~23% and
the "surplus" on those pitchers shrinks or reverses. Under split pool, Gilbert (paid $30) flips from
+$1.8 to -$5.6; Kirby (paid $25) from +$2.8 to -$3.7. The pitching staff wasn't a bargain — it was
market price. Gusteroids paid correctly for good pitching, but didn't steal it.
<br><br>
The teams that rise under split pool are the ones that leaned into hitting.
<strong>R&amp;R</strong> climbs from #3 to <strong>#1 at -$7.5</strong> — their patient, value-oriented
approach and relatively hitting-balanced roster looks much better when hitter values are recalibrated
upward. <strong>Kerry &amp; Mitch</strong> similarly rises from #6 to #2 (-$16.0): their heavy
hitter acquisitions (Ramírez, Henderson, Altuve, Garcia, Ward) carry higher split-pool values
even though some of those players were nominally overpaid at auction.
<span class="callout">
  <strong>What this means in practice:</strong> if your pre-draft valuation model uses single pool,
  you'll systematically see pitching as undervalued and be drawn toward pitcher-heavy strategies.
  Split pool corrects for this, showing pitching as roughly fairly priced. Teams that
  used single-pool intuition to justify SP spending weren't wrong to buy those pitchers — they're
  good players — but they weren't getting the edge the model implied.
</span>
<strong>HAMMERHEADS</strong> rank last in both models (-$66.3 single, -$46.8 split) though the gap
narrows under split pool because their 18-player approach included a mix of hitters and pitchers.
Their deficit reflects volume — buying more players creates more opportunities for the market to
outbid the model — as well as some meaningful overpays on early nominations.
</div>

```js
const surplusMode = view(makeToggle());
```

```js
{
  const mc = document.createElement("div");
  mc.className = "mode-callout";

  const single = document.createElement("div");
  single.className = "mode-callout-box mc-single";
  single.style.opacity = surplusMode === "single" ? "1" : "0.38";
  const st = document.createElement("div"); st.className = "mct"; st.textContent = "Single Pool — Rankings";
  single.appendChild(st);
  single.appendChild(document.createTextNode("#1 Gusteroids -$10.3 · #2 Mean Machine -$12.6 · #3 R&R -$19.6"));
  single.appendChild(document.createElement("br"));
  single.appendChild(document.createTextNode("#9 On a Bender -$44.4 · #10 HAMMERHEADS -$66.3"));

  const splt = document.createElement("div");
  splt.className = "mode-callout-box mc-split";
  splt.style.opacity = surplusMode === "split" ? "1" : "0.38";
  const spt = document.createElement("div"); spt.className = "mct"; spt.textContent = "Split Pool — Rankings";
  splt.appendChild(spt);
  splt.appendChild(document.createTextNode("#1 R&R -$7.5 · #2 Kerry & Mitch -$16.0 · #3 Shrooms -$19.9"));
  splt.appendChild(document.createElement("br"));
  splt.appendChild(document.createTextNode("#9 Thunder & Lightning -$37.0 · #10 HAMMERHEADS -$46.8"));

  mc.append(single, splt);
  display(mc);
}
```

```js
{
  const allSurp = Object.values(DATA.teamSummary).flatMap(s => [s.surplus_total, s.split_surplus_total]);
  const xDom = [Math.min(...allSurp) - 8, Math.max(...allSurp) + 8];
  const mode = surplusMode;

  const pd = Object.entries(DATA.teamSummary)
    .map(([n, s]) => ({name: n,
      surplus: mode === "single" ? s.surplus_total : s.split_surplus_total,
      count: s.count, spent: s.auction_total}))
    .sort((a, b) => b.surplus - a.surplus);

  const W = Math.min(width, 900);
  const m = {t: 10, r: 90, b: 22, l: 158};
  const iW = W - m.l - m.r, iH = 360 - m.t - m.b;

  const x = d3.scaleLinear().domain(xDom).range([0, iW]);
  const y = d3.scaleBand().domain(pd.map(d => d.name)).range([0, iH]).padding(0.4);

  const svg = d3.create("svg").attr("width", W).attr("height", iH + m.t + m.b).style("background", C.bg);
  const g   = svg.append("g").attr("transform", `translate(${m.l},${m.t})`);

  x.ticks(6).forEach(v => {
    g.append("line").attr("x1", x(v)).attr("x2", x(v)).attr("y1", 0).attr("y2", iH)
      .attr("stroke", C.grd).attr("stroke-width", 0.5);
  });
  g.append("line").attr("x1", x(0)).attr("x2", x(0)).attr("y1", -8).attr("y2", iH)
    .attr("stroke", C.mid).attr("stroke-width", 1).attr("opacity", 0.35);

  g.selectAll(".sseg").data(pd).join("line").attr("class", "sseg")
    .attr("x1", x(0)).attr("x2", d => x(d.surplus))
    .attr("y1", d => y(d.name) + y.bandwidth() / 2).attr("y2", d => y(d.name) + y.bandwidth() / 2)
    .attr("stroke", d => d.surplus >= 0 ? C.acc : C.sec).attr("stroke-width", 2.2).attr("opacity", 0.8);

  g.selectAll(".sdot2").data(pd).join("circle").attr("class", "sdot2")
    .attr("cx", d => x(d.surplus)).attr("cy", d => y(d.name) + y.bandwidth() / 2).attr("r", 9)
    .attr("fill", d => d.surplus >= 0 ? C.acc : C.sec).style("cursor", "pointer")
    .on("mouseover", (e, d) => tip([
      {cls: "tp", text: d.name},
      {cls: "tr", label: `Surplus (${mode})`, value: fs(d.surplus), valCls: sc(d.surplus)},
      {cls: "tr", label: "Players",           value: String(d.count)},
      {cls: "tr", label: "Auction spend",     value: `$${d.spent}`},
    ], e))
    .on("mousemove", mv).on("mouseout", ht);

  g.selectAll(".slbl").data(pd).join("text").attr("class", "slbl")
    .attr("x", d => x(d.surplus) + (d.surplus >= 0 ? 14 : -14))
    .attr("y", d => y(d.name) + y.bandwidth() / 2 + 4)
    .attr("text-anchor", d => d.surplus >= 0 ? "start" : "end")
    .attr("fill", C.mid).attr("font-size", 11).attr("font-weight", 600).text(d => fs(d.surplus));

  g.append("g").call(d3.axisLeft(y).tickSize(0))
    .call(a => a.select(".domain").remove())
    .call(a => a.selectAll(".tick text").attr("fill", C.mid).attr("font-size", 12));
  g.append("g").attr("transform", `translate(0,${iH})`)
    .call(d3.axisBottom(x).ticks(6).tickFormat(d => `$${d}`))
    .call(a => a.select(".domain").remove())
    .call(a => a.selectAll(".tick line").remove())
    .call(a => a.selectAll(".tick text").attr("fill", C.lit).attr("font-size", 10));

  display(svg.node());
}
```

<hr class="chart-divider">

## Team Spending Profiles

<p class="section-meta">Each row = one team · Dot size proportional to price · Blue = hitter, rose = pitcher · Unaffected by valuation model</p>

<div class="narrative">
This chart shows the actual shape of each team's auction strategy — and in combination with the
surplus analysis, it explains why model choice matters so much for evaluating those strategies.
<br><br>
The rose-heavy right tail on <strong>Gusteroids'</strong> row is immediately visible: their three
largest purchases (Gilbert $30, Kirby $25, Seager $23) are two pitchers and a hitter, and the rest
of the roster was assembled from mid-range investments. Under single pool, this pitching-forward
approach looked like a strategic win. Under split pool, it looks like fair execution — paying market
rates for good-but-not-stolen pitchers while building a solid mid-tier hitter core.
<br><br>
The contrast with <strong>HAMMERHEADS</strong> is instructive. HAMMERHEADS spread $190 across 18
players with no single acquisition above $17 — the flattest distribution in the league at 35%
concentration. Under single pool they look expensive (worst surplus); under split pool the gap
narrows somewhat, suggesting their balanced approach captured slightly more hitter value than
the single-pool ranking implies.
<br><br>
<strong>Kosher Hogs</strong> (77% concentration) and <strong>Mean Machine</strong> (71%) took the
stars-and-scrubs approach, concentrating budget in a few premium slots. The degree to which this
works depends on whether those top players hit their projections — the model surplus analysis only
tells you whether you overpaid relative to expectation, not whether the expectation will be met.
</div>

```js
{
  const TEAMS = Object.keys(TC);
  const W = Math.min(width, 900);
  const m = {t: 10, r: 32, b: 42, l: 158};
  const iW = W - m.l - m.r, iH = 460 - m.t - m.b;

  const maxP = d3.max(DATA.players, d => d.price);
  const x = d3.scaleLinear().domain([0, maxP + 4]).range([0, iW]);
  const y = d3.scaleBand().domain(TEAMS).range([0, iH]).padding(0.15);

  const svg = d3.create("svg").attr("width", W).attr("height", iH + m.t + m.b).style("background", C.bg);
  const g   = svg.append("g").attr("transform", `translate(${m.l},${m.t})`);

  x.ticks(7).forEach(v => {
    g.append("line").attr("x1", x(v)).attr("x2", x(v)).attr("y1", 0).attr("y2", iH)
      .attr("stroke", C.grd).attr("stroke-width", 0.5);
  });

  const avgByTeam = d3.rollup(DATA.players, v => d3.mean(v, d => d.price), d => d.team);
  TEAMS.forEach(t => {
    const avg = avgByTeam.get(t);
    if (avg == null) return;
    g.append("line")
      .attr("x1", x(avg)).attr("x2", x(avg)).attr("y1", y(t)).attr("y2", y(t) + y.bandwidth())
      .attr("stroke", TC[t]).attr("stroke-width", 1.5).attr("opacity", 0.3).attr("stroke-dasharray", "3 2");
  });

  DATA.players.forEach(d => {
    const yMid = y(d.team) + y.bandwidth() / 2;
    const r    = Math.sqrt(d.price) * 1.9;
    g.append("circle")
      .attr("cx", x(d.price)).attr("cy", yMid + stableJitter(d.player) * y.bandwidth() * 0.52).attr("r", r)
      .attr("fill", d.pos_type === "hitter" ? C.pri : C.sec).attr("opacity", 0.6)
      .attr("stroke", "#faf9f5").attr("stroke-width", 0.6).style("cursor", "pointer")
      .on("mouseover", function(e) {
        d3.select(this).attr("opacity", 1).attr("stroke", C.txt).attr("stroke-width", 1.5);
        const sv = gs(d, "single");
        tip([
          {cls: "tp", text: d.player},
          {cls: "tm", text: d.team, color: TC[d.team]},
          {cls: "tr", label: "Price paid",  value: `$${d.price}`},
          {cls: "tr", label: "Model value", value: String(gv(d, "single") ?? "—")},
          {cls: "tr", label: "Surplus",     value: fs(sv), valCls: sc(sv)},
          {cls: "tr", label: "Position",    value: d.position},
        ], e);
      })
      .on("mousemove", mv)
      .on("mouseout", function() {
        d3.select(this).attr("opacity", 0.6).attr("stroke", "#faf9f5").attr("stroke-width", 0.6);
        ht();
      });
  });

  g.append("g").call(d3.axisLeft(y).tickSize(0))
    .call(a => a.select(".domain").remove())
    .call(a => a.selectAll(".tick text").attr("fill", C.mid).attr("font-size", 12));
  g.append("g").attr("transform", `translate(0,${iH})`)
    .call(d3.axisBottom(x).ticks(7).tickFormat(d => `$${d}`))
    .call(a => a.select(".domain").remove())
    .call(a => a.selectAll(".tick line").remove())
    .call(a => a.selectAll(".tick text").attr("fill", C.lit).attr("font-size", 10));
  g.append("text").attr("x", iW / 2).attr("y", iH + 35)
    .attr("text-anchor", "middle").attr("fill", C.mid).attr("font-size", 11)
    .text("Price paid · dot area proportional to price · dashed = team average");

  display(svg.node());
}
```

<hr class="chart-divider">

## Auction Flow — How Prices Evolved

<p class="section-meta">Price by nomination order · Grey line = 10-nomination rolling average · Unaffected by valuation model</p>

<div class="narrative">
Auction prices compressed sharply over the course of the night's 119 nominations. The first 30
averaged <strong>$24.20</strong>; nominations 31–70 dropped to <strong>$10.20</strong>; the final
49 averaged just <strong>$5.20</strong>, with ten players going for $1. This compression is structural
— as the high-end players are taken and budgets are spent, competition narrows and prices fall.
<br><br>
The opening run set the tone: Ramírez ($48), Henderson ($40), Muñoz ($34), Langford ($35), and
Raleigh ($30) all went in the first 11 nominations. These early prices represent the market's
assessment of scarcity — each of these players had legitimate competition from multiple bidders
with full budgets, which drove prices well above model in all cases. As a general rule, the early
auction is where the largest nominal overpays happen; the late auction is where the
largest nominal bargains (on a percentage basis) are found.
<br><br>
The interplay with model choice is subtle here: the late-auction SP bargains that look most
dramatic under single pool (Bibee at nom 61, Cameron at nom 100, Eflin at nom 91) look much
more like fair-market deals under split pool. Patience in the SP market wasn't a skill edge
so much as recognizing that a correctly-priced pitcher was available late once budget constraints
took the early bidders out of the market.
</div>

```js
{
  const sorted = DATA.players.slice().sort((a, b) => a.nom - b.nom);
  const roll   = sorted.map((d, i) => {
    const sl = sorted.slice(Math.max(0, i - 10 + 1), i + 1);
    return {nom: d.nom, avg: d3.mean(sl, w => w.price)};
  });

  const W = Math.min(width, 900);
  const m = {t: 22, r: 30, b: 50, l: 58};
  const iW = W - m.l - m.r, iH = 370 - m.t - m.b;
  const maxP = d3.max(DATA.players, d => d.price);

  const x = d3.scaleLinear().domain([1, 119]).range([0, iW]);
  const y = d3.scaleLinear().domain([0, maxP + 5]).range([iH, 0]);

  const svg = d3.create("svg").attr("width", W).attr("height", iH + m.t + m.b).style("background", C.bg);
  const g   = svg.append("g").attr("transform", `translate(${m.l},${m.t})`);

  y.ticks(6).forEach(v => {
    g.append("line").attr("x1", 0).attr("x2", iW).attr("y1", y(v)).attr("y2", y(v))
      .attr("stroke", C.grd).attr("stroke-width", 0.5);
  });

  g.append("path").datum(roll)
    .attr("d", d3.line().x(d => x(d.nom)).y(d => y(d.avg)).curve(d3.curveCatmullRom))
    .attr("fill", "none").attr("stroke", C.mid).attr("stroke-width", 1.8).attr("opacity", 0.35);

  g.selectAll(".tdot").data(DATA.players).join("circle").attr("class", "tdot")
    .attr("cx", d => x(d.nom)).attr("cy", d => y(d.price)).attr("r", 5)
    .attr("fill", d => TC[d.team]).attr("opacity", 0.78)
    .attr("stroke", "#faf9f5").attr("stroke-width", 0.7).style("cursor", "pointer")
    .on("mouseover", function(e, d) {
      d3.select(this).attr("r", 7.5).attr("opacity", 1).attr("stroke", C.txt).attr("stroke-width", 1.5);
      tip([
        {cls: "tp", text: d.player},
        {cls: "tm", text: d.team, color: TC[d.team]},
        {cls: "tr", label: "Nom #",    value: `#${d.nom}`},
        {cls: "tr", label: "Time",     value: d.timestamp},
        {cls: "tr", label: "Price",    value: `$${d.price}`},
        {cls: "tr", label: "Position", value: d.position},
      ], e);
    })
    .on("mousemove", mv)
    .on("mouseout", function() {
      d3.select(this).attr("r", 5).attr("opacity", 0.78).attr("stroke", "#faf9f5").attr("stroke-width", 0.7);
      ht();
    });

  g.append("g").attr("transform", `translate(0,${iH})`)
    .call(d3.axisBottom(x).ticks(10))
    .call(a => a.select(".domain").remove())
    .call(a => a.selectAll(".tick line").remove())
    .call(a => a.selectAll(".tick text").attr("fill", C.lit).attr("font-size", 11));
  g.append("g")
    .call(d3.axisLeft(y).ticks(6).tickFormat(d => `$${d}`))
    .call(a => a.select(".domain").remove())
    .call(a => a.selectAll(".tick line").remove())
    .call(a => a.selectAll(".tick text").attr("fill", C.lit).attr("font-size", 11));

  g.append("text").attr("x", iW / 2).attr("y", iH + 42)
    .attr("text-anchor", "middle").attr("fill", C.mid).attr("font-size", 12).text("Nomination order");
  g.append("text").attr("transform", "rotate(-90)").attr("x", -iH / 2).attr("y", -46)
    .attr("text-anchor", "middle").attr("fill", C.mid).attr("font-size", 12).text("Price paid ($)");

  display(svg.node());
}
```

<hr class="chart-divider">

## Gusteroids — Target Tracking

<p class="section-meta">Shaded band = pre-draft target range · Dashed line = model value (toggle-aware) · Large dot = price paid</p>

<div class="narrative">
For each Gusteroids acquisition, the <strong>shaded band</strong> shows the pre-draft target-to-max
range, the <strong>dashed line</strong> is the model value (which shifts under split pool for pitchers),
and the large dot is the price paid — teal if at or under model value, rose if above.
<br><br>
Under <strong>single pool</strong>, the pitching staff looks strong: Gilbert, Kirby, Pepiot, and
Suárez all sit at or below the dashed model-value line. Toggle to <strong>split pool</strong> and
the dashed lines shift left for all four starters — Gilbert from $31.8 to $24.4, Kirby from $27.8
to $21.3, Pepiot from $22.5 to $17.2, Suárez from $20.8 to $15.9. Under split pool, only Suárez
(+$1.9) and Pepiot (+$0.2) remain clearly in the teal zone; Gilbert (-$5.6) and Kirby (-$3.7)
flip rose. The pre-draft target bands are unchanged — Gusteroids set appropriate targets — but
the model value baseline moves out from under them.
<br><br>
The hitter side tells a more nuanced story across the two models. <strong>Corey Seager</strong>
improves slightly (-$8.4 single → -$4.8 split) because hitter values rise under split pool, but
he remains the largest single overpay. <strong>Steven Kwan</strong> nearly reaches break-even under
split pool (-$3.7 → -$0.4). <strong>Willson Contreras</strong> flips from small deficit to slight
surplus (-$2.2 → +$0.7). This pattern — hitters looking incrementally better under split pool —
is consistent across the league, not unique to Gusteroids.
<span class="callout">
  <strong>The practical takeaway for future auctions:</strong> the pre-draft target ranges here were
  built on single-pool values, which inflated SP targets slightly and deflated hitter targets slightly.
  Rebuilding targets on split-pool values in 2027 would mean lower ceilings for starting pitchers
  and somewhat higher ceilings for equivalent hitters — pushing the bidding strategy closer to
  where the market actually settles.
</span>
</div>

```js
const gustMode = view(makeToggle());
```

```js
{
  const mode  = gustMode;
  const picks = DATA.players
    .filter(d => d.team === "Gusteroids" && d.pre_tgt != null)
    .sort((a, b) => b.dollar_value - a.dollar_value);

  const rowH = 40;
  const W    = Math.min(width, 900);
  const m    = {t: 10, r: 110, b: 38, l: 140};
  const iW   = W - m.l - m.r, iH = picks.length * rowH + 4;

  const allV = picks.flatMap(d =>
    [d.price, d.pre_tgt, d.pre_max, d.live_tgt, d.live_max, d.dollar_value, d.split_dollar_value]
    .filter(v => v != null)
  );
  const xMax = Math.max(...allV) + 10;
  const x = d3.scaleLinear().domain([0, xMax]).range([0, iW]);
  const y = d3.scaleBand().domain(picks.map(d => d.player)).range([0, iH]).padding(0.3);

  const svg = d3.create("svg").attr("width", W).attr("height", iH + m.t + m.b).style("background", C.bg);
  const g   = svg.append("g").attr("transform", `translate(${m.l},${m.t})`);

  x.ticks(8).forEach(v => {
    g.append("line").attr("x1", x(v)).attr("x2", x(v)).attr("y1", 0).attr("y2", iH)
      .attr("stroke", C.grd).attr("stroke-width", 0.5);
  });

  picks.forEach(d => {
    const yMid = y(d.player) + y.bandwidth() / 2;
    const bh   = y.bandwidth();
    if (d.pre_tgt != null && d.pre_max != null) {
      g.append("rect")
        .attr("x", x(d.pre_tgt)).attr("y", yMid - bh * 0.46)
        .attr("width", x(d.pre_max) - x(d.pre_tgt)).attr("height", bh * 0.92)
        .attr("fill", C.pri).attr("opacity", 0.12).attr("rx", 3);
    }
    if (d.live_tgt != null && d.live_tgt !== d.pre_tgt) {
      g.append("circle").attr("cx", x(d.live_tgt)).attr("cy", yMid).attr("r", 4.5)
        .attr("fill", C.mid).attr("opacity", 0.75);
    }
    if (d.pre_tgt != null) {
      g.append("circle").attr("cx", x(d.pre_tgt)).attr("cy", yMid).attr("r", 5)
        .attr("fill", "#faf9f5").attr("stroke", C.pri).attr("stroke-width", 2);
    }
  });

  g.selectAll(".gml").data(picks).join("line").attr("class", "gml")
    .attr("x1", d => x(gv(d, mode) ?? 0)).attr("x2", d => x(gv(d, mode) ?? 0))
    .attr("y1", d => y(d.player) + y.bandwidth() / 2 - y.bandwidth() * 0.5)
    .attr("y2", d => y(d.player) + y.bandwidth() / 2 + y.bandwidth() * 0.5)
    .attr("stroke", C.lit).attr("stroke-width", 1.5).attr("stroke-dasharray", "3 2");

  g.selectAll(".gpaid").data(picks).join("circle").attr("class", "gpaid")
    .attr("cx", d => x(d.price)).attr("cy", d => y(d.player) + y.bandwidth() / 2).attr("r", 9)
    .attr("fill", d => gv(d, mode) != null && d.price <= gv(d, mode) ? C.acc : C.sec)
    .attr("opacity", 0.9).style("cursor", "pointer")
    .on("mouseover", (e, d) => {
      const sv  = gs(d, mode);
      const rows = [
        {cls: "tp", text: d.player},
        {cls: "tr", label: "Price paid",     value: `$${d.price}`},
        {cls: "tr", label: "Model value",    value: `$${gv(d, mode)}`},
        {cls: "tr", label: "Pre-draft range",value: `$${d.pre_tgt} – $${d.pre_max}`},
      ];
      if (d.live_tgt != null && d.live_tgt !== d.pre_tgt) {
        rows.push({cls: "tr", label: "Live target", value: `$${d.live_tgt} – $${d.live_max}`});
      }
      rows.push(
        {cls: "tr", label: "Surplus",  value: fs(sv), valCls: sc(sv)},
        {cls: "tr", label: "MSP rank", value: String(d.msp_rank ?? "—")},
      );
      tip(rows, e);
    })
    .on("mousemove", mv).on("mouseout", ht);

  g.selectAll(".gplbl").data(picks).join("text").attr("class", "gplbl")
    .attr("x", d => x(d.price) + 14).attr("y", d => y(d.player) + y.bandwidth() / 2 + 4)
    .attr("fill", d => gv(d, mode) != null && d.price <= gv(d, mode) ? C.acc : C.sec)
    .attr("font-size", 11).attr("font-weight", 700).text(d => `$${d.price}`);

  g.append("g").call(d3.axisLeft(y).tickSize(0))
    .call(a => a.select(".domain").remove())
    .call(a => a.selectAll(".tick text").attr("fill", C.mid).attr("font-size", 12));
  g.append("g").attr("transform", `translate(0,${iH})`)
    .call(d3.axisBottom(x).ticks(8).tickFormat(d => `$${d}`))
    .call(a => a.select(".domain").remove())
    .call(a => a.selectAll(".tick line").remove())
    .call(a => a.selectAll(".tick text").attr("fill", C.lit).attr("font-size", 10));

  const legendItems = [
    {type: "c", f: C.acc, l: "Paid ≤ model value"},
    {type: "c", f: C.sec, l: "Paid > model value"},
    {type: "b", f: C.pri, l: "Pre-draft target range"},
    {type: "d", f: C.lit, l: "ATC model value (toggle-aware)"},
  ];
  legendItems.forEach((item, i) => {
    const lx = iW - 195, ly = 4 + i * 18;
    if (item.type === "d") {
      g.append("line").attr("x1", lx).attr("x2", lx + 16).attr("y1", ly + 5).attr("y2", ly + 5)
        .attr("stroke", item.f).attr("stroke-width", 1.5).attr("stroke-dasharray", "3 2");
    } else if (item.type === "b") {
      g.append("rect").attr("x", lx).attr("y", ly).attr("width", 16).attr("height", 10)
        .attr("fill", item.f).attr("opacity", 0.25).attr("rx", 2);
    } else {
      g.append("circle").attr("cx", lx + 8).attr("cy", ly + 5).attr("r", 6).attr("fill", item.f);
    }
    g.append("text").attr("x", lx + 22).attr("y", ly + 9)
      .attr("fill", C.mid).attr("font-size", 10.5).text(item.l);
  });

  display(svg.node());
}
```

<hr class="chart-divider">

## Synthesis — What the Model Difference Tells Us

Taken together, the two valuation frameworks converge on a few durable conclusions and diverge on one major one. Here's what to carry forward.

<dl class="synthesis-grid">
<div class="synthesis-item">
<dt>Overpaying for elite hitters is universal and model-independent</dt>
<dd>The top-of-market premium on players like Ramírez, Henderson, and Langford is
consistent across both models. The scarcity premium on proven fantasy stars isn't a
modeling artifact — it's a real market dynamic. Budgeting extra for the one or two
players you must have is rational; expecting to win those auctions near model is not.</dd>
</div>
<div class="synthesis-item">
<dt>SP "bargains" are largely a single-pool illusion</dt>
<dd>Under single pool, nearly every SP in the auction looks like good value. Under split
pool, SPs price at 0.99× — essentially perfectly efficient. The market as a whole priced
starting pitching correctly; it was the single-pool model that was off. Future SP target
bids built on single-pool valuations will be set too high relative to where the market settles.</dd>
</div>
<div class="synthesis-item">
<dt>Relief pitching is the one genuine market inefficiency</dt>
<dd>RP is expensive in both models (1.61× single, 2.09× split) and the premium is larger
under the more accurate split-pool framework. Save upside is systematically overpriced.
A disciplined closer strategy — setting hard max bids regardless of how "available" a
closer seems — is supported by the data across multiple years and both valuation methods.</dd>
</div>
<div class="synthesis-item">
<dt>The league's hitter/pitcher split is shifting</dt>
<dd>Historical spending fell from 66% on hitters in 2019 to 53% in 2025 before bouncing
to 61% in 2026. The split-pool calibration used here (61/39) should be treated as a
snapshot, not a constant. If the trend toward pitching spend resumes, the "correct"
split-pool baseline will shift, and pitcher values will need to be recalibrated downward further.</dd>
</div>
<div class="synthesis-item">
<dt>Team surplus rankings are sensitive to model choice</dt>
<dd>Gusteroids: #1 single → #6 split. R&amp;R: #3 single → #1 split. Kerry &amp; Mitch:
#6 single → #2 split. A pitching-heavy auction strategy looks excellent under single pool
and merely average under split pool. The honest read is that Gusteroids executed well
within a defensible plan — but shouldn't assume surplus that may reflect model choice
more than genuine market edge.</dd>
</div>
<div class="synthesis-item">
<dt>Split pool should be the default for target-setting</dt>
<dd>Because split pool is calibrated to how the market actually distributes dollars, it
will produce more accurate bid guidance. Single pool remains useful as a cross-check and
for understanding relative player values within each position group. For 2027 auction
prep, build primary targets on split-pool values and use single-pool as a sanity check
on relative rankings — not absolute bid ceilings.</dd>
</div>
</dl>

<hr class="chart-divider">

## Glossary

Key terms and calculations used throughout this report.

<dl class="glossary-grid">
<div class="glossary-item">
<dt>Single Pool Valuation</dt>
<dd>All players share one dollars-per-PAR rate ($4.06 this year). Simple but tends to over-value pitchers relative to how the market actually spends, because it implicitly assumes ~50% of auction dollars go to pitching when the historical league average is closer to 39–47%.</dd>
</div>
<div class="glossary-item">
<dt>Split Pool Valuation</dt>
<dd>The total budget is divided into separate hitter (61%) and pitcher (39%) pools based on Moonlight Graham's historical spending. Hitters: $5.06/PAR; pitchers: $3.11/PAR. Aligns model values with revealed market preferences and is the recommended baseline for target-setting.</dd>
</div>
<div class="glossary-item">
<dt>Model Value / Dollar Value</dt>
<dd>The estimated auction worth of a player derived from ATC projected stats → SGP → dollars. A $25 model value means the player is projected to contribute ~$25 of standings gains over a full season. The specific dollar figure changes depending on which pool method is used.</dd>
</div>
<div class="glossary-item">
<dt>ATC Projections</dt>
<dd>Aggregated The Computer — a composite projection system blending multiple public forecast models. Pulled from FanGraphs and used as the statistical backbone for all values here.</dd>
</div>
<div class="glossary-item">
<dt>SGP (Standings Gain Points)</dt>
<dd>A framework that converts projected stats into expected standings-point gains across all ten categories. Denominators are calibrated to Moonlight Graham's historical standings, making values league-specific rather than generic.</dd>
</div>
<div class="glossary-item">
<dt>Surplus</dt>
<dd>Model value minus price paid. Positive = bargain; negative = premium above model. Changes depending on which valuation model is selected. Does not account for team-specific roster context (see MSP).</dd>
</div>
<div class="glossary-item">
<dt>MSP (Marginal Standings Points)</dt>
<dd>A team-specific extension of SGP that computes the marginal value of adding a player to your specific roster — accounting for what you already have via keepers. Higher MSP means the player fills a bigger need for your team specifically.</dd>
</div>
<div class="glossary-item">
<dt>Keeper Inflation</dt>
<dd>Because teams keep players at their contracted salaries (often below market), the open auction pool is both smaller and more competitive. All ten teams arrive with their full $260 budgets but compete over fewer available players, structurally pushing prices above model for auction picks.</dd>
</div>
</dl>
