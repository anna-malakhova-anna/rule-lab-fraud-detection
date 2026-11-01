"""The types page."""
from __future__ import annotations

from scripts import results as R
from scripts.sitegen.components import catbar, esc, page_title, table
from scripts.sitegen.content import STAGE, TYPOLOGY_TEXT


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
