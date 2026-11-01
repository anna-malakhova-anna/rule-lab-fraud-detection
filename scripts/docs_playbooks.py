"""Analyst playbooks (module A): one page per rule in docs/playbooks/. The facts block at the top of each page
(reason code, action, cutoff, volume, precision) is generated here; the guidance below it is hand-written."""
from __future__ import annotations

from pathlib import Path

from scripts import results as R
from scripts.common import ROOT, load_yaml

PLAYBOOKS = ROOT / "docs" / "playbooks"


def facts(rule_id: str, rule: dict, volumes: dict, cutoffs: dict, precision: dict) -> str:
    strategy = "champion" if rule["status"] == "champion" else "challenger"
    v = volumes[strategy].get(rule_id, {})
    action = rule["action"] + (f"; {rule['escalate']['action']} when the score is {rule['comparator']} {rule['escalate']['at']:g}"
                               " and the case is eligible" if rule.get("escalate") else "")
    rows = [
        ("Reason code", f"`{rule['reason_code']}`"),
        ("Status", "running (champion)" if strategy == "champion" else "proposed (challenger)"),
        ("Action", action),
        ("Fires when", f"{rule['score']} {rule['comparator']} {cutoffs[rule_id]:g}"),
        ("Why it exists", rule["rationale"]),
        ("Cases per business day (test months)", f"{v.get('cases_per_day', 0):.1f}"),
        ("Share that were fraud (test months)", R.pct(precision.get(rule_id), 1)),
    ]
    return R.markdown_table(["", ""], rows)


def documents() -> dict[Path, dict[str, str]]:
    rules = load_yaml("rules.yaml")["rules"]
    volumes = {s: R.rule_volumes(s) for s in ("champion", "challenger")}
    cutoffs = {r["rule_id"]: r["challenger_cutoff"] for r in R.challenger_thresholds()}
    test = {(m["rule_id"], m["cutoff"]): m for m in R.sweep("test")}
    precision = {rid: test[(rid, cutoffs[rid])]["precision"] for rid in rules}
    return {PLAYBOOKS / f"{rid}.md": {"playbook-facts": facts(rid, r, volumes, cutoffs, precision)}
            for rid, r in rules.items()}
