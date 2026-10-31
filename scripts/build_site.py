"""Build the static results page (site/index.html) from the warehouse.

Every number comes from scripts/results.py. Charts are inline SVG drawn here: no third-party scripts,
fonts, images or logos (scripts/site_check.py refuses them).

  uv run python -m scripts.build_site
"""
from __future__ import annotations

import html
from datetime import date

from scripts import results as R
from scripts.common import ROOT

OUT = ROOT / "site" / "index.html"
esc = html.escape

CSS = """
:root {
  color-scheme: light;
  --page: #f9f9f7; --surface: #fcfcfb; --ink: #0b0b0b; --ink-2: #52514e; --muted: #898781;
  --grid: #e1e0d9; --axis: #c3c2b7; --border: rgba(11,11,11,0.10);
  --series-1: #2a78d6; --series-2: #eb6834; --critical: #d03b3b; --banner: #fff6e5;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --page: #0d0d0d; --surface: #1a1a19; --ink: #f0efec; --ink-2: #c3c2b7; --muted: #898781;
    --grid: #2c2c2a; --axis: #383835; --border: rgba(255,255,255,0.10);
    --series-1: #3987e5; --series-2: #d95926; --critical: #d03b3b; --banner: #2a2414;
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --page: #0d0d0d; --surface: #1a1a19; --ink: #f0efec; --ink-2: #c3c2b7; --muted: #898781;
  --grid: #2c2c2a; --axis: #383835; --border: rgba(255,255,255,0.10);
  --series-1: #3987e5; --series-2: #d95926; --critical: #d03b3b; --banner: #2a2414;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--page); color: var(--ink);
       font: 16px/1.55 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 1040px; margin: 0 auto; padding: 32px 16px 64px; }
h1 { font-size: 28px; line-height: 1.2; margin: 0 0 8px; }
h2 { font-size: 20px; margin: 48px 0 8px; }
h3 { font-size: 15px; margin: 0 0 4px; }
p, li { color: var(--ink-2); max-width: 72ch; }
.question { font-size: 18px; color: var(--ink); }
.banner { background: var(--banner); border: 1px solid var(--border); border-radius: 8px; padding: 12px 16px;
          margin: 16px 0 24px; color: var(--ink); }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 16px; }
.table-wrap { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: 14px; }
th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--grid); vertical-align: top; }
th { color: var(--ink-2); font-weight: 600; }
td.n, th.n { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }
svg { display: block; width: 100%; height: auto; overflow: visible; }
svg text { font: 11px system-ui, -apple-system, "Segoe UI", sans-serif; fill: var(--muted); }
svg .lbl { fill: var(--ink-2); }
svg .strong { fill: var(--ink); font-weight: 600; }
svg text.strong, svg text.lbl { paint-order: stroke; stroke: var(--surface); stroke-width: 3px; stroke-linejoin: round; }
.legend { display: flex; gap: 16px; font-size: 13px; color: var(--ink-2); margin: 4px 0 8px; flex-wrap: wrap; }
.key { display: inline-block; width: 14px; height: 2px; vertical-align: middle; margin-right: 6px; }
details { margin-top: 8px; font-size: 14px; }
summary { cursor: pointer; color: var(--ink-2); }
.src { font-size: 12px; color: var(--muted); margin-top: 6px; }
dl { display: grid; grid-template-columns: max-content 1fr; gap: 6px 16px; }
dt { font-weight: 600; } dd { margin: 0; color: var(--ink-2); }
"""


def table(header: list[str], rows: list[list], numeric: set[int] = frozenset()) -> str:
    th = "".join(f'<th class="{"n" if i in numeric else ""}">{esc(h)}</th>' for i, h in enumerate(header))
    trs = "".join("<tr>" + "".join(f'<td class="{"n" if i in numeric else ""}">{esc(str(c))}</td>' for i, c in enumerate(r)) + "</tr>"
                  for r in rows)
    return f'<div class="table-wrap"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>'


def nice_max(v: float) -> float:
    if v <= 0:
        return 1
    import math
    mag = 10 ** math.floor(math.log10(v))
    for m in (1, 2, 2.5, 5, 10):
        if v <= m * mag:
            return m * mag
    return 10 * mag


def ticks(vmax: float) -> list[float]:
    """Round tick values from 0 to vmax: a 1/2/2.5/5 step giving about four intervals."""
    step = nice_max(vmax / 4)
    out, v = [0.0], 0.0
    while v < vmax * 0.9999:      # the last tick is the first one at or above vmax
        v += step
        out.append(v)
    return out


