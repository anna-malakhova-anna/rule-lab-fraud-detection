"""Shared page pieces: tables, titles, category bars, the logo and the page shell."""
from __future__ import annotations

import html

from scripts import results as R
from scripts.sitegen.style import CSS

esc = html.escape


def table(header: list[str], rows: list[list], numeric: set[int] = frozenset()) -> str:
    th = "".join(f'<th class="{"n" if i in numeric else ""}">{esc(h)}</th>' for i, h in enumerate(header))
    trs = "".join("<tr>" + "".join(f'<td class="{"n" if i in numeric else ""}">{esc(str(c))}</td>' for i, c in enumerate(r)) + "</tr>"
                  for r in rows)
    return f'<div class="table-wrap"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>'


NAV = [("index.html", "Overview"), ("tradeoffs.html", "Trade-offs"), ("riskops.html", "Risk Ops"),
       ("launch.html", "Launch review"), ("vendors.html", "Vendors"), ("types.html", "Fraud types"),
       ("monitoring.html", "Monitoring"), ("limitations.html", "How sure are we"), ("glossary.html", "Glossary")]


ICONS = {
    # Simple line icons, drawn here (no third-party marks).
    "shield": '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z"/><path d="M9 12l2 2 4-4"/></svg>',
    "people": '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c.8-3.5 3.4-5.5 6.5-5.5s5.7 2 6.5 5.5"/><path d="M16 4.5a3.5 3.5 0 010 7"/><path d="M18 14.8c2 .7 3.2 2.5 3.6 5.2"/></svg>',
    "queue": '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 8h8M8 12h8M8 16h5"/></svg>',
}


# The logo: a lab flask tipped over, its liquid running to the neck and coins pouring out. Drawn here as inline
# SVG in the site's own colour tokens (so it follows dark mode); no image file, no third-party mark.
FLASK = "M17 6 V16 L8 33 Q6.5 37 10.5 37 H29.5 Q33.5 37 32 33 L23 16 V6 Z"
LOGO = f"""<svg class="logo" viewBox="0 2 48 48" width="40" height="40" role="img" aria-label="Rule Lab logo: a flask pouring coins">
<defs><clipPath id="logo-flask"><path transform="rotate(118 20 22)" d="{FLASK}"/></clipPath></defs>
<path transform="rotate(118 20 22)" d="{FLASK}" fill="var(--brand-wash)"/>
<rect x="-10" y="21" width="80" height="40" fill="var(--brand)" clip-path="url(#logo-flask)"/>
<g transform="rotate(118 20 22)" fill="none" stroke="var(--brand-deep)" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round">
<path d="{FLASK}"/><path d="M14.5 6 H25.5"/></g>
<g stroke="var(--brand-deep)" stroke-width="1.5" fill="#E0A93B">
<circle cx="37.5" cy="35.5" r="3.3"/><circle cx="34" cy="42" r="3.3"/><circle cx="41" cy="45.5" r="3.3"/></g>
<g stroke="var(--brand-deep)" stroke-width="0.9" fill="none">
<circle cx="37.5" cy="35.5" r="1.7"/><circle cx="34" cy="42" r="1.7"/><circle cx="41" cy="45.5" r="1.7"/></g>
</svg>"""


def page_title(title: str, subtitle: str = "") -> str:
    sub = f'<p class="subtitle">{esc(subtitle)}</p>' if subtitle else ""
    return f'<div class="title"><h1 class="display">{esc(title)}</h1>{sub}</div>'


def catbar(links: list[tuple[str, str]]) -> str:
    sep = ' <span class="sep">|</span> '   # spaces give the line somewhere to wrap
    return '<nav class="catbar">' + sep.join(f'<a href="{h}">{esc(t)}</a>' for h, t in links) + "</nav>"


def shell(title: str, body: str, depth: int = 0, current: str = "") -> str:
    up = "../" * depth
    # Fraud types is the button on the right; How sure are we lives in the footer. The text links skip both.
    current_attr = ' aria-current="page"'
    links = "".join(f'<a href="{up}{href}"{current_attr if href == current else ""}>{esc(name)}</a>'
                    for href, name in NAV[1:] if href not in ("types.html", "limitations.html"))
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
<a class="brand" href="{up}index.html">{LOGO}<span class="wordmark">Rule Lab</span></a>
<nav class="links">{links}</nav>
<div class="pills"><a class="pill solid" href="{up}types.html">Fraud types</a></div>
</div></header>
<div class="banner"><div class="banner-in"><strong>All data is synthetic.</strong> {esc(w["bank_name"])} is invented, and so are its
{t["businesses"]:,} businesses and {t["transactions"]:,} transactions. The {t["cases"]} fraud cases were planted with an answer key.
No number here is a real-world fraud rate.</div></div>
<main>
{body}
</main>
<footer><p><a href="{up}limitations.html">How sure are we?</a> What flatters these numbers, and what they leave out.</p>
<p class="src">Built from the warehouse by <code>make site</code>. Synthetic data, seed 42.</p></footer>
</body>
</html>
"""
