"""Inline SVG charts. Every chart has a hover title per mark and a table view (dataviz guidance)."""
from __future__ import annotations

from scripts import results as R
from scripts.sitegen.components import esc, table


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


SERIES_COLORS = ("var(--series-1)", "var(--series-2)")


def weekly_lines(series: list[tuple[str, list[tuple]]], aria: str, reference: tuple[float, str] | None = None,
                 split_at=None) -> str:
    """Weekly line chart, at most two series (validated pair). Each series is (label, [(week, value, tooltip)]).
    Optional reference line (value, label) and a vertical split (e.g. the end of the tuning months)."""
    W, H, L, B, T, Rm = 960, 260, 40, 28, 16, 90
    weeks = sorted({pt[0] for _, pts in series for pt in pts})
    top = max([pt[1] for _, pts in series for pt in pts] + [reference[0] if reference else 0])
    ymax = nice_max(top * 1.1)
    sx = lambda d: L + (W - L - Rm) * weeks.index(d) / max(1, len(weeks) - 1)
    sy = lambda v: H - B - (H - B - T) * v / ymax
    parts = []
    for i in range(5):
        y = ymax * i / 4
        parts.append(f'<line x1="{L}" x2="{W - Rm}" y1="{sy(y):.1f}" y2="{sy(y):.1f}" stroke="var(--grid)"/>')
        parts.append(f'<text x="{L - 6}" y="{sy(y) + 4:.1f}" text-anchor="end">{y:,.0f}</text>')
    for d in weeks:
        if d.day <= 7 and d.month % 2 == 1:
            parts.append(f'<text x="{sx(d):.1f}" y="{H - B + 16}" text-anchor="middle">{d:%b %y}</text>')
    split = next((d for d in weeks if split_at and d >= split_at), None)
    if split and split != weeks[0]:
        parts.append(f'<line x1="{sx(split):.1f}" x2="{sx(split):.1f}" y1="{T}" y2="{H - B}" stroke="var(--axis)"/>')
        parts.append(f'<text x="{sx(split) + 4:.1f}" y="{T + 10}" class="lbl">test months →</text>')
        parts.append(f'<text x="{sx(split) - 4:.1f}" y="{T + 10}" class="lbl" text-anchor="end">← tuning months</text>')
    if reference:
        parts.append(f'<line x1="{L}" x2="{W - Rm}" y1="{sy(reference[0]):.1f}" y2="{sy(reference[0]):.1f}" stroke="var(--ink-2)" stroke-width="1.5"/>')
        parts.append(f'<text x="{W - Rm + 6}" y="{sy(reference[0]) + 4:.1f}" class="strong">{esc(reference[1])}</text>')
    for k, (label, pts) in enumerate(series):
        color = SERIES_COLORS[k]
        d = " ".join(f'{"M" if i == 0 else "L"}{sx(w):.1f},{sy(v):.1f}' for i, (w, v, _) in enumerate(pts))
        parts.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>')
        for w, v, tip in pts:
            parts.append(f'<g><title>{esc(tip)}</title><circle cx="{sx(w):.1f}" cy="{sy(v):.1f}" r="6" fill="transparent"/></g>')
        w, v, _ = pts[-1]
        parts.append(f'<text x="{sx(w) + 6:.1f}" y="{sy(v) + (12 if k else -4):.1f}" class="lbl">{esc(label)}</text>')
    keys = "".join(f'<span><span class="key" style="background:{SERIES_COLORS[k]}"></span>{esc(lbl)}</span>'
                   for k, (lbl, _) in enumerate(series))
    if reference:
        keys += f'<span><span class="key" style="background:var(--ink-2)"></span>{esc(reference[1])}</span>'
    svg = f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{esc(aria)}">{"".join(parts)}</svg>'
    return f'<div class="legend">{keys}</div>{svg}'


def reviews_chart(weeks: list[dict]) -> str:
    cap = weeks[0]["capacity"]
    series = [(name.capitalize(), [(w["week"], w["avg_reviews"],
                                    f'{name}, week of {w["week"]:%d %b %Y}: {w["avg_reviews"]:.1f} reviews/day avg, '
                                    f'max {w["max_reviews"]}, {w["days_over"]} day(s) over capacity')
                                   for w in weeks if w["strategy_id"] == name])
              for name in ("champion", "challenger")]
    chart = weekly_lines(series, "Average reviews per business day by week", (cap, f"capacity {cap:g}"),
                         R.window()["train_end"])
    rows = [[f'{w["week"]:%Y-%m-%d}', w["strategy_id"], f'{w["avg_reviews"]:.1f}', w["max_reviews"], w["days_over"]] for w in weeks]
    tbl = table(["Week", "Rule set", "Avg reviews/day", "Max day", "Days over capacity"], rows, {2, 3, 4})
    return f'<div class="card">{chart}<details><summary>Table view</summary>{tbl}</details></div>'


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