def tradeoff_panel(rule_id: str, pts: list[dict]) -> str:
    """One rule's sweep: good businesses flagged (x) vs fraud $ prevented (y), one dot per cutoff."""
    W, H, L, B, T, Rm = 320, 210, 46, 30, 14, 14
    xmax = max(p["good_businesses_flagged"] for p in pts) * 1.05
    ymax = max(p["loss_prevented"] for p in pts) * 1.05
    sx = lambda v: L + (W - L - Rm) * v / xmax
    sy = lambda v: H - B - (H - B - T) * v / ymax
    parts = []
    ymax, xmax = ticks(ymax)[-1], ticks(xmax)[-1]
    for y in ticks(ymax):
        parts.append(f'<line x1="{L}" x2="{W - Rm}" y1="{sy(y):.1f}" y2="{sy(y):.1f}" stroke="var(--grid)" stroke-width="1"/>')
        parts.append(f'<text x="{L - 6}" y="{sy(y) + 4:.1f}" text-anchor="end">{esc(R.usd(y))}</text>')
    for x in ticks(xmax):
        parts.append(f'<text x="{sx(x):.1f}" y="{H - B + 16}" text-anchor="middle">{x:,.0f}</text>')
    parts.append(f'<line x1="{L}" x2="{W - Rm}" y1="{H - B}" y2="{H - B}" stroke="var(--axis)" stroke-width="1"/>')
    ordered = sorted(pts, key=lambda p: p["good_businesses_flagged"])
    path = " ".join(f'{"M" if i == 0 else "L"}{sx(p["good_businesses_flagged"]):.1f},{sy(p["loss_prevented"]):.1f}' for i, p in enumerate(ordered))
    parts.append(f'<path d="{path}" fill="none" stroke="var(--series-1)" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>')
    for p in ordered:
        x, y = sx(p["good_businesses_flagged"]), sy(p["loss_prevented"])
        tip = (f'cutoff {p["comparator"]} {p["cutoff"]:g}: {R.usd(p["loss_prevented"])} prevented, '
               f'{p["cases_detected"]} of {p["cases"]} cases, {p["good_businesses_flagged"]:,} good businesses flagged, '
               f'{p["payrolls_delayed"]:,} payrolls delayed, {p["reviews_per_day"]:.1f} reviews/day')
        parts.append(f'<g><title>{esc(tip)}</title><circle cx="{x:.1f}" cy="{y:.1f}" r="9" fill="transparent"/>'
                     f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="var(--series-1)" stroke="var(--surface)" stroke-width="2"/></g>')
        tags = [t for t, flag in (("champion", p["is_champion_cutoff"]), ("challenger", p["is_challenger_cutoff"])) if flag]
        if tags:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="8" fill="none" stroke="var(--ink)" stroke-width="1.5"/>')
            # Champion label above the dot, challenger label below, so neighbouring dots never collide.
            anchor = "end" if x > W * 0.55 else "start"
            dx = -10 if anchor == "end" else 10
            dy = 22 if tags == ["challenger"] else -12
            parts.append(f'<text class="strong" x="{x + dx:.1f}" y="{y + dy:.1f}" text-anchor="{anchor}">'
                         f'{esc(" + ".join(tags))} ({p["comparator"]} {p["cutoff"]:g})</text>')
    parts.append(f'<text x="{(L + W - Rm) / 2}" y="{H - 2}" text-anchor="middle" class="lbl">good businesses flagged</text>')
    svg = f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{esc(R.RULE_LABELS[rule_id])} trade-off curve">{"".join(parts)}</svg>'
    rows = [[f'{p["comparator"]} {p["cutoff"]:g}', R.usd(p["loss_prevented"]), f'{p["cases_detected"]}/{p["cases"]}',
             f'{p["good_businesses_flagged"]:,}', f'{p["payrolls_delayed"]:,}', f'{p["reviews_per_day"]:.1f}']
            for p in sorted(pts, key=lambda p: p["cutoff"])]
    tbl = table(["Cutoff", "Fraud $ prevented", "Cases", "Good businesses", "Payrolls delayed", "Reviews/day"], rows, {1, 2, 3, 4, 5})
    return (f'<div class="card"><h3>{esc(R.RULE_LABELS[rule_id])}</h3>{svg}'
            f'<details><summary>Table view</summary>{tbl}</details></div>')


def reviews_chart(weeks: list[dict]) -> str:
    W, H, L, B, T, Rm = 960, 260, 40, 28, 16, 90
    series = {s: [w for w in weeks if w["strategy_id"] == s] for s in ("champion", "challenger")}
    allw = sorted({w["week"] for w in weeks})
    cap = weeks[0]["capacity"]
    ymax = nice_max(max(max(w["avg_reviews"] for w in weeks), cap) * 1.1)
    sx = lambda d: L + (W - L - Rm) * allw.index(d) / max(1, len(allw) - 1)
    sy = lambda v: H - B - (H - B - T) * v / ymax
    parts = []
    for i in range(5):
        y = ymax * i / 4
        parts.append(f'<line x1="{L}" x2="{W - Rm}" y1="{sy(y):.1f}" y2="{sy(y):.1f}" stroke="var(--grid)"/>')
        parts.append(f'<text x="{L - 6}" y="{sy(y) + 4:.1f}" text-anchor="end">{y:,.0f}</text>')
    for d in allw:
        if d.day <= 7 and d.month % 2 == 1:
            parts.append(f'<text x="{sx(d):.1f}" y="{H - B + 16}" text-anchor="middle">{d:%b %y}</text>')
    train_end = R.window()["train_end"]
    split = next((d for d in allw if d >= train_end), None)
    if split:
        parts.append(f'<line x1="{sx(split):.1f}" x2="{sx(split):.1f}" y1="{T}" y2="{H - B}" stroke="var(--axis)"/>')
        parts.append(f'<text x="{sx(split) + 4:.1f}" y="{T + 10}" class="lbl">test months →</text>')
        parts.append(f'<text x="{sx(split) - 4:.1f}" y="{T + 10}" class="lbl" text-anchor="end">← tuning months</text>')
    parts.append(f'<line x1="{L}" x2="{W - Rm}" y1="{sy(cap):.1f}" y2="{sy(cap):.1f}" stroke="var(--ink-2)" stroke-width="1.5"/>')
    parts.append(f'<text x="{W - Rm + 6}" y="{sy(cap) + 4:.1f}" class="strong">capacity {cap:g}</text>')
    for s, color in (("champion", "var(--series-1)"), ("challenger", "var(--series-2)")):
        pts = series[s]
        d = " ".join(f'{"M" if i == 0 else "L"}{sx(w["week"]):.1f},{sy(w["avg_reviews"]):.1f}' for i, w in enumerate(pts))
        parts.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>')
        for w in pts:
            tip = f'{s}, week of {w["week"]:%d %b %Y}: {w["avg_reviews"]:.1f} reviews/day avg, max {w["max_reviews"]}, {w["days_over"]} day(s) over capacity'
            parts.append(f'<g><title>{esc(tip)}</title><circle cx="{sx(w["week"]):.1f}" cy="{sy(w["avg_reviews"]):.1f}" r="6" fill="transparent"/></g>')
        last = pts[-1]
        parts.append(f'<text x="{sx(last["week"]) + 6:.1f}" y="{sy(last["avg_reviews"]) + (12 if s == "challenger" else -4):.1f}" class="lbl">{s}</text>')
    svg = f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Average reviews per business day by week">{"".join(parts)}</svg>'
    legend = ('<div class="legend"><span><span class="key" style="background:var(--series-1)"></span>Champion</span>'
              '<span><span class="key" style="background:var(--series-2)"></span>Challenger</span>'
              '<span><span class="key" style="background:var(--ink-2)"></span>Review capacity</span></div>')
    rows = [[f'{w["week"]:%Y-%m-%d}', w["strategy_id"], f'{w["avg_reviews"]:.1f}', w["max_reviews"], w["days_over"]] for w in weeks]
    tbl = table(["Week", "Rule set", "Avg reviews/day", "Max day", "Days over capacity"], rows, {2, 3, 4})
    return f'<div class="card">{legend}{svg}<details><summary>Table view</summary>{tbl}</details></div>'


def page() -> str:
    w, t = R.window(), R.totals()
    head = R.headline_rows()
    sweep = R.sweep("train")
    panels = "".join(tradeoff_panel(rid, [p for p in sweep if p["rule_id"] == rid]) for rid in R.RULE_LABELS)
    thresholds = [[R.RULE_LABELS[r["rule_id"]], r["action"], f'{r["comparator"]} {r["champion_cutoff"]:g}',
                   f'{r["comparator"]} {r["challenger_cutoff"]:g}' if r["is_kept"] else "retired"] for r in R.challenger_thresholds()]
    overlap = [[R.RULE_LABELS[o["rule_id"]], o["period"], o["cases_detected"], o["cases_only_this_rule"]] for o in R.overlap("champion")]
    harm = [[h["archetype"].replace("_", " "), f'{h["good_alerts"]:,}', R.usd(h["dollar_days"])] for h in R.harm_by_archetype("champion")]
    typ = [[o["typology"].replace("_", " "), o["variant"].replace("_", " "), f'{o["detected"]} of {o["cases"]}', R.usd(o["loss"]),
            R.usd(o["prevented"]), "n/a" if o["median_hours_to_first_hit"] is None else f'{o["median_hours_to_first_hit"]:.1f}']
           for o in R.typology_outcomes("champion", "test")]
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SMB Fraud Rule Lab</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>SMB Fraud Rule Lab</h1>
<p class="question">Which fraud rules should a small-business bank run, at what thresholds, and what does each change cost and save?</p>
<div class="banner"><strong>All data is synthetic.</strong> {esc(w["bank_name"])} is invented, and so are its {t["businesses"]:,} businesses and
{t["transactions"]:,} transactions. The {t["cases"]} fraud cases were planted with an answer key. No number here is a real-world fraud rate.</div>

<h2>Champion vs challenger, on months the tuning never saw</h2>
<p>The champion is the rule set as first written. The challenger re-tunes each rule's cutoff on the first 12 months.
Both are graded on months 13 to 18 ({t["test_cases"]} fraud cases). Ranges are 90% bootstrap ranges over businesses.</p>
<div class="card">{table(["Test months", "Champion", "Challenger"], [list(r) for r in head], {1, 2})}</div>
<p class="src">Source: backtest.bt_strategy_metrics, analysis.bootstrap_ci</p>

<h2>Cutoffs</h2>
<div class="card">{table(["Rule", "Action", "Champion cutoff", "Challenger cutoff"], thresholds)}</div>

<h2>The trade-off, rule by rule (tuning months)</h2>
<p>Each dot is one cutoff. Moving right flags more good businesses; moving up prevents more fraud. A curve that flattens
early means looser cutoffs only add friction. Hover a dot for reviews per day and payrolls delayed.</p>
<div class="grid">{panels}</div>
<p class="src">Source: backtest.bt_sweep_metrics (period = train)</p>

<h2>Review load against capacity</h2>
<p>Each alert is a review on the next business day, with at most one review per business per day. Capacity is
{w["reviews_capacity_per_day"]:g} reviews per business day (1.5 analysts). The line shows the weekly average, so single days run higher.</p>
{reviews_chart(R.weekly_reviews())}
<p class="src">Source: backtest.bt_daily_reviews</p>

<h2>Which rules earn their alerts</h2>
<p>A case "only this rule touched" would be missed if the rule were turned off.</p>
<div class="card">{table(["Rule (champion set)", "Period", "Cases touched", "Cases only this rule touched"], overlap, {2, 3})}</div>

<h2>Who the false positives are (champion, test months)</h2>
<p>Good businesses grouped by the hidden archetype the generator gave them. The bank cannot see these labels; the backtest can.</p>
<div class="card">{table(["Kind of business", "Alerts on good businesses", "Dollar-days held"], harm, {1, 2})}</div>

<h2>By fraud type (champion, test months)</h2>
<div class="card">{table(["Typology", "Variant", "Detected", "Loss at stake", "Prevented", "Median hours to first alert"], typ, {2, 3, 4, 5})}</div>

<h2>How sure are we?</h2>
<ul>
<li>Synthetic data flatters rules. I wrote the fraud, so the rules look for exactly the shapes I planted. Real fraud adapts once it starts getting caught.</li>
<li>The test months hold only {t["test_cases"]} cases, so a single case can move recall by several points. That's why the ranges are wide.</li>
<li>Labels here are complete and arrive instantly. In reality, check returns take days and confirmed fraud can take weeks. Modelling that delay is planned for a later phase.</li>
<li>Challenger cutoffs are picked with invented costs (config/backtest.yaml). Different costs pick different cutoffs.</li>
</ul>

<h2>Glossary</h2>
<dl>
<dt>RFI</dt><dd>Request for information: ask the customer for documents. The payment is not stopped.</dd>
<dt>Hold</dt><dd>Delay the payment or the deposited funds until reviewed (assumed 2 days for a good customer).</dd>
<dt>Precision</dt><dd>Share of alerts that landed on fraud (a fraudulent transaction or a fraudster's account).</dd>
<dt>Dollar-days held</dt><dd>Good customers' money held × days held. $10,000 held for 2 days is 20,000 dollar-days.</dd>
<dt>Champion / challenger</dt><dd>The current rule set and a proposed one, graded on the same held-out months.</dd>
</dl>
<p class="src">Built {date.today():%Y-%m-%d} from the warehouse by scripts/build_site.py. Synthetic data, seed 42.</p>
</main>
</body>
</html>
"""


def main() -> None:
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(page())
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
