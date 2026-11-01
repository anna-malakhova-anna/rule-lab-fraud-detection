"""The rules page (module F): inventory, quarterly review, change log."""
from __future__ import annotations

from scripts import results as R
from scripts.common import load_yaml
from scripts.docs_governance import SHORT
from scripts.sitegen.components import catbar, page_title, table


def rules() -> str:
    reviews = load_yaml("governance.yaml")["quarterly_review"]["reviews_without_added_value"]
    inv = R.rule_inventory()
    inventory = [[R.RULE_LABELS[r["rule_id"]], r["owner"], r["status"].replace("_", " "), r["action"], f'{r["cutoff"]:g}',
                  R.pct(r["test_precision"], 1), R.num(r["test_alerts_per_day"], 1),
                  "" if r["test_unique_cases"] is None else r["test_unique_cases"], r["latest_recommendation"] or "",
                  f'{r["last_changed"]:%Y-%m-%d}'] for r in inv]
    why = [[R.RULE_LABELS[r["rule_id"]], r["rationale"], R.retirement_trigger(r, reviews)] for r in inv]
    q = R.quarterly_review()
    quarters = sorted({r["quarter"] for r in q})
    latest = quarters[-1]
    cells: dict[str, dict[str, str]] = {}
    for r in q:
        cells.setdefault(r["rule_id"], {})[r["quarter"]] = SHORT[r["recommendation"]]
    matrix = [[R.RULE_LABELS[rid]] + [c[x] for x in quarters] for rid, c in cells.items()]
    last = [[R.RULE_LABELS[r["rule_id"]] + (f' (alerts from {r["judged_quarter"]})' if r["lag_quarters"] else ""),
             f'{r["alerts"]:,}', R.pct(r["precision_known"], 1), R.pct(r["break_even_precision"], 2), r["unique_cases"],
             R.usd(r["added_value"]), r["recommendation"]] for r in q if r["quarter"] == latest]
    changes = [[c["change_no"], R.RULE_LABELS[c["rule_id"]], c["change"], "" if c["threshold"] is None else f'{c["threshold"]:g}',
                c["action"] or "", c["decision"], c["backtest"]] for c in R.rule_changes()]
    running = sum(r["is_running"] for r in inv)
    flagged = [r for r in q if r["quarter"] == latest and r["recommendation"] not in ("keep", "too early")]
    return f"""{page_title("Rules", "Inventory, quarterly review and change log")}
{catbar([("#inventory", "Inventory"), ("#review", "Quarterly review"), ("#history", "Every review"), ("#changes", "Change log")])}
<p>Every rule has an owner, a reason it exists, a record of each change and the backtest that justified it, and a
trigger for retiring it. Once a quarter, a review job looks at each running rule with only the labels the bank had by
then, and flags it to retune, retire or investigate.</p>
<div class="stats">
<div class="stat"><b>{len(inv)}</b><span>rules in the inventory, {running} of them running in the recommended set</span></div>
<div class="stat"><b>{len(flagged)}</b><span>flagged at the review after {latest}</span></div>
<div class="stat"><b>{len(changes)}</b><span>changes in the log, each tied to a decision record</span></div>
</div>

<h2 id="inventory">Inventory</h2>
<p>Test-month figures are each rule on its own at the cutoff it runs at. "Cases only it caught" is within the
recommended rule set; launch controls and vendor signals are not in that set.</p>
<div class="card">{table(["Rule", "Owner", "Status", "Action", "Cutoff", "Precision (test)", "Alerts per day", "Cases only it caught",
                         "Latest review", "Last changed"], inventory, {4, 5, 6, 7})}</div>
<details><summary>Why each rule exists, and when to retire it</summary>
<div class="card">{table(["Rule", "Rationale", "Retirement trigger"], why)}</div></details>
<p class="src">Source: backtest.gov_rule_inventory; owners and rationale from config/rules.yaml. Register: docs/governance/rule-register.md</p>

<h2 id="review">Quarterly review, after {latest}</h2>
<p>A rule is a <b>retire candidate</b> when it adds no fraud dollars on top of the other rules for {reviews} reviews in
a row. That is leave-one-out: run the rules without it and see what is lost. Catching a case earlier counts, so a rule
can be worth keeping with no case to itself. It is flagged to <b>retune</b> when its precision is below its
break-even (the precision at which its false alarms cost as much as it saves), and for <b>drift</b> when its volume
doubles or halves against the quarter before. Fraud confirmed months later (mule accounts, credit bust-outs) is judged
on an older quarter of alerts, so a missing label isn't mistaken for a false alarm.</p>
<div class="card">{table(["Rule", "Alerts judged", "Precision known", "Break-even", "Cases only it caught", "Fraud $ it added",
                         "Recommendation"], last, {1, 2, 3, 4, 5})}</div>

<h2 id="history">Every review</h2>
<p>A flag is a prompt for a person, not a decision. R9 is the warning: it guards against ACH return fraud, which only
starts in month 12, so in the reviews before that it adds nothing and looks retirable.</p>
<div class="card">{table(["Rule"] + [f"After {x}" for x in quarters], matrix)}</div>
<p class="src">Source: backtest.gov_rule_quarterly. Settings: config/governance.yaml</p>

<h2 id="changes">Change log</h2>
<p>A change ships with its entry in config/rule_changes.yaml; the build fails if a rule's cutoff or action differs
from its latest entry. What a proposed change must show first: docs/governance/rule-change-template-DRAFT.md.</p>
<div class="card">{table(["#", "Rule", "Change", "Cutoff after", "Action after", "Decision", "Backtest that justified it"], changes, {0, 3})}</div>
"""
