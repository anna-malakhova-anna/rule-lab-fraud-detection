"""The pre-launch risk review for instant payouts (module C): docs/launch/instant-payouts-review-DRAFT.md.
Same three-part format as the stakeholder pack (exec, ops, engineering). Numbers are generated; prose is a draft."""
from __future__ import annotations

from pathlib import Path

from scripts import results as R
from scripts.common import ROOT, load_yaml
from scripts.docs_stakeholder import evidence_fields

DOC = ROOT / "docs" / "launch" / "instant-payouts-review-DRAFT.md"


def _controls() -> tuple[list[dict], dict, dict]:
    rows = R.launch_controls()
    alone = [r for r in rows if r["rule_id"]]
    return alone, next(r for r in rows if r["strategy_id"] == "champion"), next(r for r in rows if r["strategy_id"] == "launch_controls")


def blocks() -> dict[str, str]:
    alone, today, together = _controls()
    launch = R.launch_date()
    tm = R.launch_threat_model()
    threat = []
    for t, label in R.TYPOLOGY_LABELS.items():
        before = next((r for r in tm if r["typology"] == t and r["launch_phase"] == "before launch" and r["strategy_id"] == "champion"), None)
        after = next((r for r in tm if r["typology"] == t and r["launch_phase"] == "after launch" and r["strategy_id"] == "champion"), None)
        if after:
            threat.append((label, R.pct(before["share_prevented"]) if before else "n/a",
                           f"{after['instant_loss_payments']} of {after['loss_payments']}", R.pct(after["share_prevented"])))
    threat_tbl = R.markdown_table(["Fraud type (test months)", "Stopped before launch", "Cash-outs sent instant after launch",
                                   "Stopped after launch, no controls"], threat)
    blind = R.markdown_table(["Running rule", "Reason code", f"Fraud $ it stopped before {launch:%d %b %Y} only at the cash-out itself"],
                             [(R.RULE_LABELS[b["rule_id"]], f"`{b['reason_code']}`", R.usd(b["stopped_only_at_the_payment"]))
                              for b in R.launch_blind_spots()])
    ctl = R.markdown_table(["After launch", "Fraud $ stopped", "Added to today's rules", "Good payouts slowed",
                            "Good businesses slowed", "Net value", "Launch with it?"],
                           [("Today's rules, no controls", R.usd(today["loss_prevented"]), "", "", "", "", "")]
                           + [(R.RULE_LABELS[r["rule_id"]], R.usd(r["loss_prevented"]), R.usd(r["added_vs_today"]),
                               R.num(r["good_payouts_delayed"]), R.num(r["good_businesses_delayed"]), R.usd(r["net_value"]),
                               "yes" if r["net_value"] > 0 else "no") for r in alone]
                           + [("All four together", R.usd(together["loss_prevented"]), R.usd(together["added_vs_today"]),
                               R.num(together["good_payouts_delayed"]), R.num(together["good_businesses_delayed"]),
                               R.usd(together["net_value"]), "")])
    rules = load_yaml("rules.yaml")["rules"]
    eng = R.markdown_table(["Control", "Pre-send check", "Cutoff", "Reason code", "What must be logged"],
                           [(R.RULE_LABELS[r["rule_id"]], rules[r["rule_id"]]["score"],
                             f"{rules[r['rule_id']]['comparator']} {rules[r['rule_id']]['threshold']:g}",
                             f"`{rules[r['rule_id']]['reason_code']}`",
                             ", ".join(f"`{f}`" for f in evidence_fields(r["rule_id"]))) for r in alone])
    return {"launch-threat": threat_tbl, "launch-blind-spots": blind, "launch-controls": ctl, "launch-eng": eng}


def documents() -> dict[Path, dict[str, str]]:
    return {DOC: blocks()}
