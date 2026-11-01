"""Analyst playbooks (module A): one page per rule in docs/playbooks/. The facts block at the top of each page
(reason code, action, cutoff, volume, precision) is generated here; the guidance below it is hand-written."""
from __future__ import annotations

from pathlib import Path

from scripts import results as R
from scripts.common import ROOT, load_yaml

PLAYBOOKS = ROOT / "docs" / "playbooks"


STATUS = {
    "champion": "running (champion)",
    "challenger": "proposed (challenger)",
    "launch_control": "launch control: a pre-send check on instant payouts (module C)",
    "vendor": "vendor signal, graded in the vendor bake-off (module D)",
}


def facts(rule_id: str, rule: dict, test: dict, cutoffs: dict) -> str:
    m = test[(rule_id, cutoffs[rule_id])]
    action = rule["action"] + (f"; {rule['escalate']['action']} when the score is {rule['comparator']} {rule['escalate']['at']:g}"
                               " and the case is eligible" if rule.get("escalate") else "")
    rows = [
        ("Reason code", f"`{rule['reason_code']}`"),
        ("Status", STATUS[rule["status"]]),
        ("Action", action),
        ("Fires when", f"{rule['score']} {rule['comparator']} {cutoffs[rule_id]:g}"),
        ("Why it exists", rule["rationale"]),
        ("Alerts per business day, rule alone (test months)", f"{m['alerts'] / m['business_days']:.1f}"),
        ("Share that were fraud (test months)", R.pct(m["precision"], 1)),
    ]
    return R.markdown_table(["", ""], rows)


def documents() -> dict[Path, dict[str, str]]:
    rules = load_yaml("rules.yaml")["rules"]
    cutoffs = {r["rule_id"]: r["challenger_cutoff"] for r in R.challenger_thresholds()}
    test = {(m["rule_id"], m["cutoff"]): m for m in R.sweep("test")}
    return {PLAYBOOKS / f"{rid}.md": {"playbook-facts": facts(rid, r, test, cutoffs)} for rid, r in rules.items()}
