"""Build the static results page (site/index.html) from the warehouse.

Every number comes from scripts/results.py. Charts are inline SVG drawn here: no third-party scripts,
fonts, images or logos (scripts/site_check.py refuses them).

  uv run python -m scripts.build_site
"""
from __future__ import annotations

import html
import shutil
from datetime import date

from scripts import results as R
from scripts.common import ROOT

OUT = ROOT / "site" / "index.html"
esc = html.escape

CSS = """
/* Palette: slate #4C5C8A and its undertones for the page; a slightly more saturated slate and an amber for chart
   marks (validated with the dataviz palette checker in both modes). */
:root {
  color-scheme: light;
  --page: #F7F5EF; --surface: #FFFFFF; --header: #FBFAF6; --tint: #E7EAF4; --tint-2: #F0F2F8;
  --ink: #161A26; --ink-2: #4A4F5E; --muted: #8A8D97;
  --brand: #4C5C8A; --brand-deep: #2E3858; --brand-soft: #7F8DBA; --brand-wash: #D9DEEF;
  --hero-a: #1B2030; --hero-b: #2E3858; --hero-c: #4C5C8A; --hero-ink: #F4F1E8;
  --grid: #E3E1DA; --axis: #C6C4BB; --border: rgba(22,26,38,0.10);
  --series-1: #4560AE; --series-2: #C26E1A; --banner: #E7EAF4;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --page: #12151F; --surface: #1C2030; --header: #161A26; --tint: #262C42; --tint-2: #1F2436;
    --ink: #EEF0F6; --ink-2: #C3C7D4; --muted: #8E93A3;
    --brand: #9AA8D6; --brand-deep: #C9D1EE; --brand-soft: #7F8DBA; --brand-wash: #2E3858;
    --hero-a: #0E1018; --hero-b: #1F2640; --hero-c: #3A4770; --hero-ink: #F4F1E8;
    --grid: #2A2F40; --axis: #3A4054; --border: rgba(255,255,255,0.10);
    --series-1: #6F84D2; --series-2: #C98236; --banner: #262C42;
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --page: #12151F; --surface: #1C2030; --header: #161A26; --tint: #262C42; --tint-2: #1F2436;
  --ink: #EEF0F6; --ink-2: #C3C7D4; --muted: #8E93A3;
  --brand: #9AA8D6; --brand-deep: #C9D1EE; --brand-soft: #7F8DBA; --brand-wash: #2E3858;
  --hero-a: #0E1018; --hero-b: #1F2640; --hero-c: #3A4770; --hero-ink: #F4F1E8;
  --grid: #2A2F40; --axis: #3A4054; --border: rgba(255,255,255,0.10);
  --series-1: #6F84D2; --series-2: #C98236; --banner: #262C42;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--page); color: var(--ink);
       font: 16px/1.6 system-ui, -apple-system, "Segoe UI", sans-serif; }
a { color: var(--brand); }
.display, .hero h1, .stat b { font-family: "Avenir Next Condensed", "Helvetica Neue", "Arial Narrow", system-ui, sans-serif;
  font-stretch: condensed; font-weight: 800; letter-spacing: -0.01em; }
.serif { font-family: "Iowan Old Style", Charter, Georgia, serif; }

/* Header: light bar, wordmark, links, two pill buttons */
.topbar { background: var(--header); border-bottom: 1px solid var(--border); }
.topbar-in { max-width: 1160px; margin: 0 auto; padding: 14px 16px; display: flex; align-items: center; gap: 28px; flex-wrap: wrap; }
/* Same family as the headlines, but the regular (wider, rounder) width instead of the condensed cut. */
.wordmark { font-family: "Avenir Next", "Helvetica Neue", "Arial", system-ui, sans-serif; font-stretch: expanded;
  font-weight: 800; font-size: 26px; text-transform: uppercase; color: var(--brand); text-decoration: none;
  letter-spacing: 0.04em; line-height: 1; }
.links { display: flex; gap: 22px; flex-wrap: wrap; }
.links a { color: var(--ink); text-decoration: none; font-size: 16px; }
.links a:hover, .links a[aria-current] { color: var(--brand); text-decoration: underline; text-underline-offset: 6px; }
.pills { margin-left: auto; display: flex; gap: 10px; flex-wrap: wrap; }
.pill { display: inline-block; padding: 9px 20px; border-radius: 999px; font-size: 15px; text-decoration: none;
  border: 1.5px solid var(--brand); color: var(--brand); white-space: nowrap; }
.pill.solid { background: var(--brand-deep); border-color: var(--brand-deep); color: var(--hero-ink); }

.banner { background: var(--banner); color: var(--ink); font-size: 14px; }
.banner-in { max-width: 1160px; margin: 0 auto; padding: 10px 16px; }

main { max-width: 1160px; margin: 0 auto; padding: 8px 16px 64px; }

/* Page titles: very large, uppercase, condensed, slate gradient */
.title { text-align: center; padding: 40px 0 8px; }
.display { font-size: clamp(44px, 9vw, 112px); line-height: 0.92; text-transform: uppercase; margin: 0;
  background: linear-gradient(90deg, var(--brand-soft), var(--brand) 55%, var(--brand-deep));
  -webkit-background-clip: text; background-clip: text; color: transparent; }
.subtitle { font-size: clamp(20px, 3vw, 30px); font-weight: 700; color: var(--brand-deep); margin: 14px auto 0; max-width: none; }

/* Category bar: serif links between two rules */
.catbar { border-top: 1.5px solid var(--ink); border-bottom: 1.5px solid var(--ink); margin: 28px 0 32px; padding: 16px 8px;
  text-align: center; font-family: "Iowan Old Style", Charter, Georgia, serif; font-size: 19px; line-height: 2; }
.catbar a { color: var(--brand-deep); text-decoration: none; white-space: nowrap; }
.catbar a:hover { text-decoration: underline; }
.catbar .sep { color: var(--muted); padding: 0 10px; }

/* Overview hero: dark slate gradient band */
.hero { background: linear-gradient(170deg, var(--hero-a) 0%, var(--hero-b) 55%, var(--hero-c) 100%); color: var(--hero-ink);
  border-radius: 0 0 24px 24px; margin: 0 -16px 8px; padding: 48px 32px 40px; }
.hero h1 { font-size: clamp(40px, 7vw, 84px); line-height: 0.95; text-transform: uppercase; margin: 0 0 18px; max-width: 17ch; }
.hero p { color: var(--hero-ink); opacity: 0.88; font-size: 18px; max-width: 62ch; }
.features { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 24px; margin-top: 32px; }
.feature { display: flex; gap: 14px; align-items: flex-start; }
.feature .icon { flex: none; width: 48px; height: 48px; border-radius: 50%; background: var(--brand-wash); color: var(--brand-deep);
  display: grid; place-items: center; }
:root[data-theme="dark"] .feature .icon { color: var(--hero-ink); }
.feature b { display: block; font-size: 22px; line-height: 1.15; }
.feature span { font-size: 14px; opacity: 0.8; }

h2 { font-size: 26px; line-height: 1.2; margin: 52px 0 10px; color: var(--ink); }
h3 { font-size: 16px; margin: 0 0 6px; }
p, li { color: var(--ink-2); max-width: 74ch; }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 18px; }
.card.tint { background: var(--tint); }
.chip { display: inline-block; border: 1.5px solid var(--brand); color: var(--brand-deep); border-radius: 8px; padding: 3px 12px;
  font-size: 14px; margin-bottom: 12px; }
.typecards { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 18px; }
.typecard { background: var(--tint); border-radius: 16px; padding: 22px; text-decoration: none; display: block; }
.typecard h3 { font-size: 26px; line-height: 1.15; color: var(--ink); font-weight: 600; margin: 0 0 8px; }
.typecard p { margin: 0; color: var(--ink-2); }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin: 20px 0; }
.stat { background: var(--tint); border-radius: 16px; padding: 18px; }
.stat b { display: block; font-size: 44px; line-height: 1; color: var(--brand-deep); }
.stat span { font-size: 14px; color: var(--ink-2); }

.table-wrap { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: 14px; }
th, td { text-align: left; padding: 9px 10px; border-bottom: 1px solid var(--grid); vertical-align: top; }
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
dl { display: grid; grid-template-columns: max-content 1fr; gap: 10px 20px; }
dt { font-weight: 600; } dd { margin: 0; color: var(--ink-2); }
footer { max-width: 1160px; margin: 0 auto; padding: 0 16px 40px; }
@media (max-width: 640px) {
  .topbar-in { gap: 12px; } .pills { margin-left: 0; } dl { grid-template-columns: 1fr; }
  .catbar { font-size: 17px; line-height: 1.5; } .catbar .sep { display: none; }
  .catbar a { display: inline-block; margin: 4px 10px; }
  .hero { padding: 32px 18px 28px; }
}
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


def tradeoff_panel(rule_id: str, pts: list[dict], title: str | None = None) -> str:
    """One rule's sweep: good businesses flagged (x) vs fraud $ prevented (y), one dot per cutoff."""
    W, H, L, B, T, Rm = 320, 210, 46, 30, 14, 14
    xmax = max(max(p["good_businesses_flagged"] for p in pts), 4) * 1.05
    ymax = max(max(p["loss_prevented"] for p in pts), 1000) * 1.05
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
    title = title or R.RULE_LABELS[rule_id]
    svg = f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{esc(title)} trade-off curve">{"".join(parts)}</svg>'
    rows = [[f'{p["comparator"]} {p["cutoff"]:g}', R.usd(p["loss_prevented"]), f'{p["cases_detected"]}/{p["cases"]}',
             f'{p["good_businesses_flagged"]:,}', f'{p["payrolls_delayed"]:,}', f'{p["reviews_per_day"]:.1f}']
            for p in sorted(pts, key=lambda p: p["cutoff"])]
    tbl = table(["Cutoff", "Fraud $ prevented", "Cases", "Good businesses", "Payrolls delayed", "Reviews/day"], rows, {1, 2, 3, 4, 5})
    return (f'<div class="card"><h3>{esc(title)}</h3>{svg}'
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


def weekly_bars(weeks: list[dict], markers: list[tuple], label: str) -> str:
    """Weekly event counts for one monitored series, with dated markers (e.g. the first alarm)."""
    W, H, L, B, T, Rm = 720, 220, 34, 28, 28, 12
    n = len(weeks)
    ymax = ticks(max(max(w["events"] for w in weeks), 1) * 1.1)[-1]
    band = (W - L - Rm) / n
    bw = min(24, band * 0.7)
    sx = lambda i: L + band * i + band / 2
    sy = lambda v: H - B - (H - B - T) * v / ymax
    parts = []
    for y in ticks(ymax):
        parts.append(f'<line x1="{L}" x2="{W - Rm}" y1="{sy(y):.1f}" y2="{sy(y):.1f}" stroke="var(--grid)"/>')
        parts.append(f'<text x="{L - 6}" y="{sy(y) + 4:.1f}" text-anchor="end">{y:,.0f}</text>')
    for i, w in enumerate(weeks):
        if w["week"].day <= 7 and w["week"].month % 2 == 1:
            parts.append(f'<text x="{sx(i):.1f}" y="{H - B + 16}" text-anchor="middle">{w["week"]:%b %y}</text>')
        if w["events"] > 0:
            x, y = sx(i) - bw / 2, sy(w["events"])
            r = min(4, H - B - y)
            # 4px rounded top, square at the baseline.
            path = (f'M{x:.1f},{H - B} L{x:.1f},{y + r:.1f} Q{x:.1f},{y:.1f} {x + r:.1f},{y:.1f} '
                    f'L{x + bw - r:.1f},{y:.1f} Q{x + bw:.1f},{y:.1f} {x + bw:.1f},{y + r:.1f} L{x + bw:.1f},{H - B} Z')
            tip = (f'week of {w["week"]:%d %b %Y}: {w["events"]} ({R.usd(w["amount"])}), '
                   f'trailing mean {w["baseline_mean"]:.1f}{" - ALARM" if w["is_alarm"] else ""}')
            parts.append(f'<g><title>{esc(tip)}</title><path d="{path}" fill="var(--series-1)"/>'
                         f'<rect x="{sx(i) - band / 2:.1f}" y="{T}" width="{band:.1f}" height="{H - B - T}" fill="transparent"/></g>')
    parts.append(f'<line x1="{L}" x2="{W - Rm}" y1="{H - B}" y2="{H - B}" stroke="var(--axis)"/>')
    for k, (d, text) in enumerate(markers):
        idx = next((i for i, w in enumerate(weeks) if w["week"] >= d.date()), None)
        if idx is not None:
            x = L + band * idx
            anchor, dx = ("end", -4) if k == 0 else ("start", 4)
            parts.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{T - 18}" y2="{H - B}" stroke="var(--ink-2)" stroke-width="1.5"/>')
            parts.append(f'<text x="{x + dx:.1f}" y="{T - 8}" text-anchor="{anchor}" class="strong">{esc(text)} {d:%d %b}</text>')
    svg = f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{esc(label)}">{"".join(parts)}</svg>'
    rows = [[f'{w["week"]:%Y-%m-%d}', w["events"], R.usd(w["amount"]), R.usd(w["unalerted_amount"]),
             f'{w["baseline_mean"]:.1f}', "alarm" if w["is_alarm"] else ""] for w in weeks if w["events"] or w["is_alarm"]]
    tbl = table(["Week", "Events", "Amount", "No champion alert", "Trailing mean", ""], rows, {1, 2, 3, 4})
    return f'<div class="card">{svg}<details><summary>Table view</summary>{tbl}</details></div>'


TYPOLOGY_TEXT = {
    "check_deposit_fraud": "Checks that will bounce are deposited by mobile, and most of the money is withdrawn before they come back. Some accounts are opened for it; some are existing customers turning to it.",
    "bec_vendor_change": "A fraudster posing as a real vendor gets the vendor's bank details changed, and the business pays its next invoice to the fraudster. The victim is a good customer.",
    "synthetic_shell": "Rings of freshly incorporated businesses applying with shared devices, phones, addresses and email domains. They are funded fast, then bust out with bad checks.",
    "money_mule": "An account collects many small payments from senders it has never seen and sweeps them out within a day or two.",
    "account_takeover": "A login from a new device, a change to the email or phone on file, a new payee, and payouts, all within hours. The owner notices days later.",
    "ach_return_fraud": "Money pulled in by ACH debit from accounts the business doesn't control, sent straight out, and returned as unauthorized days later. It starts in month 12 and was found by monitoring (INV-001).",
    "credit_bust_out": "Months of clean use of a line of credit, then round-trip money pumped through the account so the limit is raised, then the whole line drawn and wired out within hours.",
}

NAV = [("index.html", "Overview"), ("tradeoffs.html", "Trade-offs"), ("types.html", "Fraud types"),
       ("monitoring.html", "Monitoring"), ("limitations.html", "How sure are we"), ("glossary.html", "Glossary")]


ICONS = {
    # Simple line icons, drawn here (no third-party marks).
    "shield": '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z"/><path d="M9 12l2 2 4-4"/></svg>',
    "people": '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c.8-3.5 3.4-5.5 6.5-5.5s5.7 2 6.5 5.5"/><path d="M16 4.5a3.5 3.5 0 010 7"/><path d="M18 14.8c2 .7 3.2 2.5 3.6 5.2"/></svg>',
    "queue": '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 8h8M8 12h8M8 16h5"/></svg>',
}


def page_title(title: str, subtitle: str = "") -> str:
    sub = f'<p class="subtitle">{esc(subtitle)}</p>' if subtitle else ""
    return f'<div class="title"><h1 class="display">{esc(title)}</h1>{sub}</div>'


def catbar(links: list[tuple[str, str]]) -> str:
    sep = ' <span class="sep">|</span> '   # spaces give the line somewhere to wrap
    return '<nav class="catbar">' + sep.join(f'<a href="{h}">{esc(t)}</a>' for h, t in links) + "</nav>"


def shell(title: str, body: str, depth: int = 0, current: str = "") -> str:
    up = "../" * depth
    # Fraud types is the button on the right, so the text links skip it.
    links = "".join(f'<a href="{up}{href}"{" aria-current=\"page\"" if href == current else ""}>{esc(name)}</a>'
                    for href, name in NAV[1:] if href != "types.html")
    w, t = R.window(), R.totals()
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · SMB Fraud Rule Lab</title>
<style>{CSS}</style>
</head>
<body>
<header class="topbar"><div class="topbar-in">
<a class="wordmark" href="{up}index.html">Rule Lab</a>
<nav class="links">{links}</nav>
<div class="pills"><a class="pill solid" href="{up}types.html">Fraud types</a></div>
</div></header>
<div class="banner"><div class="banner-in"><strong>All data is synthetic.</strong> {esc(w["bank_name"])} is invented, and so are its
{t["businesses"]:,} businesses and {t["transactions"]:,} transactions. The {t["cases"]} fraud cases were planted with an answer key.
No number here is a real-world fraud rate.</div></div>
<main>
{body}
</main>
<footer><p class="src">Built {date.today():%Y-%m-%d} from the warehouse by scripts/build_site.py. Synthetic data, seed 42.</p></footer>
</body>
</html>
"""


def overview() -> str:
    t = R.totals()
    rules = R.challenger_thresholds()
    champ, chall = R.typology_totals("champion"), R.typology_totals("challenger")
    typ = [[label, champ[k]["cases"], champ[k]["detected"], chall[k]["detected"], R.usd(champ[k]["loss"]),
            R.usd(champ[k]["prevented"]), R.usd(chall[k]["prevented"])] for k, label in R.TYPOLOGY_LABELS.items() if k in champ]
    cl = R.credit_losses()
    ch, cc = cl.get(("champion", "test")), cl.get(("challenger", "test"))
    credit = [["Honest businesses that defaulted", ch["honest_defaults"], cc["honest_defaults"]],
              ["Balance when they missed a payment", R.usd(ch["balance_at_missed_payment"]), R.usd(cc["balance_at_missed_payment"])],
              ["Of which flagged by a rule in the 90 days before", R.usd(ch["balance_flagged_before_default"]), R.usd(cc["balance_flagged_before_default"])],
              ["Holds put on these struggling businesses", ch["holds_on_honest_defaulters"], cc["holds_on_honest_defaulters"]]]
    thresholds = [[R.RULE_LABELS[r["rule_id"]], R.action_cell(r), R.champion_cell(r), R.challenger_cell(r)] for r in rules]
    m = R.strategy_metrics("test")
    ch_m, cl_m = m["champion"], m["challenger"]
    return f"""<section class="hero">
<h1>Which rules should a small-business bank run?</h1>
<p>At what thresholds, and what does each change cost and save? Every rule here is graded on the three things a fraud
strategist actually trades off.</p>
<div class="features">
<div class="feature"><div class="icon">{ICONS["shield"]}</div><div><b>Fraud caught</b><span>Dollars prevented and cases detected</span></div></div>
<div class="feature"><div class="icon">{ICONS["people"]}</div><div><b>Good customers hurt</b><span>Businesses flagged, money held, payrolls delayed</span></div></div>
<div class="feature"><div class="icon">{ICONS["queue"]}</div><div><b>Review load</b><span>Reviews per day against a small team's capacity</span></div></div>
</div>
</section>

<div class="stats">
<div class="stat"><b>{R.pct(cl_m["dollar_recall"])}</b><span>of fraud dollars prevented by the challenger in the test months (champion: {R.pct(ch_m["dollar_recall"])})</span></div>
<div class="stat"><b>{cl_m["cases_detected"]} / {cl_m["cases"]}</b><span>fraud cases detected by the challenger (champion: {ch_m["cases_detected"]})</span></div>
<div class="stat"><b>{cl_m["good_businesses_flagged"]:,}</b><span>good businesses flagged by the challenger (champion: {ch_m["good_businesses_flagged"]:,})</span></div>
<div class="stat"><b>{cl_m["days_over_capacity"]} / {cl_m["business_days"]}</b><span>test-month days over review capacity (champion: {ch_m["days_over_capacity"]})</span></div>
</div>

<h2>Champion vs challenger, on months the tuning never saw</h2>
<p>The champion is what runs today: nine rules covering deposits, payments, onboarding, mules, account takeover and ACH
debits. The challenger adds three rules for the new line of credit. New cutoffs were tuned on the first 12 months
using only the fraud confirmed by then. Both rule sets are graded on months 13 to 18 ({t["test_cases"]} fraud cases).
Ranges are 90% bootstrap ranges over businesses.</p>
<div class="card">{table(["Test months", "Champion", "Challenger"], [list(r) for r in R.headline_rows()], {1, 2})}</div>
<p class="src">Source: backtest.bt_strategy_metrics, analysis.bootstrap_ci</p>

<h2>By fraud type (test months)</h2>
<div class="card">{table(["Fraud type", "Cases", "Detected: champion", "Detected: challenger", "Loss at stake", "Prevented: champion", "Prevented: challenger"], typ, {1, 2, 3, 4, 5, 6})}</div>
<p>One page per fraud type: <a href="types.html">Fraud types</a>.</p>

<h2>Credit losses that are not fraud (test months)</h2>
<p>Some honest businesses fail and default on their line. That's credit risk, not fraud, so it is never added to
fraud prevented. Holding a struggling customer's payments still counts as harm.</p>
<div class="card">{table(["", "Champion", "Challenger"], credit, {1, 2})}</div>
<p class="src">Source: backtest.bt_credit_losses</p>

<h2>Cutoffs</h2>
<div class="card">{table(["Rule", "Action", "Champion", "Challenger"], thresholds)}</div>
"""


def tradeoffs() -> str:
    w = R.window()
    sweep = R.sweep("train")
    panels = "".join(tradeoff_panel(rid, [p for p in sweep if p["rule_id"] == rid]) for rid in R.RULE_LABELS)
    overlap = [[R.RULE_LABELS[o["rule_id"]], o["cases_detected"], o["cases_only_this_rule"]]
               for o in R.overlap("challenger") if o["period"] == "test"]
    harm = [[h["archetype"].replace("_", " "), f'{h["good_alerts"]:,}', R.usd(h["dollar_days"])] for h in R.harm_by_archetype("challenger")]
    return f"""{page_title("Trade-offs", "Every cutoff, what it catches and who it hurts")}
{catbar([("#curves", "Cutoff curves"), ("#capacity", "Review load"), ("#overlap", "Overlap"), ("#harm", "Who gets flagged")])}
<h2 id="curves">Each rule's cutoffs (tuning months)</h2>
<p>Each dot is one cutoff. Moving right flags more good businesses; moving up prevents more fraud. A curve that flattens
early means looser cutoffs only add friction. Hover a dot for reviews per day.</p>
<div class="grid">{panels}</div>
<p class="src">Source: backtest.bt_sweep_metrics (period = train, all labels)</p>

<h2 id="capacity">Review load against capacity</h2>
<p>Each alert is a review on the next business day, with at most one review per business per day. Capacity is
{w["reviews_capacity_per_day"]:g} reviews per business day (2.25 analysts for 12,000 businesses).</p>
{reviews_chart(R.weekly_reviews())}

<h2 id="overlap">Which rules earn their alerts (challenger, test months)</h2>
<p>A case "only this rule touched" would be missed if the rule were turned off.</p>
<div class="card">{table(["Rule", "Cases touched", "Cases only this rule touched"], overlap, {1, 2})}</div>

<h2 id="harm">Who the false positives are (challenger, test months)</h2>
<p>Good businesses grouped by the hidden archetype the generator gave them. The bank cannot see these labels; the backtest can.</p>
<div class="card">{table(["Kind of business", "Alerts on good businesses", "Dollar-days held"], harm, {1, 2})}</div>
"""


def types_index() -> str:
    champ, chall = R.typology_totals("champion"), R.typology_totals("challenger")
    cards = ""
    for k, label in R.TYPOLOGY_LABELS.items():
        c, d = champ.get(k), chall.get(k)
        note = f"Test months: {c['cases']} cases; detected {c['detected']} today, {d['detected']} with the challenger." if c else ""
        cards += (f'<a class="typecard" href="types/{k}.html"><span class="chip">{esc(STAGE[k])}</span>'
                  f'<h3>{esc(label)}</h3><p>{esc(TYPOLOGY_TEXT[k])}</p><p class="src">{esc(note)}</p></a>')
    return f"""{page_title("Fraud types", "Seven ways the synthetic bank loses money")}
{catbar([(f"types/{k}.html", v) for k, v in R.TYPOLOGY_LABELS.items()])}
<div class="typecards">{cards}</div>
"""


STAGE = {
    "check_deposit_fraud": "Payments", "bec_vendor_change": "Payments", "synthetic_shell": "Onboarding",
    "money_mule": "Account usage", "account_takeover": "Account usage", "ach_return_fraud": "Payments · emerging",
    "credit_bust_out": "Credit",
}


def type_page(key: str) -> str:
    rows = []
    for period in ("test", "train"):
        a, b = R.typology_totals("champion", period).get(key), R.typology_totals("challenger", period).get(key)
        if a:
            rows.append([f"{period} months", a["cases"], a["detected"], b["detected"], R.usd(a["loss"]), R.usd(a["prevented"]), R.usd(b["prevented"])])
    touch = [[R.RULE_LABELS[r["rule_id"]], r["test_cases"], r["train_cases"]] for r in R.rules_touching(key)]
    variants = [[o["variant"].replace("_", " "), o["cases"], o["detected"], R.usd(o["loss"]), R.usd(o["prevented"]),
                 "n/a" if o["median_hours_to_first_hit"] is None else f'{o["median_hours_to_first_hit"]:.1f}']
                for o in R.typology_outcomes("challenger", "test") if o["typology"] == key]
    others = [(f"{k}.html", v) for k, v in R.TYPOLOGY_LABELS.items()]
    return f"""{page_title(R.TYPOLOGY_LABELS[key], STAGE[key])}
{catbar(others)}
<div class="card tint"><span class="chip">{esc(STAGE[key])}</span><p style="margin:0">{esc(TYPOLOGY_TEXT[key])}</p></div>
<h2>Outcomes</h2>
<div class="card">{table(["Period", "Cases", "Detected: champion", "Detected: challenger", "Loss at stake", "Prevented: champion", "Prevented: challenger"], rows, {1, 2, 3, 4, 5, 6})}</div>
<h2>Rules that touched these cases (challenger)</h2>
<div class="card">{table(["Rule", "Test cases", "Training cases"], touch, {1, 2})}</div>
<h2>By variant (challenger, test months)</h2>
<div class="card">{table(["Variant", "Cases", "Detected", "Loss at stake", "Prevented", "Median hours to first alert"], variants, {1, 2, 3, 4, 5})}</div>
"""


def monitoring() -> str:
    alarms = [[f'{a["week"]:%Y-%m-%d}', a["series"].replace(":", " / ").replace("_", " "), a["events"], f'{a["baseline_mean"]:.1f}',
               R.usd(a["amount"])] for a in R.alarms()]
    ach = R.weekly_series("ach_debit_in:unauthorized")
    first_ach = next(w for w in ach if w["is_alarm"])
    credit = R.weekly_series("credit:payment_missed")
    gap = [[R.RULE_LABELS[g["rule_id"]], f'{g["cases_known"]} of {g["cases_all"]}', R.usd(g["prevented_known"]), R.usd(g["prevented_all"]),
            R.pct(g["precision_known"], 1), R.pct(g["precision_all"], 1)] for g in R.label_delay_gap()]
    w = R.window()
    prec = {}
    for m in R.monthly_precision():
        if m["month"] >= w["train_end"]:
            a = prec.setdefault(m["rule_id"], [0, 0.0, 0.0])
            a[0] += m["alerts"]; a[1] += m["precision_at_maturity"] * m["alerts"]; a[2] += m["precision_eventually"] * m["alerts"]
    prec_rows = [[R.RULE_LABELS[k], f'{v[0]:,}', R.pct(v[1] / v[0], 1), R.pct(v[2] / v[0], 1)] for k, v in sorted(prec.items())]
    return f"""{page_title("Monitoring", "What an analyst could see each week, without labels")}
{catbar([("#ach", "The month-12 pattern"), ("#credit", "Missed credit payments"), ("#labels", "Labels arrive late")])}
<p>Every week, each kind of returned payment (by rail and return reason) and each kind of credit event (missed
payments, charge-offs) is compared with its own previous 12 weeks. No fraud labels are involved: this is what an
analyst could see that week.</p>

<h2 id="ach">How the month-12 pattern was found</h2>
<p>Unauthorized returns on ACH debits had been near zero, then jumped. The first alarm became visible on
{first_ach["week_closes_at"]:%d %b %Y}. The investigation (docs/investigations/INV-001-ach-debit-returns.md, frozen at Phase 2)
led to R9, which now runs in the champion.</p>
{weekly_bars(ach, [(first_ach["week_closes_at"], "alarm visible")], "Unauthorized ACH-debit returns per week")}

<h2 id="credit">Missed payments on the line of credit</h2>
<p>Missed payments come from honest businesses that fail and from bust-outs. The "no champion alert" column in the
table view is the part no rule saw coming.</p>
{weekly_bars(credit, [], "Missed credit payments per week")}

<details><summary>Every alarm in the window (most are bursts of bad checks that the check rules already cover)</summary>
<div class="card">{table(["Week of", "Series", "Events", "Trailing mean", "Amount"], alarms, {2, 3, 4})}</div></details>
<p class="src">Source: monitoring.mon_weekly_alarms</p>

<h2 id="labels">Labels arrive late</h2>
<p>When tuning in month 12, the bank only knows the fraud it has confirmed so far. A bust-out is confirmed around
charge-off, about five months after the money leaves. The credit rules were tuned on what the bank could see at the time:</p>
<div class="card">{table(["Tuned rule (training months)", "Cases the bank knew of (all types)", "Prevented, as seen then", "Prevented, all labels", "Precision, as seen then", "Precision, all labels"], gap, {1, 2, 3, 4, 5})}</div>
<p>Weekly monitoring has the same lag. Precision in the test months, as known 30 days after each week vs eventually:</p>
<div class="card">{table(["Rule", "Alerts", "Precision at 30 days", "Precision eventually"], prec_rows, {1, 2, 3})}</div>
<p class="src">Source: backtest.bt_sweep_metrics_known, backtest.bt_monitoring_precision</p>
"""


def limitations() -> str:
    t = R.totals()
    return f"""{page_title("How sure are we?", "What flatters these numbers, and what they leave out")}
<h2>What flatters these results</h2>
<ul>
<li><strong>I wrote the fraud.</strong> The rules look for exactly the shapes I planted, so detection rates in the 90s say more about my generator than about any real bank. Real fraud adapts once it starts getting caught.</li>
<li><strong>Synthetic bust-outs are clean.</strong> Every one draws the full line within days of an increase, which R12 catches almost perfectly. Real bust-outs are messier and slower.</li>
<li><strong>The final grade uses the full answer key.</strong> Tuning only sees labels known by month 12, but the headline comparison uses every label, including cases a real bank would never confirm.</li>
<li><strong>Generator shortcuts can leak into results.</strong> I've found and fixed two. Bust-out money sent back to the owner's own account made R5 look like a bust-out detector. ACH fraud cash-outs to the owner's account let R5 catch part of the month-12 pattern by luck. I documented the second rather than removing it.</li>
</ul>
<h2>What makes them uncertain</h2>
<ul>
<li><strong>Small samples.</strong> The test months hold {t["test_cases"]} cases across seven fraud types, 6 to 22 each. One case moves a fraud type's numbers a lot; the headline carries bootstrap ranges for that reason.</li>
<li><strong>Invented costs.</strong> Cutoffs are chosen with costs I made up (config/backtest.yaml): $30 a review, $150 per good business flagged, $1,000 per delayed payroll, $300 per good applicant declined. Different costs pick different cutoffs.</li>
<li><strong>Simplified mechanics.</strong> There are no account balances or overdrafts, an RFI is assumed to stop half the fraud, and a hold is assumed to stop all of it.</li>
<li><strong>A thin tuning set for credit.</strong> Bust-out labels arrive about five months after the money leaves, so tuning in month 12 saw only a handful of confirmed bust-outs.</li>
</ul>
<h2>What isn't modelled</h2>
<ul>
<li>Fraud that adapts to the rules: a ring buying aged shelf companies to dodge R6's decline, or money moved out through fake payroll runs to dodge R1.</li>
<li>Customer reactions to friction (churn), chargebacks, and the card rail beyond aggregate spend.</li>
</ul>
"""


def glossary() -> str:
    terms = [
        ("RFI", "Request for information: ask the customer for documents. The payment is not stopped."),
        ("Hold", "Delay the payment, the deposited funds or the credit draw until reviewed (assumed 2 days for a good customer)."),
        ("Block", "At onboarding: decline the application. R6 declines only strong identity links at newly incorporated businesses."),
        ("Precision", "Share of alerts that landed on fraud (a fraudulent transaction or a fraudster's account)."),
        ("Recall", "Share of fraud cases (or fraud dollars) the rules caught."),
        ("Dollar-days held", "Good customers' money held × days held. $10,000 held for 2 days is 20,000 dollar-days."),
        ("Champion / challenger", "The current rule set and a proposed one, graded on the same held-out months."),
        ("Label delay", "The time between a fraud happening and the bank confirming it was fraud."),
        ("Alarm", "A week where a monitored series is far above its own recent normal."),
        ("Bust-out", "Building a clean credit history, raising the limit, then drawing everything and disappearing."),
        ("Charge-off", "The bank writing off a balance it no longer expects to collect (here, 120 days after a missed payment)."),
        ("First-party fraud", "Fraud by the customer themselves, as opposed to someone impersonating or exploiting them."),
    ]
    dl = "".join(f"<dt>{esc(a)}</dt><dd>{esc(b)}</dd>" for a, b in terms)
    return f"""{page_title("Glossary", "The words on these pages, in plain terms")}<div class="card"><dl>{dl}</dl></div>"""


def pages() -> dict[str, tuple[str, str, int]]:
    out = {"index.html": ("Overview", overview(), 0), "tradeoffs.html": ("Trade-offs", tradeoffs(), 0),
           "types.html": ("Fraud types", types_index(), 0), "monitoring.html": ("Monitoring", monitoring(), 0),
           "limitations.html": ("How sure are we", limitations(), 0), "glossary.html": ("Glossary", glossary(), 0)}
    for key, label in R.TYPOLOGY_LABELS.items():
        out[f"types/{key}.html"] = (label, type_page(key), 1)
    return out


def main() -> None:
    site = OUT.parent
    shutil.rmtree(site, ignore_errors=True)
    for rel, (title, body, depth) in pages().items():
        path = site / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(shell(title, body, depth, rel))
    print(f"wrote {len(pages())} pages to {site.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
