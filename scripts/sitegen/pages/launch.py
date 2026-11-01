"""The new product launch review page (module C): instant payouts."""
from __future__ import annotations

from scripts import results as R
from scripts.sitegen.components import catbar, page_title, table


def launch() -> str:
    rows = R.launch_controls()
    today = next(r for r in rows if r["strategy_id"] == "champion")
    together = next(r for r in rows if r["strategy_id"] == "launch_controls")
    alone = [r for r in rows if r["rule_id"]]
    best = max(alone, key=lambda r: r["net_value"])
    ctl = [[R.RULE_LABELS[r["rule_id"]], R.usd(r["added_vs_today"]), f'{r["good_payouts_delayed"]:,}',
            f'{r["good_businesses_delayed"]:,}', R.usd(r["net_value"]), "yes" if r["net_value"] > 0 else "no"] for r in alone]
    ctl.append(["All four together", R.usd(together["added_vs_today"]), f'{together["good_payouts_delayed"]:,}',
                f'{together["good_businesses_delayed"]:,}', R.usd(together["net_value"]), ""])
    tm = R.launch_threat_model()
    threat = []
    for t, label in R.TYPOLOGY_LABELS.items():
        b = next((r for r in tm if r["typology"] == t and r["launch_phase"] == "before launch" and r["strategy_id"] == "champion"), None)
        a = next((r for r in tm if r["typology"] == t and r["launch_phase"] == "after launch" and r["strategy_id"] == "champion"), None)
        c = next((r for r in tm if r["typology"] == t and r["launch_phase"] == "after launch" and r["strategy_id"] == "launch_controls"), None)
        if a:
            threat.append([label, R.pct(b["share_prevented"]) if b else "n/a", f'{a["instant_loss_payments"]} of {a["loss_payments"]}',
                           R.pct(a["share_prevented"]), R.pct(c["share_prevented"])])
    blind = [[R.RULE_LABELS[b["rule_id"]], b["reason_code"], R.usd(b["stopped_only_at_the_payment"])] for b in R.launch_blind_spots()]
    before = [r for r in tm if r["strategy_id"] == "champion" and r["launch_phase"] == "before launch"]
    share_before = sum(r["loss_prevented"] for r in before) / sum(r["loss_at_stake"] for r in before)
    return f"""{page_title("Launch review", f"Instant payouts, launched {R.launch_date():%d %b %Y}")}
{catbar([("#controls", "Controls"), ("#threats", "Threat model"), ("#blind", "Rule blind spots")])}
<p>From the launch date, businesses can send payouts that arrive in seconds. That's a feature for honest customers, and
for fraudsters it removes the time between the money leaving and anyone noticing. The rules here score a payment after
it is sent; on a standard payment there is still time to hold it, on an instant one there isn't. Fraudsters in the
simulation adapt: most cash-outs switch to instant, and big ones are split under the per-payout cap.</p>
<div class="stats">
<div class="stat"><b>{R.pct(share_before)}</b><span>of fraud dollars today's rules stopped before launch (test months)</span></div>
<div class="stat"><b>{R.pct(today["loss_prevented"] / today["loss_at_stake"])}</b><span>after launch, with no controls</span></div>
<div class="stat"><b>{R.usd(best["added_vs_today"])}</b><span>added by the best single control ({best["rule_id"].split("_")[0]}), slowing {best["good_businesses_delayed"]:,} good businesses</span></div>
</div>

<h2 id="controls">Controls to build in before launch</h2>
<p>Each control is a check made before the payout is sent. When it trips, the payout simply goes the standard way, which
gives the other rules their window back. Nobody is refused, but the customer waits about a day. Net value prices each
good business slowed down like any good business flagged ($150, the stated cost in config/backtest.yaml).</p>
<div class="card">{table(["Control (after launch)", "Fraud $ added to today's rules", "Good payouts slowed", "Good businesses slowed",
                         "Net value", "Launch with it?"], ctl, {1, 2, 3, 4})}</div>
<p class="src">Source: backtest.bt_launch_controls. Each control is also a rule with a playbook (docs/playbooks/C*.md).</p>

<h2 id="threats">Threat model: what gets faster</h2>
<div class="card">{table(["Fraud type (test months)", "Stopped before launch", "Cash-outs sent instant", "Stopped after, no controls",
                         "Stopped after, all controls"], threat, {1, 2, 3, 4})}</div>
<p class="src">Source: backtest.bt_launch_threat_model</p>

<h2 id="blind">Rule blind spots</h2>
<p>Fraud each running rule stopped before launch only by alerting on the cash-out payment itself, with no earlier alert on
the case. Once that payment is instant, the alert arrives after the money has gone.</p>
<div class="card">{table(["Running rule", "Reason code", "Stopped only at the cash-out (before launch)"], blind, {2})}</div>
<p class="src">Source: backtest.bt_launch_blind_spots. Full review with the exec / ops / engineering parts: docs/launch/.</p>
"""
